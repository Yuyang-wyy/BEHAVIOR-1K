"""Collect verified train-only radio press recoveries from serialized simulator snapshots.

This is deliberately not an evaluation policy. It consumes privileged toggle-marker
poses only after validating a ``mode=train`` recovery snapshot, resets the exact
simulator state between candidates, and writes supervision only for attempts that
physically toggle the radio.
"""

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np


RADIO_RGB_KEYS = (
    "robot_r1::robot_r1:zed_link:Camera:0::rgb",
    "robot_r1::robot_r1:left_realsense_link:Camera:0::rgb",
    "robot_r1::robot_r1:right_realsense_link:Camera:0::rgb",
)
RADIO_PROPRIO_KEY = "robot_r1::proprio"


def _require_physical_grasp_config(robot_config) -> None:
    if robot_config.grasping_mode != "physical":
        raise ValueError(
            "Radio data collection requires grasping_mode='physical'; assisted and sticky grasping are disabled."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--robot-config", type=Path, default=Path(__file__).with_name("r1pro.yaml"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument(
        "--candidate-start-index",
        type=int,
        default=0,
        help="Skip earlier deterministic approach candidates when sharding an oracle search.",
    )
    # Batch eight exhausts a 24 GB RTX 4090 during CuRobo warmup for R1Pro.
    # A single planning seed is slower but leaves enough memory for Isaac Sim.
    parser.add_argument("--planner-batch-size", type=int, default=1)
    parser.add_argument("--planner-timeout", type=float, default=4.0)
    parser.add_argument("--planner-max-attempts", type=int, default=8)
    parser.add_argument("--standoff-distances", type=float, nargs="+", default=(0.08, 0.12))
    parser.add_argument("--orientation-yaw-degrees", type=float, nargs="+", default=(0.0, -25.0, 25.0))
    parser.add_argument(
        "--orientation-mode",
        choices=("current", "approach_aligned"),
        default="current",
        help="Keep the snapshot wrist orientation or align the EEF fingertip axis with the press direction.",
    )
    parser.add_argument("--contact-offsets", type=float, nargs="+", default=(0.035, 0.02, 0.005, -0.01))
    parser.add_argument("--contact-dwell-steps", type=int, default=8)
    parser.add_argument("--max-joint-step", type=float, default=0.015)
    parser.add_argument("--contact-servo-max-steps", type=int, default=512)
    parser.add_argument("--contact-servo-tolerance", type=float, default=0.005)
    parser.add_argument("--record-stride", type=int, default=8)
    parser.add_argument("--action-horizon", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--video-path", type=Path, default=None)
    parser.add_argument("--side-video-path", type=Path, default=None)
    parser.add_argument("--allow-non-press-snapshot", action="store_true")
    parser.add_argument("--reset-radio-to-table", action="store_true")
    parser.add_argument("--assisted-after-contact", action="store_true")
    parser.add_argument(
        "--allow-direct-contact-fallback",
        action="store_true",
        help="Try a short left-arm-only IK press when collision-aware standoff planning rejects the contact snapshot.",
    )
    parser.add_argument(
        "--mobility",
        choices=("left_only", "left_torso", "bimanual"),
        default="left_only",
        help="Privileged planning DOFs, ordered from most conservative to most expressive.",
    )
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def load_snapshot_metadata(path: Path, *, allow_non_press: bool = False) -> dict:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    with np.load(path, allow_pickle=False) as snapshot:
        required = {"format_version", "simulator_state", "state_size", "metadata_json"}
        missing = sorted(required - set(snapshot.files))
        if missing:
            raise ValueError(f"Recovery snapshot is missing fields: {missing}")
        if int(snapshot["format_version"].item()) != 1:
            raise ValueError(f"Unsupported recovery snapshot format: {path}")
        metadata = json.loads(str(snapshot["metadata_json"].item()))
    if metadata.get("mode") != "train" or metadata.get("task") != "turning_on_radio":
        raise ValueError("The recovery oracle accepts only mode=train turning_on_radio snapshots.")
    triggers = [str(trigger) for trigger in metadata.get("triggers", ())]
    if not allow_non_press and not any(trigger.startswith("press_retry") for trigger in triggers):
        raise ValueError(
            f"Snapshot triggers {triggers} are not a press retry; pass --allow-non-press-snapshot to override."
        )
    return metadata


def build_action_chunks(actions: np.ndarray, start_indices: np.ndarray, horizon: int) -> np.ndarray:
    """Build fixed-length future action chunks, padding terminal targets."""
    actions = np.asarray(actions, dtype=np.float32)
    start_indices = np.asarray(start_indices, dtype=np.int64)
    if actions.ndim != 2 or actions.shape[0] < 1:
        raise ValueError(f"Expected at least one [time, action_dim] action, got {actions.shape}.")
    if horizon < 1:
        raise ValueError("horizon must be positive")
    if np.any(start_indices < 0) or np.any(start_indices >= len(actions)):
        raise ValueError("start_indices must reference executed actions")
    indices = start_indices[:, None] + np.arange(horizon, dtype=np.int64)[None, :]
    indices = np.minimum(indices, len(actions) - 1)
    return actions[indices]


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as file:
        json.dump(payload, file, indent=2, sort_keys=True)
    os.replace(temporary, path)


def _snapshot_identity(metadata: dict) -> dict:
    return {
        key: metadata[key]
        for key in ("task", "instance_id", "rollout_id", "seed", "mode")
    }


def _normalized(vector):
    import torch as th

    vector = th.as_tensor(vector, dtype=th.float32)
    norm = th.linalg.vector_norm(vector)
    return vector / th.clamp(norm, min=1e-8)


def _deduplicate_directions(directions, cosine_threshold: float = 0.985):
    unique = []
    for direction in directions:
        direction = _normalized(direction)
        if all(float(direction @ other) < cosine_threshold for other in unique):
            unique.append(direction)
    return unique


def _approach_aligned_orientation(direction, current_orientation, roll_degrees):
    import torch as th
    from omnigibson.utils import transform_utils as transform_utils

    # R1Pro's canonical EEF +z points out through the fingertips. A standoff
    # direction points from the button toward free space, so the fingertip axis
    # must point in the opposite direction during the press.
    tip_axis = _normalized(-direction)
    current_x = transform_utils.quat2mat(current_orientation)[:, 0]
    x_axis = current_x - th.dot(current_x, tip_axis) * tip_axis
    if float(th.linalg.vector_norm(x_axis).item()) < 1e-4:
        fallback = th.tensor([1.0, 0.0, 0.0], dtype=th.float32)
        if abs(float(th.dot(fallback, tip_axis).item())) > 0.9:
            fallback = th.tensor([0.0, 1.0, 0.0], dtype=th.float32)
        x_axis = fallback - th.dot(fallback, tip_axis) * tip_axis
    x_axis = _normalized(x_axis)
    y_axis = _normalized(th.linalg.cross(tip_axis, x_axis))
    base_rotation = th.stack([x_axis, y_axis, tip_axis], dim=1)
    roll = math.radians(float(roll_degrees))
    roll_rotation = th.tensor(
        [[math.cos(roll), -math.sin(roll), 0.0], [math.sin(roll), math.cos(roll), 0.0], [0.0, 0.0, 1.0]],
        dtype=th.float32,
    )
    return transform_utils.mat2quat(base_rotation @ roll_rotation)


def _candidate_standoffs(
    robot,
    marker_position,
    marker_orientation,
    distances,
    orientation_yaw_degrees,
    orientation_mode,
):
    import torch as th
    from omnigibson.utils import transform_utils as transform_utils

    rotation = transform_utils.quat2mat(marker_orientation)
    local_axes = [rotation[:, axis] * sign for axis in range(3) for sign in (-1.0, 1.0)]
    left_position = robot.get_eef_position("left")
    base_position = robot.get_position_orientation()[0]
    preferred = [left_position - marker_position, base_position - marker_position, *local_axes]
    directions = _deduplicate_directions(preferred)
    current_orientation = robot.eef_links["left"].get_position_orientation()[1]
    finger_centroid = th.stack(
        [link.get_position_orientation()[0] for link in robot.finger_links["left"]]
    ).mean(dim=0)
    finger_local_offset = transform_utils.quat_apply(
        transform_utils.quat_inverse(current_orientation),
        finger_centroid - left_position,
    )
    candidates = []
    # Interleave directions so a bounded max-candidates budget explores the
    # marker's distinct approach axes instead of spending every trial on
    # orientation variants of the first (often occluded) approach.
    for distance in distances:
        for orientation_index, yaw_degrees in enumerate(orientation_yaw_degrees):
            for direction_index, direction in enumerate(directions):
                if orientation_mode == "approach_aligned":
                    orientation = _approach_aligned_orientation(direction, current_orientation, yaw_degrees)
                else:
                    yaw = math.radians(float(yaw_degrees))
                    orientation = transform_utils.quat_multiply(
                        transform_utils.axisangle2quat(th.tensor([0.0, 0.0, yaw], dtype=th.float32)),
                        current_orientation,
                    )
                finger_world_offset = transform_utils.quat_apply(orientation, finger_local_offset)
                candidates.append(
                    {
                        "direction_index": direction_index,
                        "orientation_index": orientation_index,
                        "direction": direction,
                        "distance": float(distance),
                        # CuRobo targets the EEF frame, while ToggledOn checks a
                        # finger-link overlap. Place the closed-finger centroid,
                        # not the EEF origin, at the requested standoff/contact.
                        "position": marker_position + direction * float(distance) - finger_world_offset,
                        "finger_target_position": marker_position + direction * float(distance),
                        "finger_local_offset": finger_local_offset,
                        "orientation": orientation,
                    }
                )
    return candidates


def _resize_with_pad(image, size: int) -> np.ndarray:
    import torch as th
    import torch.nn.functional as functional

    image = th.as_tensor(image)[..., :3]
    height, width = image.shape[:2]
    scale = min(size / height, size / width)
    resized_height = max(1, round(height * scale))
    resized_width = max(1, round(width * scale))
    resized = functional.interpolate(
        image.permute(2, 0, 1).unsqueeze(0).float(),
        size=(resized_height, resized_width),
        mode="bilinear",
        align_corners=False,
    )[0]
    output = th.zeros((3, size, size), dtype=th.float32, device=resized.device)
    top = (size - resized_height) // 2
    left = (size - resized_width) // 2
    output[:, top : top + resized_height, left : left + resized_width] = resized
    return output.permute(1, 2, 0).clamp(0, 255).byte().cpu().numpy()


def _capture_legal_observation(evaluator, image_size: int) -> tuple[np.ndarray, np.ndarray]:
    missing = [key for key in (*RADIO_RGB_KEYS, RADIO_PROPRIO_KEY) if key not in evaluator.obs]
    if missing:
        raise KeyError(f"Oracle observation is missing legal policy fields: {missing}")
    images = np.stack([_resize_with_pad(evaluator.obs[key], image_size) for key in RADIO_RGB_KEYS])
    proprio = evaluator.obs[RADIO_PROPRIO_KEY]
    if hasattr(proprio, "detach"):
        proprio = proprio.detach().cpu().numpy()
    return images, np.asarray(proprio, dtype=np.float32)


def _joint_target_to_action(robot, joint_target, *, close_left: bool = True, close_right: bool = True):
    import torch as th

    joint_target = th.as_tensor(joint_target, dtype=th.float32)
    if getattr(robot, "_radio_lock_trunk_default", False):
        joint_target = joint_target.clone()
        joint_target[robot.trunk_control_idx] = robot.reset_joint_pos[robot.trunk_control_idx]
    action = th.zeros(robot.action_dim, dtype=th.float32)
    action[robot.trunk_action_idx] = joint_target[robot.trunk_control_idx]
    for arm in robot.arm_names:
        action[robot.arm_action_idx[arm]] = joint_target[robot.arm_control_idx[arm]]
    # Match the official B1K action convention. Values beyond [-1, 1] are
    # accepted by the simulator but become extreme normalization outliers.
    action[robot.gripper_action_idx["left"]] = -1.0 if close_left else 1.0
    action[robot.gripper_action_idx["right"]] = -1.0 if close_right else 1.0
    return action


def _radio_and_toggle_state(evaluator):
    from omnigibson.object_states import ToggledOn

    radios = [
        entity
        for name, entity in evaluator.env.task.object_scope.items()
        if name.startswith("radio_receiver.n.") and entity is not None
    ]
    if len(radios) != 1:
        raise RuntimeError(f"Expected one radio, found {len(radios)}.")
    radio = radios[0]
    return radio, radio.states[ToggledOn]


def _step_target(evaluator, action, *, capture_observation: bool):
    import omnigibson as og

    recording = evaluator._video_path is not None or evaluator._side_video_path is not None
    capture_observation = capture_observation or recording
    with og.sim.render_on_step(capture_observation):
        obs, _, terminated, truncated, info = evaluator.env.step(
            action,
            n_render_iterations=1,
            skip_obs=not capture_observation,
        )
    if capture_observation:
        obs = evaluator._sync_lights_and_get_obs(obs)
        evaluator.obs = evaluator._preprocess_obs(obs)
    if recording:
        evaluator._write_video()
    return bool(terminated), bool(truncated), info


def _refresh_observation(evaluator) -> None:
    import omnigibson as og

    og.sim.render()
    obs, _ = evaluator.env.get_obs()
    obs = evaluator._sync_lights_and_get_obs(obs)
    evaluator.obs = evaluator._preprocess_obs(obs)


def _record_toggle_proximity(evaluator, trial, toggle_state) -> None:
    import torch as th

    marker_position = toggle_state.visual_marker.get_position_orientation()[0]
    distances = [
        float(th.linalg.vector_norm(link.get_position_orientation()[0] - marker_position).item())
        for arm in evaluator.robot.arm_names
        for link in evaluator.robot.finger_links[arm]
    ]
    min_distance = min(distances)
    overlap_steps = int(toggle_state.robot_can_toggle_steps)
    finger_contact = toggle_state.obj in toggle_state._finger_contact_objs
    trial["min_finger_marker_distance"] = min(trial.get("min_finger_marker_distance", math.inf), min_distance)
    trial["max_toggle_overlap_steps"] = max(
        trial.get("max_toggle_overlap_steps", 0),
        overlap_steps,
    )
    trial["ever_finger_radio_contact"] = trial.get("ever_finger_radio_contact", False) or finger_contact
    if finger_contact and "first_contact_position" not in trial:
        radio = toggle_state.obj
        contact_positions = [
            evaluator.robot._find_finger_contact_position(arm, link.prim_path)
            for arm in evaluator.robot.arm_names
            for link in radio.links.values()
        ]
        contact_positions = [position for position in contact_positions if position is not None]
        if contact_positions:
            trial["first_contact_position"] = contact_positions[0].detach().clone()
    trial["toggle_proximity"].append((min_distance, overlap_steps, finger_contact))


def _execute_joint_sequence(evaluator, joint_sequence, trial, args, toggle_state) -> bool:
    for joint_target in joint_sequence:
        action_index = len(trial["actions"])
        capture = action_index % args.record_stride == 0
        if capture:
            _refresh_observation(evaluator)
            images, proprio = _capture_legal_observation(evaluator, args.image_size)
            trial["images"].append(images)
            trial["proprio"].append(proprio)
            trial["action_step_indices"].append(action_index)
        action = _joint_target_to_action(evaluator.robot, joint_target)
        trial["actions"].append(action.cpu().numpy())
        trial["last_joint_target"] = joint_target.detach().cpu().clone()
        terminated, truncated, _ = _step_target(evaluator, action, capture_observation=False)
        _record_toggle_proximity(evaluator, trial, toggle_state)
        if bool(toggle_state.get_value()):
            return True
        if terminated or truncated:
            return False
    return bool(toggle_state.get_value())


def _servo_joint_target(evaluator, target, trial, args, toggle_state) -> bool:
    """Approach an IK target with state-feedback-bounded position commands."""
    import torch as th

    controlled_indices = [evaluator.robot.trunk_control_idx]
    controlled_indices.extend(evaluator.robot.arm_control_idx[arm] for arm in evaluator.robot.arm_names)
    controlled_indices = th.cat([th.as_tensor(indices, dtype=th.long).reshape(-1) for indices in controlled_indices])
    target = th.as_tensor(target, dtype=th.float32).detach().cpu()
    for _ in range(args.contact_servo_max_steps):
        current = evaluator.robot.get_joint_positions().detach().cpu()
        error = target[controlled_indices] - current[controlled_indices]
        if float(th.max(th.abs(error)).item()) <= args.contact_servo_tolerance:
            break
        command = current.clone()
        command[controlled_indices] += th.clamp(error, min=-args.max_joint_step, max=args.max_joint_step)
        if _execute_joint_sequence(evaluator, command.unsqueeze(0), trial, args, toggle_state):
            return True
    return bool(toggle_state.get_value())


def _path_positions(robot, path):
    """Expand a CuRobo path by name without its duplicate-lock helper."""
    position = path.position
    if position.ndim == 1:
        position = position.unsqueeze(0)
    trajectory = robot.get_joint_positions().detach().cpu().unsqueeze(0).repeat(len(position), 1)
    robot_joint_indices = {name: index for index, name in enumerate(robot.joints.keys())}
    if len(path.joint_names) != position.shape[-1]:
        raise ValueError(f"Path joint names/positions differ: {len(path.joint_names)} != {position.shape[-1]}")
    for path_index, name in enumerate(path.joint_names):
        if name not in robot_joint_indices:
            raise KeyError(f"CuRobo path returned unknown robot joint {name!r}.")
        trajectory[:, robot_joint_indices[name]] = position[:, path_index].detach().cpu()
    return trajectory


def _ik_joint_target(robot, path):
    """Expand an IK-only JointState by name without CuRobo's duplicate-lock helper."""
    position = path.position
    if position.ndim > 1:
        position = position[-1]
    target = robot.get_joint_positions().detach().cpu().clone()
    robot_joint_indices = {name: index for index, name in enumerate(robot.joints.keys())}
    if len(path.joint_names) != len(position):
        raise ValueError(f"IK joint names/positions differ: {len(path.joint_names)} != {len(position)}")
    for name, value in zip(path.joint_names, position.detach().cpu()):
        if name not in robot_joint_indices:
            raise KeyError(f"CuRobo IK returned unknown robot joint {name!r}.")
        target[robot_joint_indices[name]] = value
    return target


def _contact_ik_targets(
    motion_generator,
    robot,
    marker_position,
    direction,
    orientation,
    finger_local_offset,
    offsets,
    args,
    embodiment,
):
    import torch as th
    from omnigibson.utils import transform_utils as transform_utils

    finger_world_offset = transform_utils.quat_apply(orientation, finger_local_offset)
    positions = th.stack(
        [marker_position + direction * float(offset) - finger_world_offset for offset in offsets]
    )
    orientations = th.stack([orientation] * len(offsets))
    successes, paths = motion_generator.compute_trajectories(
        positions,
        orientations,
        initial_joint_pos=robot.get_joint_positions(),
        max_attempts=args.planner_max_attempts,
        timeout=args.planner_timeout,
        skip_obstacle_update=True,
        ik_only=True,
        ik_world_collision_check=False,
        emb_sel=embodiment,
    )
    return [
        _ik_joint_target(robot, path) if bool(success) and path is not None else None
        for success, path in zip(successes, paths)
    ]


def _save_success(output_path: Path, metadata: dict, candidate: dict, trial: dict, args, task_success: bool) -> None:
    actions = np.asarray(trial["actions"], dtype=np.float32)
    start_indices = np.asarray(trial["action_step_indices"], dtype=np.int64)
    chunks = build_action_chunks(actions, start_indices, args.action_horizon)
    temporary_path = output_path.with_suffix(".npz.tmp")
    with temporary_path.open("wb") as file:
        np.savez_compressed(
            file,
            format_version=np.asarray(1, dtype=np.int32),
            label_source=np.asarray("privileged_train_only_verified_toggle_oracle"),
            snapshot_metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
            candidate_json=np.asarray(json.dumps(candidate, sort_keys=True)),
            image_keys=np.asarray(RADIO_RGB_KEYS),
            images=np.asarray(trial["images"], dtype=np.uint8),
            proprio=np.asarray(trial["proprio"], dtype=np.float32),
            action_step_indices=start_indices,
            actions=chunks,
            executed_actions=actions,
            prompt=np.asarray("turn on the radio"),
            toggled=np.asarray(True),
            task_success=np.asarray(bool(task_success)),
        )
    os.replace(temporary_path, output_path)


def main() -> None:
    args = parse_args()
    if args.max_candidates < 1 or args.planner_batch_size < 1 or args.candidate_start_index < 0:
        raise ValueError("Candidate and planner batch counts must be positive.")
    if args.record_stride < 1 or args.image_size < 1 or args.max_joint_step <= 0:
        raise ValueError("record-stride, image-size, and max-joint-step must be positive.")
    if args.contact_servo_max_steps < 1 or args.contact_servo_tolerance <= 0:
        raise ValueError("contact-servo-max-steps and contact-servo-tolerance must be positive.")
    metadata = load_snapshot_metadata(args.snapshot, allow_non_press=args.allow_non_press_snapshot)
    args.snapshot = args.snapshot.expanduser().resolve()
    args.output_dir = args.output_dir.expanduser().resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Isaac Sim ships a second, older Warp package in its extension cache. Load
    # CuRobo's pinned external Warp (including the torch bridge) before the app
    # mutates sys.path, otherwise a mixed 1.12/1.8 runtime has no CUDA context.
    import warp as warp
    import warp.torch as warp_torch  # noqa: F401

    warp.init()
    import curobo.geom.sdf.world_mesh  # noqa: F401
    import torch as th
    from omegaconf import OmegaConf

    from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection
    from omnigibson.action_primitives.curobo import CuRoboMotionGenerator
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm

    gm.HEADLESS = args.headless
    seed_everything(args.seed)
    robot_config = OmegaConf.load(str(args.robot_config.expanduser().resolve()))
    robot_config.grasping_mode = "physical"
    _require_physical_grasp_config(robot_config)
    base_controller = robot_config.controller_config.base
    primitive_config = OmegaConf.load(str(Path(__file__).parents[1] / "configs" / "r1pro_primitives.yaml"))
    robot_config.controller_config = primitive_config.robots[0].controller_config
    robot_config.controller_config.base = base_controller
    cfg = OmegaConf.create(
        {
            "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
            "policy_name": "local",
            "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
            "headless": args.headless,
            "partial_scene_load": True,
            "max_steps": 10_000,
            "write_video": False,
            "write_side_video": False,
            "chunk_boundary_observations": False,
            "training_fail_fast": False,
            "mode": "train",
            "seed": args.seed,
            "task": {"name": "turning_on_radio"},
            "robot": robot_config,
        }
    )

    summary = {
        "format_version": 1,
        "label_source": "privileged_train_only_verified_toggle_oracle",
        "snapshot": str(args.snapshot),
        "snapshot_metadata": metadata,
        "attempts": [],
        "success_paths": [],
        "mobility": args.mobility,
    }
    summary_path = args.output_dir / "summary.json"
    embodiment = CuRoboEmbodimentSelection.ARM
    with Evaluator(cfg) as evaluator:
        evaluator.robot._radio_lock_trunk_default = False
        evaluator.reset(seed=args.seed)
        evaluator.load_task_instance(int(metadata["instance_id"]))
        evaluator.reset(seed=int(metadata["seed"]))
        table_radio, _ = _radio_and_toggle_state(evaluator)
        table_radio_pose = tuple(value.detach().clone() for value in table_radio.get_position_orientation())
        evaluator.load_radio_training_recovery_snapshot(
            str(args.snapshot),
            expected_metadata=_snapshot_identity(metadata),
        )
        summary["snapshot_robot_base_q"] = (
            evaluator.robot.get_joint_positions()[evaluator.robot.base_control_idx].detach().cpu().tolist()
        )
        summary["snapshot_robot_world_pose"] = [
            value.detach().cpu().tolist() for value in evaluator.robot.get_position_orientation()
        ]
        summary["snapshot_eef_poses"] = {
            arm: [value.detach().cpu().tolist() for value in evaluator.robot.get_eef_pose(arm=arm)]
            for arm in evaluator.robot.arm_names
        }
        summary["snapshot_radio_pose"] = [
            value.detach().cpu().tolist() for value in radio.get_position_orientation()
        ] if 'radio' in locals() else None
        if args.video_path is not None or args.side_video_path is not None:
            for path in (args.video_path, args.side_video_path):
                if path is not None:
                    path.expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
            evaluator.start_recording(
                str(args.video_path.expanduser().resolve()) if args.video_path is not None else None,
                side_fpath=(
                    str(args.side_video_path.expanduser().resolve())
                    if args.side_video_path is not None
                    else None
                ),
            )
        radio, toggle_state = _radio_and_toggle_state(evaluator)
        summary["snapshot_radio_pose"] = [
            value.detach().cpu().tolist() for value in radio.get_position_orientation()
        ]
        if bool(toggle_state.get_value()):
            raise ValueError("Snapshot is already toggled; it cannot supervise a recovery press.")
        marker_position, marker_orientation = toggle_state.visual_marker.get_position_orientation()
        all_candidates = _candidate_standoffs(
            evaluator.robot,
            marker_position,
            marker_orientation,
            args.standoff_distances,
            args.orientation_yaw_degrees,
            args.orientation_mode,
        )
        candidate_stop_index = args.candidate_start_index + args.max_candidates
        candidates = all_candidates[args.candidate_start_index : candidate_stop_index]
        if not candidates:
            raise ValueError(
                f"Candidate slice [{args.candidate_start_index}:{candidate_stop_index}] is empty; "
                f"only {len(all_candidates)} candidates exist."
            )
        summary["toggle_overlap_radius"] = float(
            th.min(toggle_state.visual_marker.extent * toggle_state.scale * toggle_state.link.scale).item()
        )
        lock_joint_names = [evaluator.robot.trunk_joint_names[-1]]
        if args.mobility == "left_only":
            lock_joint_names = [*evaluator.robot.trunk_joint_names, *evaluator.robot.arm_joint_names["right"]]
        elif args.mobility == "left_torso":
            lock_joint_names.extend(evaluator.robot.arm_joint_names["right"])
        motion_generator = CuRoboMotionGenerator(
            evaluator.robot,
            batch_size=args.planner_batch_size,
            use_cuda_graph=False,
            # Always lock torso_joint4: it is effectively stationary in the
            # official demonstrations, so moving it creates extreme normalized
            # labels. More expressive modes are explicit train-only fallbacks.
            lock_joint_names=lock_joint_names,
        )
        # A press-retry snapshot commonly contains an assisted right-hand grasp.
        # Treating that same radio as a static world obstacle makes the initial
        # state collide with itself. The target is ignored only in this privileged
        # train-time planner; table/world and robot self-collisions remain enabled.
        motion_generator.update_obstacles(ignore_objects=[radio])
        initial_collision = motion_generator.check_collisions(
            evaluator.robot.get_joint_positions().unsqueeze(0),
            skip_obstacle_update=True,
        )
        summary["initial_collision_with_radio_ignored"] = bool(initial_collision.reshape(-1)[0])
        positions = th.stack([candidate["position"] for candidate in candidates])
        orientations = th.stack([candidate["orientation"] for candidate in candidates])
        planning_successes, planning_paths = motion_generator.compute_trajectories(
            positions,
            orientations,
            max_attempts=args.planner_max_attempts,
            timeout=args.planner_timeout,
            skip_obstacle_update=True,
            emb_sel=embodiment,
        )

        for local_candidate_index, (candidate, planning_success, planning_path) in enumerate(
            zip(candidates, planning_successes, planning_paths)
        ):
            candidate_index = args.candidate_start_index + local_candidate_index
            candidate_record = {
                "candidate_index": candidate_index,
                "direction_index": candidate["direction_index"],
                "orientation_index": candidate["orientation_index"],
                "standoff_distance": candidate["distance"],
                "standoff_planning_success": bool(planning_success),
                "direction": candidate["direction"].cpu().tolist(),
                "standoff_position": candidate["position"].cpu().tolist(),
                "finger_target_position": candidate["finger_target_position"].cpu().tolist(),
                "finger_local_offset": candidate["finger_local_offset"].cpu().tolist(),
                "orientation": candidate["orientation"].cpu().tolist(),
                "contact_attempts": [],
                "toggled": False,
            }
            summary["attempts"].append(candidate_record)
            direct_contact_fallback = not bool(planning_success) or planning_path is None
            candidate_record["direct_contact_fallback"] = bool(direct_contact_fallback)
            if direct_contact_fallback and not args.allow_direct_contact_fallback:
                _atomic_json(summary_path, summary)
                continue

            evaluator.load_radio_training_recovery_snapshot(
                str(args.snapshot),
                expected_metadata=_snapshot_identity(metadata),
            )
            if args.reset_radio_to_table:
                radio, _ = _radio_and_toggle_state(evaluator)
                radio.set_position_orientation(*table_radio_pose)
                q = evaluator.robot.get_joint_positions().clone()
                right_idx = evaluator.robot.arm_control_idx["right"]
                q[right_idx] = evaluator.robot.reset_joint_pos[right_idx]
                q[evaluator.robot.base_control_idx] = evaluator.robot.get_joint_positions()[evaluator.robot.base_control_idx]
                evaluator.robot.set_joint_positions(q)
                import omnigibson as og
                og.sim.step_physics()
            _, toggle_state = _radio_and_toggle_state(evaluator)
            trial = {
                "actions": [],
                "images": [],
                "proprio": [],
                "action_step_indices": [],
                "min_finger_marker_distance": math.inf,
                "max_toggle_overlap_steps": 0,
                "ever_finger_radio_contact": False,
                "toggle_proximity": [],
            }
            trial["initial_radio_z"] = float(_radio_and_toggle_state(evaluator)[0].get_position_orientation()[0][2])
            _record_toggle_proximity(evaluator, trial, toggle_state)
            toggled = False
            if not direct_contact_fallback:
                standoff_trajectory = _path_positions(evaluator.robot, planning_path)
                toggled = _execute_joint_sequence(evaluator, standoff_trajectory, trial, args, toggle_state)
            if not toggled:
                current_marker, _ = toggle_state.visual_marker.get_position_orientation()
                contact_targets = _contact_ik_targets(
                    motion_generator,
                    evaluator.robot,
                    current_marker,
                    candidate["direction"],
                    candidate["orientation"],
                    candidate["finger_local_offset"],
                    args.contact_offsets,
                    args,
                    embodiment,
                )
                for offset, target in zip(args.contact_offsets, contact_targets):
                    contact_record = {"offset": float(offset), "ik_success": target is not None}
                    candidate_record["contact_attempts"].append(contact_record)
                    if target is None:
                        continue
                    proximity_start = len(trial["toggle_proximity"])
                    toggled = _servo_joint_target(evaluator, target, trial, args, toggle_state)
                    if not toggled:
                        dwell = target.unsqueeze(0).repeat(args.contact_dwell_steps, 1)
                        toggled = _execute_joint_sequence(evaluator, dwell, trial, args, toggle_state)
                    proximity = trial["toggle_proximity"][proximity_start:]
                    contact_record["min_finger_marker_distance"] = min(item[0] for item in proximity)
                    contact_record["max_toggle_overlap_steps"] = max(item[1] for item in proximity)
                    contact_record["ever_finger_radio_contact"] = any(item[2] for item in proximity)
                    contact_record["toggled"] = bool(toggled)
                    if toggled:
                        break

            if args.assisted_after_contact and trial["ever_finger_radio_contact"]:
                radio, _ = _radio_and_toggle_state(evaluator)
                link_name = next(iter(radio.links))
                contact = evaluator.robot._find_finger_contact_position("left", radio.links[link_name].prim_path)
                if contact is None:
                    contact = trial.get("first_contact_position")
                if contact is None:
                    contact = th.as_tensor(candidate["finger_target_position"], dtype=th.float32)
                joint_type = evaluator.robot._get_assisted_grasp_joint_type(radio, link_name)
                if contact is not None and joint_type is not None:
                    evaluator.robot._establish_grasp(radio, link_name, "left", contact, joint_type)
                    candidate_record["assisted_grasp_after_physical_contact"] = True
                    candidate_record["grasp_success"] = True
                    evaluator.robot._radio_lock_trunk_default = True
                    q = evaluator.robot.get_joint_positions().clone()
                    q[evaluator.robot.trunk_control_idx] = evaluator.robot.reset_joint_pos[evaluator.robot.trunk_control_idx]
                    evaluator.robot.set_joint_positions(q)
                    import omnigibson as og
                    og.sim.step_physics()
                    hold_target = evaluator.robot.get_joint_positions().clone()
                    _execute_joint_sequence(
                        evaluator,
                        [hold_target] * 60,
                        trial,
                        args,
                        toggle_state,
                    )
                    eef_position, eef_orientation = evaluator.robot.eef_links["left"].get_position_orientation()
                    lift_position = eef_position + th.tensor([0.0, 0.0, 0.10])
                    lift_successes, lift_paths = motion_generator.compute_trajectories(
                        lift_position.unsqueeze(0), eef_orientation.unsqueeze(0),
                        initial_joint_pos=evaluator.robot.get_joint_positions(),
                        max_attempts=args.planner_max_attempts, timeout=args.planner_timeout,
                        skip_obstacle_update=True, emb_sel=embodiment,
                    )
                    if bool(lift_successes[0]) and lift_paths[0] is not None:
                        _execute_joint_sequence(evaluator, _path_positions(evaluator.robot, lift_paths[0]), trial, args, toggle_state)
                        candidate_record["lift_success"] = True

            task_success = bool(evaluator.env.task.success)
            candidate_record["toggled"] = bool(toggled)
            candidate_record["task_success"] = task_success
            candidate_record["assisted_constraints"] = {
                arm: constraint is not None for arm, constraint in evaluator.robot._ag_obj_constraints.items()
            }
            candidate_record["initial_radio_z"] = trial["initial_radio_z"]
            candidate_record["final_radio_z"] = float(_radio_and_toggle_state(evaluator)[0].get_position_orientation()[0][2])
            candidate_record["radio_height_delta"] = candidate_record["final_radio_z"] - candidate_record["initial_radio_z"]
            trunk_q = evaluator.robot.get_joint_positions()[evaluator.robot.trunk_control_idx]
            default_trunk_q = evaluator.robot.reset_joint_pos[evaluator.robot.trunk_control_idx]
            candidate_record["final_trunk_q"] = trunk_q.detach().cpu().tolist()
            candidate_record["default_trunk_q"] = default_trunk_q.detach().cpu().tolist()
            candidate_record["final_trunk_max_abs_error"] = float(th.max(th.abs(trunk_q - default_trunk_q)))
            base_position, base_quat = evaluator.robot.get_position_orientation()
            from omnigibson.utils import transform_utils
            base_euler = transform_utils.quat2euler(base_quat)
            candidate_record["final_base_world_pose"] = [base_position.detach().cpu().tolist(), base_quat.detach().cpu().tolist()]
            candidate_record["final_base_planar_pose"] = [float(base_position[0]), float(base_position[1]), float(base_euler[2])]
            candidate_record["final_base_nonplanar_abs_max"] = float(th.max(th.abs(th.stack((base_position[2], base_euler[0], base_euler[1])))))
            candidate_record["executed_steps"] = len(trial["actions"])
            candidate_record["min_finger_marker_distance"] = trial["min_finger_marker_distance"]
            candidate_record["max_toggle_overlap_steps"] = trial["max_toggle_overlap_steps"]
            candidate_record["ever_finger_radio_contact"] = trial["ever_finger_radio_contact"]
            if toggled:
                output_path = args.output_dir / f"success-{len(summary['success_paths']):03d}.npz"
                _save_success(output_path, metadata, candidate_record, trial, args, task_success)
                summary["success_paths"].append(str(output_path))
            _atomic_json(summary_path, summary)

        _atomic_json(summary_path, summary)

    _atomic_json(summary_path, summary)


if __name__ == "__main__":
    main()
