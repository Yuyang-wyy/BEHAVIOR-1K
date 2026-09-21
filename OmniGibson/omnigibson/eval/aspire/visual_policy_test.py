"""CPU checks: geometry, ASPIRE SAM3 protocol, privilege guard and visual grasp evidence."""

import base64
import ast
import importlib.util
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import torch as th
from scipy.spatial.transform import Rotation

from omnigibson.eval.aspire.public_policy import PublicPolicyExecutor, validate_policy
from omnigibson.eval.aspire.visual_perception import (
    ContactGraspNetClient, Sam3Client, contact_grasps_to_eef, mask_to_world_points, observed_box,
)
from omnigibson.eval.aspire.visual_radio_harness import VisualRadioHarness
from omnigibson.utils.aspire_kinematics import PlanarOdometry


def test_camera_convention_and_invalid_depth():
    depth = np.array([[2.0, np.nan], [0, np.inf]])
    points = mask_to_world_points(np.ones((2, 2), bool), depth, np.eye(3), np.eye(4))
    np.testing.assert_allclose(points, [[0, 0, -2]])
    transform = np.eye(4)
    transform[:3, 3] = [1, 2, 3]
    points = mask_to_world_points([[True]], [[2]], [[2, 0, -1], [0, 2, -1], [0, 0, 1]], transform)
    np.testing.assert_allclose(points, [[2, 1, 1]])


def _legal_observation_harness():
    harness = object.__new__(VisualRadioHarness)
    class ForbiddenPose:
        intrinsic_matrix = np.eye(3)
        def get_position_orientation(self):
            raise AssertionError("policy must not read simulator sensor pose")
    robot = SimpleNamespace(
        name="r1pro", sensors={"head_camera": ForbiddenPose()},
        joints=["base_x", "base_y", "base_z", "left", "right"],
        arm_names=["left", "right"],
        trunk_control_idx=th.tensor([0, 1, 2]),
        arm_control_idx={"left": th.tensor([3]), "right": th.tensor([4])},
        gripper_control_idx={"left": th.tensor([], dtype=th.long), "right": th.tensor([], dtype=th.long)},
    )
    harness.robot = robot
    harness.evaluator = SimpleNamespace(
        robot_camera_names={"head": "r1pro::head_camera"},
        obs={
            "r1pro::head_camera::rgb": th.zeros((2, 2, 3), dtype=th.uint8),
            "r1pro::head_camera::depth_linear": th.ones((2, 2)),
            "r1pro::cam_rel_poses": th.tensor([[.5, -.25, .75, 0., 0., 0., 1.]]),
            "r1pro::proprio": th.tensor([0., 0., 0., .2, .3]),
        },
    )
    harness.odometry = PlanarOdometry()
    harness.odometry._odom_from_base[:3, 3] = [2., 3., .1]
    harness.proprio_slices = {
        "base_qvel": slice(0, 3), "trunk_qpos": slice(0, 3), "arm_left_qpos": slice(3, 4),
        "arm_right_qpos": slice(4, 5), "gripper_left_qpos": slice(0, 0), "gripper_right_qpos": slice(0, 0),
    }
    return harness


def test_observation_forbids_robot_pose_access_and_uses_relative_camera_odom():
    harness = _legal_observation_harness()
    with patch.object(harness, "get_env_observation", return_value=(np.zeros((2, 2, 3), np.uint8), np.ones((2, 2)))):
        observation = harness.get_observation()
    np.testing.assert_allclose(observation["world_from_camera"][:3, 3], [2.5, 2.75, .85])


def test_proprio_joints_keep_virtual_base_zero_and_eef_uses_odom():
    harness = _legal_observation_harness()
    np.testing.assert_allclose(harness.get_current_joint_positions(), [0., 0., 0., .2, .3])
    harness.proprio_slices.update({"eef_left_pos": slice(3, 6), "eef_left_quat": slice(6, 10)})
    harness.evaluator.obs["r1pro::proprio"] = th.tensor([0., 0., 0., .1, .2, .3, 0., 0., 0., 1.])
    position, quat = harness.get_current_eef_pose(arm=0)
    np.testing.assert_allclose(position, [2.1, 3.2, .4])
    np.testing.assert_allclose(quat, [1., 0., 0., 0.])


def _extract_radio_is_held():
    root = Path(__file__).resolve().parents[4]
    tree = ast.parse((root / "scripts/aspire_radio/learned_press_policy.py").read_text())
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "radio_is_held")
    namespace = {"np": np}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<radio_is_held>", "exec"), namespace)
    return namespace["radio_is_held"]


def test_radio_is_held_rejects_stationary_radio_near_empty_hand():
    radio_is_held = _extract_radio_is_held()
    state = {"eef_calls": 0, "saves": 0}
    center = np.array([0., 0., .10])

    def eef(_arm=1, **_kwargs):
        state["eef_calls"] += 1
        return (np.zeros(3), np.array([1., 0., 0., 0.])) if state["eef_calls"] == 1 else (
            np.array([0., 0., .08]), np.array([1., 0., 0., 0.]))
    def observed(_observation, _near=None):
        return (np.ones((1, 1), dtype=bool), np.array([center]))

    namespace = radio_is_held.__globals__
    namespace.update({"get_current_eef_pose": eef, "observed_radio": observed,
                      "get_observation": lambda _camera: object(),
                      "move_hand": lambda *_args, **_kwargs: True,
                      "save_current_observation": lambda *_args, **_kwargs: state.__setitem__("saves", state["saves"] + 1),
                      "grasp_probe_count": 0})
    assert radio_is_held(0.) is False
    assert state["saves"] == 2


def test_radio_is_held_accepts_radio_matching_hand_lift():
    radio_is_held = _extract_radio_is_held()
    state = {"eef_calls": 0}
    centers = [np.array([0., 0., .10]), np.array([0., 0., .18])]

    def eef(_arm=1, **_kwargs):
        state["eef_calls"] += 1
        position = np.zeros(3) if state["eef_calls"] == 1 else np.array([0., 0., .08])
        return position, np.array([1., 0., 0., 0.])
    def observed(_observation, near=None):
        index = 0 if near is None or np.linalg.norm(np.asarray(near) - centers[1]) > .05 else 1
        return (np.ones((1, 1), dtype=bool), np.array([centers[index]]))

    namespace = radio_is_held.__globals__
    namespace.update({"get_current_eef_pose": eef, "observed_radio": observed,
                      "get_observation": lambda _camera: object(),
                      "move_hand": lambda *_args, **_kwargs: True,
                      "save_current_observation": lambda *_args, **_kwargs: None,
                      "grasp_probe_count": 0})
    assert radio_is_held(0.) is True


def test_observed_box_is_fitted_to_points():
    random = np.random.default_rng(3)
    cloud = random.uniform([-0.2, -0.05, 0.7], [0.2, 0.05, 0.9], (5000, 3))
    center, rotation, extent, _ = observed_box(cloud)
    np.testing.assert_allclose(center, [0, 0, 0.8], atol=.01)
    np.testing.assert_allclose(extent, [.4, .1, .2], atol=.03)
    np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-6)


def test_privileged_programs_are_rejected():
    for source in ("execute_reference_skill('press')", "import omnigibson", "import pyarrow",
                   "RESULT = env.task.success", "RESULT = get_object_pose.__self__",
                   "import numpy as np\nnp.load('demo.npz')", "open('scene.json')"):
        try:
            validate_policy(source)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Privileged source passed: {source}")
    executor = PublicPolicyExecutor({"get_object_pose": lambda name: [1, 2, 3]})
    blocks = executor.run_source("import numpy as np\n# Code block 1\nRESULT = np.mean(get_object_pose('radio'))")
    assert blocks[0].ok and blocks[0].result == 2
    root = Path(__file__).resolve().parents[4]
    validate_policy((root / "scripts/aspire_radio/visual_policy.py").read_text())


def test_sam3_protocol_without_model_weights():
    mask = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            assert self.path == "/segment" and payload["text_prompt"] == "red radio"
            assert base64.b64decode(payload["image_base64"]).startswith(b"\x89PNG")
            response = {"results": [{"shape": [2, 2], "mask_base64": base64.b64encode(mask.tobytes()).decode(),
                                     "box": [0, 0, 2, 2], "score": .9}]}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        def log_message(self, *args):
            pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        results = Sam3Client(f"http://127.0.0.1:{server.server_port}").segment(np.zeros((2, 2, 3), np.uint8), "red radio")
        np.testing.assert_array_equal(results[0]["mask"], mask.astype(bool))
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_contact_graspnet_protocol_and_robot_frame_conversion():
    import io
    grasps = np.eye(4)[None]
    def encode(array):
        stream = io.BytesIO()
        np.save(stream, array, allow_pickle=False)
        return base64.b64encode(stream.getvalue()).decode("ascii")
    payload = {key: encode(value) for key, value in zip(
        ("grasps_base64", "scores_base64", "contact_pts_base64"),
        (grasps, np.array([.8]), np.zeros((1, 3))))}
    with patch("omnigibson.eval.aspire.visual_perception.requests.post") as post:
        post.return_value.json.return_value = payload
        poses, scores, _ = ContactGraspNetClient().plan(np.ones((5, 5)), np.eye(3), np.ones((5, 5), bool))
        assert scores[0] == .8 and post.call_args.kwargs["timeout"] == 90
        sent = post.call_args.kwargs["json"]
        mask = np.load(io.BytesIO(base64.b64decode(sent["segmap_base64"])), allow_pickle=False)
        assert np.all(mask == 1) and sent["segmap_id"] == 1
        assert sent["forward_passes"] == 1 and sent["max_retries"] == 7
        assert sent["filter_grasps"] is True
        pre, goal = contact_grasps_to_eef(poses, np.eye(4), .02)
        np.testing.assert_allclose(goal[0, :3, 3], [0, 0, -.0984])
        np.testing.assert_allclose(pre[0, :3, 3], [0, 0, .0216])
        np.testing.assert_allclose(goal[0, :3, 1], [1, 0, 0])
        np.testing.assert_allclose(goal[0, :3, 2], [0, 0, -1])
        payload["grasps_base64"] = encode(np.zeros((1, 4, 4)))
        try:
            ContactGraspNetClient().plan(np.ones((5, 5)), np.eye(3), np.ones((5, 5), bool))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid grasp rotation was accepted")


def test_grasp_check_requires_visual_lift_and_proximity():
    harness = object.__new__(VisualRadioHarness)
    harness.last_grasp = ("red radio", np.array([0, 0, .7]))
    with patch.object(harness, "_trace"), patch.object(harness, "get_object_pose", return_value=(np.array([0, 0, .78]),)), \
         patch.object(harness, "get_current_eef_pose", return_value=(np.array([0, 0, .9]), None)):
        assert harness.check_object_in_hand()
    with patch.object(harness, "_trace"), patch.object(harness, "get_object_pose", return_value=(np.array([0, 0, .7]),)), \
         patch.object(harness, "get_current_eef_pose", return_value=(np.array([0, 0, .9]), None)):
        assert not harness.check_object_in_hand()


def test_refinement_runner_revises_then_executes_and_strips_credentials():
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location("radio_refinement_test", root / "scripts/aspire_radio/refine_visual_policy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only", "HF_TOKEN": "test-only"}):
        env = module.worker_environment(root)
        assert "OPENAI_API_KEY" not in env and "HF_TOKEN" not in env
    calls = []
    revised = "# Code block 1\nRESULT = {'observed': True}\n"
    def fake_worker(command, **kwargs):
        directory = Path(command[command.index("--output-dir") + 1])
        directory.mkdir()
        executed = Path(command[command.index("--policy") + 1]).read_text()
        calls.append(executed)
        passed = len(calls) == 2
        (directory / "result.json").write_text(json.dumps({"task_success": passed, "status": "success" if passed else "policy_failed"}))
        return 0
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "campaign"
        arguments = ["refine", "--output-dir", str(output), "--max-attempts", "2"]
        with patch.object(sys, "argv", arguments), patch.object(module, "run_process", side_effect=fake_worker), \
             patch.object(module.requests, "get") as get, patch.object(module, "propose_policy") as propose:
            get.return_value.json.return_value = {"paths": {"/segment": {}}}
            propose.return_value = {"policy": revised, "diagnosis": "mocked failure", "lesson": "test-only"}
            module.main()
        state = json.loads((output / "state.json").read_text())
        assert state["task_success"] and len(state["attempts"]) == 2
        assert calls[0] != revised and calls[1] == revised
        assert propose.call_count == 1


def test_both_gripper_commands_preserve_holding_hand():
    harness = object.__new__(VisualRadioHarness)
    harness.gripper_closed = {"left": False, "right": True}
    harness.joint_targets = np.array([.5, .1, .2, .05, .05])
    harness.robot = SimpleNamespace(
        action_dim=8, arm_names=["left", "right"],
        trunk_action_idx=th.tensor([3]), trunk_control_idx=th.tensor([0]),
        arm_action_idx={"left": th.tensor([4]), "right": th.tensor([5])},
        arm_control_idx={"left": th.tensor([1]), "right": th.tensor([2])},
        gripper_action_idx={"left": th.tensor([6]), "right": th.tensor([7])},
        get_joint_positions=lambda: th.tensor([.5, .1, .2, .05, .05]),
    )
    action = harness._action()
    np.testing.assert_allclose(action.numpy(), [0, 0, 0, .5, .1, .2, 1, -1])
    harness.robot.get_joint_positions = lambda: th.zeros(5)
    np.testing.assert_array_equal(harness._action(), action)


def test_navigation_final_rotation_survives_small_base_drift():
    harness = object.__new__(VisualRadioHarness)
    harness.robot = SimpleNamespace(base_action_idx=th.tensor([0, 1, 2]))
    poses = [(np.array([-distance, 0, 0]), None, yaw)
             for distance, yaw in ((.09, 0), (.09, 0), (.079, 0), (.081, .5), (.081, 1))]
    actions = []
    with patch.object(harness, "get_robot_position", side_effect=poses), patch.object(harness, "_trace"), \
         patch.object(harness, "_action", side_effect=lambda: th.zeros(3)), \
         patch.object(harness, "_step", side_effect=actions.append):
        assert harness.navigate_to_pose([0, 0, 1])
    # The final-dock hysteresis accepts the 9 cm visual residual before
    # issuing a translational command, then handles heading correction.
    assert actions[0][0] == 0
    assert actions[1][0] == actions[2][0] == 0
    assert actions[1][2] > 0 and actions[2][2] > 0


def test_navigation_pose_approaches_nearest_table_edge():
    harness = object.__new__(VisualRadioHarness)
    harness.output_dir = Path(tempfile.mkdtemp())
    harness.steps = 0
    harness.get_robot_position = lambda: (np.array([3., .5, 0]), None, 0)
    table = np.array([[0, 0, .4], [2, 0, .4], [2, 1, .4], [0, 1, .4]])
    goal = harness.get_navigation_pose(table, [[1.8, .5, .6]])
    np.testing.assert_allclose(goal[:2], [2.4, .5], atol=1e-6)
    assert abs(abs(goal[2]) - np.pi) < 1e-6


def test_navigation_long_table_rejects_unreachable_near_base_edge():
    harness = object.__new__(VisualRadioHarness)
    harness.output_dir = Path(tempfile.mkdtemp())
    harness.steps = 0
    harness.get_robot_position = lambda: (np.array([0., .5, 0]), None, 0)
    table = np.array([[0, 0, .4], [10, 0, .4], [10, 1, .4], [0, 1, .4]])
    goal = harness.get_navigation_pose(table, [[9.5, .5, .6]])
    assert goal[0] > 9.0
    assert np.linalg.norm(goal[:2] - np.array([9.5, .5])) <= .93 + 1e-6


def test_motor_settling_is_bounded_and_reports_obstruction():
    harness = object.__new__(VisualRadioHarness)
    harness.robot = SimpleNamespace(trunk_control_idx=th.tensor([0]), arm_names=["right"],
                                    arm_control_idx={"right": th.tensor([1])},
                                    joint_lower_limits=th.tensor([-2., -2.]),
                                    joint_upper_limits=th.tensor([2., 2.]), joints={"trunk": None, "arm": None})
    with patch.object(harness, "get_current_joint_positions", return_value=np.zeros(2)), \
         patch.object(harness, "_action", side_effect=lambda joints: joints), \
         patch.object(harness, "_step") as step, patch.object(harness, "_trace") as trace:
        assert not harness.move_to_joints([.015, .015])
        assert step.call_count == 121
        assert trace.call_args.kwargs["settled"] is False


def test_free_hand_press_uses_mobile_approach_then_fixed_contact():
    harness = object.__new__(VisualRadioHarness)
    harness.last_grasp = ("radio", np.zeros(3))
    harness.grasp_arm = 1
    harness.gripper_closed = {"left": False, "right": True}
    harness.robot = SimpleNamespace(eef_to_fingertip_lengths={"left": {"finger": .02}})
    observation = {"depth": np.ones((5, 5)), "intrinsics": np.eye(3), "world_from_camera": np.eye(4)}
    with patch.object(harness, "get_observation", return_value=observation), \
         patch.object(harness, "_trace"), patch.object(harness, "close_gripper"), \
         patch.object(harness, "save_current_observation"), \
         patch.object(harness, "_action", return_value=np.zeros(1)), \
         patch.object(harness, "_step"), \
         patch.object(harness, "get_current_joint_positions", return_value=np.zeros(1)), \
         patch.object(harness, "get_current_eef_pose",
                      return_value=(np.zeros(3), np.array([1., 0., 0., 0.]))), \
         patch.object(harness, "solve_ik", side_effect=[None, None, *[np.array([.1 + index / 10]) for index in range(6)]]) as solve, \
         patch.object(harness, "move_to_joints") as move_joints, \
         patch.object(harness, "move_hand", return_value=True) as move:
        assert harness.press_at_pixel(2, 2, arm=0)
        assert solve.call_count == 7
        assert all(call.kwargs["lock_last_trunk"] is True for call in solve.call_args_list[:6])
        assert solve.call_args_list[-1].kwargs["lock_trunk"] is True
        assert move_joints.call_count == 2
        np.testing.assert_allclose(move_joints.call_args_list[0].args[0], [.1])
        np.testing.assert_allclose(move_joints.call_args_list[1].args[0], [.5])
        assert move.call_count == 4
        assert all(call.kwargs["lock_trunk"] is True for call in move.call_args_list)


def test_holder_contact_orientation_transport_preserves_current_approach_axis():
    initial_holder = Rotation.from_euler("zyx", [20, -10, 15], degrees=True)
    current_holder = Rotation.from_euler("zyx", [75, 25, -20], degrees=True)
    base_rotation = Rotation.from_euler("zyx", [35, 10, 5], degrees=True)
    holder_delta = current_holder * initial_holder.inv()
    contact = holder_delta * base_rotation * Rotation.from_euler("z", 0.7)
    expected_axis = holder_delta.apply(base_rotation.apply(np.array([0., 0., 1.])))
    np.testing.assert_allclose(contact.apply(np.array([0., 0., 1.])), expected_axis, atol=1e-7)


def test_press_terminal_guard_reports_motion_incomplete():
    harness = object.__new__(VisualRadioHarness)
    harness.terminated = False
    harness.truncated = True
    assert harness.press_at_pixel(0, 0) is False


def test_failed_press_fallback_reacquires_button_before_bimanual_geometry():
    root = Path(__file__).resolve().parents[4]
    tree = ast.parse((root / "scripts/aspire_radio/learned_press_policy.py").read_text())
    fallback = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.If) and isinstance(node.test, ast.UnaryOp)
                    and isinstance(node.test.op, ast.Not)
                    and isinstance(node.test.operand, ast.Name)
                    and node.test.operand.id == "pressed"
                    and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                            and child.func.id == "get_current_eef_pose" for child in ast.walk(node)))
    reacquire = next(child for child in ast.walk(fallback)
                     if isinstance(child, ast.For)
                     and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                             and call.func.id == "held_radio_pixels" for call in ast.walk(child)))
    geometry = next(child for child in ast.walk(fallback)
                    if isinstance(child, ast.Assign)
                    and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                            and call.func.id == "get_current_eef_pose" for call in ast.walk(child)))
    assert reacquire.lineno < geometry.lineno
    source = (root / "scripts/aspire_radio/learned_press_policy.py").read_text()
    assert "assert reacquired, \"Cannot safely fallback without a fresh button observation\"" in source
    assert "lock_last_trunk=True" not in ast.get_source_segment(source, fallback)
    assert "holder_joints[6:10]" in ast.get_source_segment(source, fallback)


def test_contact_candidates_keep_measured_current_orientation():
    source = (Path(__file__).resolve().parents[4]
              / "OmniGibson/omnigibson/eval/aspire/visual_radio_harness.py").read_text()
    assert "if contact_roll is None and current_rotation is None" in source
    assert "Rotation.from_matrix(current_rotation)" in source
    assert "contact_rolls = (wrist_roll, math.pi / 2" in source


def test_free_hand_press_can_lock_torso_during_approach():
    harness = object.__new__(VisualRadioHarness)
    harness.last_grasp = ("radio", np.zeros(3))
    harness.grasp_arm = 1
    harness.gripper_closed = {"left": False, "right": True}
    harness.robot = SimpleNamespace(eef_to_fingertip_lengths={"left": {"finger": .02}})
    observation = {"depth": np.ones((5, 5)), "intrinsics": np.eye(3),
                   "world_from_camera": np.eye(4)}
    with patch.object(harness, "get_observation", return_value=observation), \
         patch.object(harness, "_trace"), patch.object(harness, "close_gripper"), \
         patch.object(harness, "save_current_observation"), \
         patch.object(harness, "_action", return_value=np.zeros(1)), \
         patch.object(harness, "_step"), \
         patch.object(harness, "get_current_joint_positions", return_value=np.zeros(1)), \
         patch.object(harness, "get_current_eef_pose",
                      return_value=(np.zeros(3), np.array([1., 0., 0., 0.]))), \
         patch.object(harness, "solve_ik", return_value=np.array([.1])) as solve, \
         patch.object(harness, "move_to_joints"), \
         patch.object(harness, "move_hand", return_value=True):
        assert harness.press_at_pixel(2, 2, arm=0, fixed_torso=True)
        assert all(call.kwargs["lock_trunk"] is True for call in solve.call_args_list)


def test_left_ik_config_targets_left_eef_and_locks_right_arm():
    import yaml
    from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection

    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "source.yaml"
        source.write_text(yaml.safe_dump({"robot_cfg": {"kinematics": {"ee_link": "left_eef_link", "link_names": []}}}))
        harness = object.__new__(VisualRadioHarness)
        harness.output_dir = Path(temp)
        harness.motion_generators = {}
        joint_state = np.zeros(3)
        harness.robot = SimpleNamespace(curobo_path={CuRoboEmbodimentSelection.ARM: str(source)},
                                        trunk_joint_names=["torso_j", "torso_lift"],
                                        arm_joint_names={"right": ["right_j"], "left": ["left_j"]},
                                        joints={"right_j": None, "torso_j": None, "torso_lift": None},
                                        get_joint_positions=lambda: joint_state)
        with patch("omnigibson.action_primitives.curobo.CuRoboMotionGenerator") as constructor:
            with patch.object(harness, "get_current_joint_positions", return_value=joint_state):
                generator = harness._init_ik(arm=0)
            assert generator is constructor.return_value
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            config = yaml.safe_load((Path(temp) / "robot_left_ik.yaml").read_text())
            assert config["robot_cfg"]["kinematics"]["ee_link"] == "left_eef_link"
            with patch.object(harness, "get_current_joint_positions", return_value=joint_state):
                assert harness._init_ik(arm=0) is generator
            assert constructor.call_count == 1
            with patch.object(harness, "get_current_joint_positions", return_value=joint_state):
                fixed_generator = harness._init_ik(arm=0, lock_trunk=True)
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            assert constructor.call_count == 2
            with patch.object(harness, "get_current_joint_positions", return_value=joint_state):
                harness._init_ik(arm=0, lock_last_trunk=True)
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            assert constructor.call_count == 3
            joint_state[1] = .2
            with patch.object(harness, "get_current_joint_positions", return_value=joint_state):
                assert harness._init_ik(arm=0, lock_trunk=True) is fixed_generator
            assert constructor.call_count == 3


def test_solve_ik_preserves_current_solver_omitted_locked_joints():
    path = SimpleNamespace(position=th.tensor([[.5]]), joint_names=["right_arm"])
    generator = SimpleNamespace(compute_trajectories=lambda *args, **kwargs: (th.tensor([True]), [path]))
    harness = object.__new__(VisualRadioHarness)
    harness.motion_generators = {"right_fixed_trunk": generator}
    harness.motion_generator_locks = {"right_fixed_trunk": {"torso": .9}}
    harness.odometry = PlanarOdometry()
    harness.robot = SimpleNamespace(
        get_joint_positions=lambda: th.tensor([.9, .1]),
        joints={"torso": None, "right_arm": None},
        trunk_joint_names=["torso"],
        trunk_control_idx=th.tensor([0]), arm_names=["right"],
        arm_control_idx={"right": th.tensor([1])},
        joint_lower_limits=th.tensor([-2., -2.]), joint_upper_limits=th.tensor([2., 2.]),
    )
    with patch.object(harness, "get_current_joint_positions", return_value=np.array([.9, .1])):
        np.testing.assert_allclose(
            harness.solve_ik(np.zeros(3), np.array([1., 0., 0., 0.]), arm=1, lock_trunk=True),
            [.9, .5],
        )


def test_move_to_posture_preserves_other_arm():
    harness = object.__new__(VisualRadioHarness)
    harness.robot = SimpleNamespace(
        arm_control_idx={"left": th.tensor([2, 3]), "right": th.tensor([4, 5])},
        trunk_control_idx=th.tensor([0, 1]),
    )
    actual = np.arange(6, dtype=float)
    harness.get_current_joint_positions = lambda: actual.copy()
    def loaded_move(target, **kwargs):
        actual[:] = target
        actual[4] += .03
        return False
    harness.move_to_joints = MagicMock(side_effect=loaded_move)
    assert harness.move_to_posture(0, [-2, -3], [.5, .6], max_joint_step=.01)
    np.testing.assert_allclose(harness.move_to_joints.call_args.args[0], [.5, .6, -2, -3, 4, 5])
    assert harness.move_to_joints.call_args.kwargs["max_joint_step"] == .01
    harness.move_to_joints.side_effect = lambda *args, **kwargs: False
    assert not harness.move_to_posture(0, [-1, -3])


def test_pixel_mode_captures_before_fresh_policy_construction():
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location("radio_pixel_refinement_test", root / "scripts/aspire_radio/refine_visual_policy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    candidate = "# Code block 1\nRESULT = {'motion': True}\n"
    def fake_worker(command, **kwargs):
        directory = Path(command[command.index("--output-dir") + 1])
        directory.mkdir()
        captured = "--capture-only" in command
        calls.append((captured, Path(command[command.index("--policy") + 1]).read_text()))
        (directory / "result.json").write_text(json.dumps({"task_success": not captured,
            "status": "capture_only" if captured else "success"}))
        return 0
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "campaign"
        reference = Path(temp) / "reference"
        reference.mkdir()
        (reference / "provenance.json").write_text(json.dumps({"action_columns_read": False,
            "training_reference_only": True, "skills": [{"description": ["press"], "frames": [10, 30]}]}))
        for frame in (10, 20, 29):
            (reference / f"zed_link_camera_0_frame_{frame:05d}.png").touch()
        with patch.object(sys, "argv", ["refine", "--output-dir", str(output), "--grounding", "codex-pixels",
                                       "--reference-dir", str(reference)]), \
             patch.object(module, "run_process", side_effect=fake_worker), patch.object(module, "propose_policy") as propose, \
             patch.object(module.requests, "get") as get:
            propose.return_value = {"policy": candidate, "diagnosis": "mocked", "lesson": "test-only"}
            module.main()
        assert calls[0][0] and not calls[1][0] and calls[1][1] == candidate
        assert propose.call_args.kwargs["grounding"] == "codex-pixels"
        assert [path.stem[-5:] for path in propose.call_args.kwargs["reference_images"]] == ["00020", "00029"]
        assert get.call_count == 0
        assert json.loads((output / "state.json").read_text())["grounding_backend"] == "codex-pixels"


def test_refinement_keeps_full_resolution_grasp_evidence():
    root = Path(__file__).resolve().parents[4]
    spec = importlib.util.spec_from_file_location("radio_evidence_test", root / "scripts/aspire_radio/refine_visual_policy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        for name in ("initial_head", "initial_left_wrist", "initial_right_wrist", "before_grasp",
                     "after_grasp", "after_grasp_right", "after_left_motion"):
            (directory / f"{name}.png").touch()
        _, images = module.evidence_for_codex(directory, directory)
        names = {path.stem for path in images}
        assert {"initial_head", "before_grasp", "after_grasp", "after_grasp_right", "after_left_motion"} <= names
        assert "initial_left_wrist" not in names and "initial_right_wrist" not in names


def test_finger_positions_strip_the_scene_prefix_from_link_names():
    """Robot link names are scene-prefixed; URDF finger offsets are not.

    Indexing the offsets with the raw link name raised ``KeyError`` on every
    call, which ``press_at_pixel`` swallowed and then aimed as if the fingertip
    sat on the EEF +Z axis - a systematic 13.5 mm lateral error on a control
    whose overlap volume is about a centimetre across.
    """
    harness = object.__new__(VisualRadioHarness)
    offset = np.eye(4)
    offset[:3, 3] = [0.0, .0135, .1]
    harness.finger_geometry = SimpleNamespace(update=lambda joints: {
        "right_gripper_finger_link1": offset, "right_gripper_finger_link2": offset})
    harness.robot = SimpleNamespace(
        joints={"a": None},
        finger_links={"right": [SimpleNamespace(name="robot_r1:right_gripper_finger_link1"),
                                SimpleNamespace(name="robot_r1:right_gripper_finger_link2")]})
    with patch.object(harness, "get_current_joint_positions", return_value=np.zeros(1)), \
         patch.object(harness, "get_current_eef_pose",
                      return_value=(np.array([1., 2., 3.]), np.array([1., 0., 0., 0.]))):
        positions = harness._finger_positions(1)
        center = harness.get_current_finger_center(1)
    np.testing.assert_allclose(positions, [[1., 2.0135, 3.1]] * 2)
    np.testing.assert_allclose(center, [1., 2.0135, 3.1])


def test_navigate_to_pose_gives_up_on_a_blocked_approach():
    """A straight-line dock with no obstacle model must not burn 800 steps."""
    harness = object.__new__(VisualRadioHarness)
    harness.robot = SimpleNamespace(base_action_idx=th.tensor([0, 1, 2]))
    with patch.object(harness, "get_robot_position",
                      return_value=(np.array([0., 0., 0.]), None, 0.0)), \
         patch.object(harness, "_action", side_effect=lambda *a, **k: th.zeros(3)), \
         patch.object(harness, "_step") as step, patch.object(harness, "_trace") as trace:
        assert harness.navigate_to_pose(np.array([1.0, 0.0, 0.0])) is False
    assert step.call_count < 300
    assert any(call.args[0] == "navigation_stalled" for call in trace.call_args_list)


def test_press_advances_in_a_straight_line_from_the_standoff():
    """The approach arc is unplanned, so it must end clear of the object.

    ``move_to_joints`` interpolates in joint space and ``solve_ik`` runs with
    ``ik_world_collision_check=False``, so the sweep that reaches the stand-off
    can pass through whatever it is pressing. Parking 13 cm out and covering
    the rest with collinear Cartesian steps is what keeps it from toppling a
    free-standing object.
    """
    harness = object.__new__(VisualRadioHarness)
    harness.last_grasp = None
    harness.grasp_arm = 1
    harness.gripper_closed = {"left": False, "right": False}
    harness.robot = SimpleNamespace(eef_to_fingertip_lengths={"left": {"finger": .02}})
    observation = {"depth": np.ones((5, 5)), "intrinsics": np.eye(3), "world_from_camera": np.eye(4)}
    with patch.object(harness, "get_observation", return_value=observation), \
         patch.object(harness, "_trace"), patch.object(harness, "close_gripper"), \
         patch.object(harness, "save_current_observation"), \
         patch.object(harness, "_action", return_value=np.zeros(1)), \
         patch.object(harness, "_step"), \
         patch.object(harness, "get_current_joint_positions", return_value=np.zeros(1)), \
         patch.object(harness, "get_current_eef_pose",
                      return_value=(np.zeros(3), np.array([1., 0., 0., 0.]))), \
         patch.object(harness, "solve_ik", return_value=np.zeros(1)), \
         patch.object(harness, "move_to_joints"), \
         patch.object(harness, "move_hand", return_value=True) as move:
        assert harness.press_at_pixel(2, 2, arm=0, travel=.008, surface_offset=.004)
    # With K = I and unit depth, pixel (2, 2) backprojects to [2, -2, -1], so
    # the press normal is that direction normalised.
    direction = np.array([2., -2., -1.]) / 3.0
    poses = [call.args[0][0] for call in move.call_args_list]
    assert len(poses) == 4, poses
    # every commanded pose lies on one line along the press normal
    for pose in poses[1:]:
        offset = pose - poses[0]
        assert np.allclose(offset, direction * float(np.dot(offset, direction)), atol=1e-9)
    # and the advance spans the full stand-off (0.13) plus the travel (0.008)
    span = float(np.dot(poses[-1] - poses[0], direction))
    assert abs(span - 0.138) < 1e-6, span


def test_connected_component_pass_is_bounded():
    """A rollout once stalled with its trace frozen; the red pass is capped."""
    import importlib.util
    path = Path(__file__).resolve().parents[4] / "scripts/aspire_radio/press_marker_policy.py"
    source = path.read_text()
    namespace = {"np": np}
    helpers = source[source.index("COMPONENT_PIXEL_BUDGET"):source.index("def observed_radio")]
    exec(compile(helpers, "helpers", "exec"), namespace, namespace)  # noqa: S102
    mask = np.ones((400, 400), dtype=bool)          # 160k pixels, over the budget
    found = namespace["connected_components"](mask, 1)
    assert len(found) == 1                          # one giant blob, then stop
    checkerboard = np.zeros((200, 200), dtype=bool)
    checkerboard[::2, ::2] = True                   # 10k separate components
    assert len(namespace["connected_components"](checkerboard, 1)) <= namespace["COMPONENT_COUNT_BUDGET"]
