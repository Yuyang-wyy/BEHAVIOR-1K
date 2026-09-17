"""CPU checks: geometry, ASPIRE SAM3 protocol, privilege guard and visual grasp evidence."""

import base64
import importlib.util
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch as th

from omnigibson.eval.aspire.public_policy import PublicPolicyExecutor, validate_policy
from omnigibson.eval.aspire.visual_perception import (
    ContactGraspNetClient, Sam3Client, contact_grasps_to_eef, mask_to_world_points, observed_box,
)
from omnigibson.eval.aspire.visual_radio_harness import VisualRadioHarness


def test_camera_convention_and_invalid_depth():
    depth = np.array([[2.0, np.nan], [0, np.inf]])
    points = mask_to_world_points(np.ones((2, 2), bool), depth, np.eye(3), np.eye(4))
    np.testing.assert_allclose(points, [[0, 0, -2]])
    transform = np.eye(4)
    transform[:3, 3] = [1, 2, 3]
    points = mask_to_world_points([[True]], [[2]], [[2, 0, -1], [0, 2, -1], [0, 0, 1]], transform)
    np.testing.assert_allclose(points, [[2, 1, 1]])


def test_observation_uses_live_sensor_world_pose():
    harness = object.__new__(VisualRadioHarness)
    sensor = SimpleNamespace(
        intrinsic_matrix=np.eye(3),
        get_position_orientation=lambda: (th.tensor([1., 2., 3.]), th.tensor([0., 0., 0., 1.])),
    )
    harness.evaluator = SimpleNamespace(robot_camera_names={"head": "r1pro::head_camera"})
    harness.robot = SimpleNamespace(sensors={"head_camera": sensor}, get_joint_positions=lambda: th.zeros(2))
    with patch.object(harness, "get_env_observation", return_value=(np.zeros((2, 2, 3)), np.ones((2, 2)))):
        observation = harness.get_observation()
    np.testing.assert_allclose(observation["world_from_camera"][:3, 3], [1, 2, 3])


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
    assert actions[0][0] > 0
    assert actions[1][0] == actions[2][0] == 0
    assert actions[1][2] > 0 and actions[2][2] > 0


def test_navigation_pose_approaches_nearest_table_edge():
    harness = object.__new__(VisualRadioHarness)
    harness.get_robot_position = lambda: (np.array([3., .5, 0]), None, 0)
    table = np.array([[0, 0, .4], [2, 0, .4], [2, 1, .4], [0, 1, .4]])
    goal = harness.get_navigation_pose(table, [[1.8, .5, .6]])
    np.testing.assert_allclose(goal[:2], [2.4, .5], atol=1e-6)
    assert abs(abs(goal[2]) - np.pi) < 1e-6


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
        move_joints.assert_called_once()
        np.testing.assert_allclose(move_joints.call_args.args[0], [.1])
        assert move.call_count == 5
        assert all(call.kwargs["lock_trunk"] is True for call in move.call_args_list)


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
        harness.robot = SimpleNamespace(curobo_path={CuRoboEmbodimentSelection.ARM: str(source)},
                                        trunk_joint_names=["torso_j", "torso_lift"],
                                        arm_joint_names={"right": ["right_j"], "left": ["left_j"]},
                                        joints={"right_j": None, "torso_j": None, "torso_lift": None},
                                        get_joint_positions=lambda: np.zeros(3))
        with patch("omnigibson.action_primitives.curobo.CuRoboMotionGenerator") as constructor:
            generator = harness._init_ik(arm=0)
            assert generator is constructor.return_value
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            config = yaml.safe_load((Path(temp) / "robot_left_ik.yaml").read_text())
            assert config["robot_cfg"]["kinematics"]["ee_link"] == "left_eef_link"
            assert harness._init_ik(arm=0) is generator
            assert constructor.call_count == 1
            harness._init_ik(arm=0, lock_trunk=True)
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            assert constructor.call_count == 2
            harness._init_ik(arm=0, lock_last_trunk=True)
            assert constructor.call_args.kwargs["lock_joint_names"] == []
            assert constructor.call_count == 3


def test_solve_ik_restores_solver_omitted_locked_joints():
    path = SimpleNamespace(position=th.tensor([[.5]]), joint_names=["right_arm"])
    generator = SimpleNamespace(compute_trajectories=lambda *args, **kwargs: (th.tensor([True]), [path]))
    harness = object.__new__(VisualRadioHarness)
    harness.motion_generators = {"right_fixed_trunk": generator}
    harness.motion_generator_locks = {"right_fixed_trunk": {"torso": .25}}
    harness.robot = SimpleNamespace(
        get_joint_positions=lambda: th.tensor([.9, .1]),
        joints={"torso": None, "right_arm": None},
        trunk_control_idx=th.tensor([0]), arm_names=["right"],
        arm_control_idx={"right": th.tensor([1])},
        joint_lower_limits=th.tensor([-2., -2.]), joint_upper_limits=th.tensor([2., 2.]),
    )
    np.testing.assert_allclose(
        harness.solve_ik(np.zeros(3), np.array([1., 0., 0., 0.]), arm=1, lock_trunk=True),
        [.25, .5],
    )


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
