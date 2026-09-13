"""Continuously replay a raw radio demo segment with constraint-free physical grasping."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-hdf5", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=1360)
    parser.add_argument("--end-frame", type=int, default=1600)
    parser.add_argument("--finger-friction", type=float)
    parser.add_argument("--restore-each-frame", action="store_true")
    parser.add_argument("--robot-offset", type=float, nargs=3, default=(0.0, 0.0, 0.0))
    parser.add_argument("--radio-target-pose", type=float, nargs=7)
    parser.add_argument("--radio-pose-alpha", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    import h5py
    import numpy as np
    import torch as th
    import omnigibson as og
    from omnigibson.controllers.controller_base import IsGraspingState
    from omnigibson.envs import Environment
    from omnigibson.eval.extract_radio_event_labels import _prepare_recorded_scene, _task_object_names
    from omnigibson.macros import gm
    from omnigibson.object_states import OnTop
    from omnigibson.utils import transform_utils as T
    from omnigibson.utils.usd_utils import RigidContactAPI

    gm.HEADLESS = True
    gm.ENABLE_TRANSITION_RULES = False
    with h5py.File(args.raw_hdf5.expanduser().resolve(), "r") as raw:
        config = json.loads(raw["data"].attrs["config"])
        scene_file = json.loads(raw["data"].attrs["scene_file"])
        trajectory = raw["data/demo_0"]
        actions = trajectory["action"]
        states = trajectory["state"]
        state_sizes = trajectory["state_size"]
        if not 0 <= args.start_frame < args.end_frame <= len(actions):
            raise ValueError(f"Invalid frame range for {len(actions)} actions.")

        config["scene"]["scene_file"] = scene_file
        config["objects"] = []
        config["task"] = {"type": "DummyTask", "include_obs": False}
        config["env"]["flatten_obs_space"] = True
        for robot_config in config["robots"]:
            robot_config["obs_modalities"] = []
            robot_config["grasping_mode"] = "physical"
            if args.finger_friction is not None:
                robot_config["finger_static_friction"] = args.finger_friction
                robot_config["finger_dynamic_friction"] = args.finger_friction

        env = Environment(configs=config)
        try:
            playback = SimpleNamespace(
                scene=env.scene,
                robots=env.robots,
                recorded_scene_file=scene_file,
                scene_file=scene_file,
            )
            _prepare_recorded_scene(playback, trajectory, scene_file)
            radio_name, table_name = _task_object_names(scene_file)
            radio = env.scene.object_registry("name", radio_name)
            table = env.scene.object_registry("name", table_name)
            robot = env.robots[0]
            state_size = int(state_sizes[args.start_frame])
            og.sim.load_state(th.as_tensor(states[args.start_frame, :state_size]), serialized=True)
            if args.radio_target_pose is not None:
                radio_position, radio_orientation = radio.get_position_orientation()
                target_radio_position = th.tensor(args.radio_target_pose[:3])
                target_radio_orientation = th.tensor(args.radio_target_pose[3:])
                alpha = args.radio_pose_alpha
                radio.set_position_orientation(
                    radio_position + alpha * (target_radio_position - radio_position),
                    T.quat_slerp(radio_orientation, target_radio_orientation, th.tensor(alpha)),
                )
            robot_position, robot_orientation = robot.get_position_orientation()
            robot.set_position_orientation(
                robot_position + th.tensor(args.robot_offset), robot_orientation
            )
            og.sim.step()

            initial_z = float(radio.get_position_orientation()[0][2])
            initial_radio_pose = [
                value.detach().cpu().tolist() for value in radio.get_position_orientation()
            ]
            initial_radio_aabb = {
                "center": radio.aabb_center.detach().cpu().tolist(),
                "extent": radio.aabb_extent.detach().cpu().tolist(),
            }
            max_z = initial_z
            samples = []
            radio_links = set(radio.links.values())
            for frame in range(args.start_frame, args.end_frame):
                if args.restore_each_frame:
                    state_size = int(state_sizes[frame])
                    og.sim.load_state(th.as_tensor(states[frame, :state_size]), serialized=True)
                env.step(th.as_tensor(actions[frame]))
                radio_position = radio.get_position_orientation()[0]
                radio_z = float(radio_position[2])
                max_z = max(max_z, radio_z)
                finger_contacts = [
                    bool(
                        RigidContactAPI.is_in_contact(
                            scene_idx=env.scene.idx,
                            query_set={finger},
                            with_set=radio_links,
                            ignore_set=None,
                            current_only=True,
                        )
                    )
                    for finger in robot.finger_links["right"]
                ]
                contact_position = robot._find_finger_contact_position(
                    "right", next(iter(radio.links.values())).prim_path
                )
                radio_orientation = radio.get_position_orientation()[1]
                eef_position, eef_orientation = robot.eef_links["right"].get_position_orientation()
                samples.append(
                    {
                        "frame": frame,
                        "radio_z": radio_z,
                        "radio_position": radio_position.detach().cpu().tolist(),
                        "radio_orientation": radio_orientation.detach().cpu().tolist(),
                        "eef_position": eef_position.detach().cpu().tolist(),
                        "eef_orientation": eef_orientation.detach().cpu().tolist(),
                        "contact_position": (
                            contact_position.detach().cpu().tolist() if contact_position is not None else None
                        ),
                        "finger_positions": [
                            finger.get_position_orientation()[0].detach().cpu().tolist()
                            for finger in robot.finger_links["right"]
                        ],
                        "on_table": bool(radio.states[OnTop].get_value(table)),
                        "finger_contacts": finger_contacts,
                        "gripper_qpos": robot.get_joint_positions()[robot.gripper_control_idx["right"]]
                        .detach()
                        .cpu()
                        .tolist(),
                        "is_grasping": int(robot.is_grasping("right", candidate_obj=radio)),
                    }
                )

            result = {
                "raw_hdf5": str(args.raw_hdf5.expanduser().resolve()),
                "frame_range": [args.start_frame, args.end_frame],
                "restore_each_frame": args.restore_each_frame,
                "robot_offset": args.robot_offset,
                "radio_target_pose": args.radio_target_pose,
                "radio_pose_alpha": args.radio_pose_alpha,
                "grasping_mode": robot.grasping_mode,
                "finger_friction": args.finger_friction,
                "initial_radio_z": initial_z,
                "initial_radio_pose": initial_radio_pose,
                "initial_radio_aabb": initial_radio_aabb,
                "final_radio_z": samples[-1]["radio_z"],
                "max_radio_height_delta": max_z - initial_z,
                "ever_two_finger_contact": any(all(sample["finger_contacts"]) for sample in samples),
                "ever_physical_grasp": any(
                    sample["is_grasping"] == int(IsGraspingState.TRUE) for sample in samples
                ),
                "assisted_constraints": {
                    arm: constraint is not None for arm, constraint in robot._ag_obj_constraints.items()
                },
                "samples": samples,
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps({key: value for key, value in result.items() if key != "samples"}, indent=2))
        except BaseException:
            import traceback

            traceback.print_exc()
            raise
        finally:
            env.close()
            og.shutdown()


if __name__ == "__main__":
    main()
