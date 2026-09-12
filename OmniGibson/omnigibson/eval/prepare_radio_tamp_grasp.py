"""Use the existing starter TAMP primitive to grasp and present the task radio."""

import argparse
import json
import os
from pathlib import Path

import numpy as np


def _args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=int, default=199)
    parser.add_argument("--seed", type=int, default=291844035)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--robot-config", type=Path, default=Path(__file__).with_name("r1pro.yaml"))
    parser.add_argument("--video-path", type=Path)
    parser.add_argument("--side-video-path", type=Path)
    parser.add_argument("--reference-snapshot", type=Path)
    parser.add_argument("--reference-base-pose", type=float, nargs=3)
    parser.add_argument("--start-snapshot", type=Path)
    parser.add_argument("--privileged-assist-fallback", action="store_true")
    return parser.parse_args()


def main():
    args = _args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Import external Warp before Isaac Sim can put its bundled version first.
    import warp
    import warp.torch  # noqa: F401

    warp.init()
    import curobo.geom.sdf.world_mesh  # noqa: F401
    import omnigibson as og
    import torch as th
    from omegaconf import OmegaConf

    from omnigibson.action_primitives.starter_semantic_action_primitives import (
        StarterSemanticActionPrimitiveSet,
        StarterSemanticActionPrimitives,
    )
    from omnigibson.eval.collect_radio_recovery_oracle import _radio_and_toggle_state, _step_target
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm

    class RightArmPrimitives(StarterSemanticActionPrimitives):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.close_right = False
            self.reference_grasp_in_radio = None

        @property
        def arm(self):
            return "right"

        def _action_for_joint_target(self, target):
            from omnigibson.eval.collect_radio_recovery_oracle import _joint_target_to_action
            return _joint_target_to_action(
                self.robot, target, close_left=False, close_right=self.close_right
            )

        def _empty_action(self, follow_arm_targets=True):
            return self._action_for_joint_target(self.robot.get_joint_positions())

        def _settle_robot(self):
            for _ in range(20):
                yield self._postprocess_action(self._action_for_joint_target(self.robot.get_joint_positions()))

        def _execute_motion_plan(self, q_traj, **kwargs):
            for joint_pos in q_traj:
                yield self._postprocess_action(self._action_for_joint_target(joint_pos))

        def _move_fingers_to_limit_direct(self, limit_type):
            target = self._get_joint_position_with_fingers_at_limit(limit_type)
            for _ in range(80):
                yield self._postprocess_action(self._action_for_joint_target(target))
                if th.allclose(self.robot.get_joint_positions(), target, atol=0.01):
                    break

        def _execute_release(self):
            self.close_right = False
            yield from self._move_fingers_to_limit_direct("upper")

        def _execute_grasp(self):
            self.close_right = True
            yield from self._move_fingers_to_limit_direct("lower")

        def _grasp(self, obj):
            # The generic primitive re-samples a base pose even when the arm is already
            # beside the object; for this diagnostic, keep the TAMP base decision fixed.
            self._tracking_object = obj
            yield from self._execute_release()
            center = obj.aabb_center
            extent = obj.aabb_extent
            orientation = self.robot.eef_links[self.arm].get_position_orientation()[1]
            if self.reference_grasp_in_radio is None:
                grasp_pose = (center + th.tensor([0.0, 0.0, float(extent[2]) * 0.5 + 0.015]), orientation)
            else:
                from omnigibson.utils import transform_utils
                radio_pos, radio_quat = obj.get_position_orientation()
                grasp_pose = transform_utils.pose_transform(
                    radio_pos, radio_quat, *self.reference_grasp_in_radio
                )
            # Start from the recorded hand pose; a direct high pregrasp can be
            # outside the right-arm model's reachable workspace.
            pregrasp_pose = self.robot.eef_links[self.arm].get_position_orientation()
            yield from self._move_hand(pregrasp_pose)
            yield from self._move_hand(grasp_pose, motion_constraint=[1, 1, 1, 1, 1, 0], stop_on_ag=True)
            yield from self._execute_grasp()
            yield from self._settle_robot()

        def _move_hand(self, target_pose, **kwargs):
            from omnigibson.action_primitives.action_primitive_set_base import ActionPrimitiveError
            from omnigibson.eval.collect_radio_recovery_oracle import _contact_ik_targets
            from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection
            pos, quat = target_pose
            pos = th.as_tensor(pos, dtype=th.float32)
            quat = th.as_tensor(quat, dtype=th.float32)
            current_orientation = self.robot.eef_links[self.arm].get_position_orientation()[1]
            # CuRobo target is the robot's eef_link, not the finger centroid.
            # Passing the latter's offset double-shifts the pose on R1Pro.
            finger_offset = th.zeros(3)
            candidates = [(pos, quat)]
            if self._tracking_object is not None:
                obj_quat = self._tracking_object.get_position_orientation()[1]
                candidates.append((pos, obj_quat))
            candidates.append((pos, th.tensor([-0.114, -0.559, 0.655, 0.495], dtype=th.float32)))
            candidates.append((pos, th.tensor([0.0, 0.0, 0.0, 1.0], dtype=th.float32)))
            target = None
            for candidate_pos, candidate_quat in candidates:
                target = _contact_ik_targets(
                    self._motion_generator, self.robot, candidate_pos, th.zeros(3), candidate_quat,
                    finger_offset, [0.0], argparse.Namespace(planner_max_attempts=3, planner_timeout=2.0),
                    CuRoboEmbodimentSelection.ARM,
                )[0]
                if target is not None:
                    break
            if target is None:
                raise ActionPrimitiveError(
                    ActionPrimitiveError.Reason.PLANNING_ERROR,
                    "Radio grasp IK failed",
                )
            current = self.robot.get_joint_positions()
            n_steps = max(1, int(th.ceil(th.max(th.abs(target - current)) / 0.015).item()))
            yield from self._execute_motion_plan(
                th.stack([current + (target - current) * (i / n_steps) for i in range(1, n_steps + 1)])
            )

    gm.HEADLESS = True
    seed_everything(args.seed)
    robot_config = OmegaConf.load(str(args.robot_config.resolve()))
    if not args.start_snapshot:
        base_controller = robot_config.controller_config.base
        primitive_config = OmegaConf.load(
            str(Path(__file__).parents[1] / "configs" / "r1pro_primitives.yaml")
        )
        # The starter primitives require absolute joint-space base and gripper controllers.
        robot_config.controller_config = primitive_config.robots[0].controller_config
        robot_config.controller_config.base = base_controller
    cfg = OmegaConf.create(
        {
            "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
            "policy_name": "local",
            "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
            "headless": True,
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
    summary = {"instance_id": args.instance, "seed": args.seed, "phase": "grasp_and_present"}
    with Evaluator(cfg) as evaluator:
        evaluator.reset(seed=args.seed)
        evaluator.load_task_instance(args.instance)
        evaluator.reset(seed=args.seed)
        if args.start_snapshot:
            from omnigibson.eval.collect_radio_recovery_oracle import _snapshot_identity, load_snapshot_metadata
            metadata = load_snapshot_metadata(args.start_snapshot, allow_non_press=True)
            evaluator.load_radio_training_recovery_snapshot(
                str(args.start_snapshot), expected_metadata=_snapshot_identity(metadata)
            )
        reference_base_pose = th.tensor(args.reference_base_pose) if args.reference_base_pose else None
        if args.reference_snapshot:
            initial_state = og.sim.dump_state(serialized=True)
            with np.load(args.reference_snapshot, allow_pickle=False) as snapshot:
                og.sim.load_state(th.as_tensor(snapshot["simulator_state"]), serialized=True)
            og.sim.step_physics()
            reference_robot_pos, reference_robot_quat = evaluator.robot.get_position_orientation()
            reference_radio, _ = _radio_and_toggle_state(evaluator)
            from omnigibson.utils import transform_utils
            reference_base_pose = th.tensor([
                reference_robot_pos[0], reference_robot_pos[1],
                transform_utils.quat2euler(reference_robot_quat)[2],
            ])
            reference_grasp_in_radio = transform_utils.relative_pose_transform(
                *evaluator.robot.eef_links["right"].get_position_orientation(),
                *reference_radio.get_position_orientation(),
            )
            og.sim.load_state(initial_state, serialized=True)
            og.sim.step_physics()
            og.sim.render()
        evaluator.start_recording(
            str(args.video_path.resolve()) if args.video_path else None,
            side_fpath=str(args.side_video_path.resolve()) if args.side_video_path else None,
        )
        radio, _ = _radio_and_toggle_state(evaluator)
        initial_height = float(radio.get_position_orientation()[0][2])
        primitives = RightArmPrimitives(
            evaluator.env,
            evaluator.robot,
            enable_head_tracking=False,
            task_relevant_objects_only=True,
            curobo_batch_size=1,
        )
        primitives.reference_grasp_in_radio = locals().get("reference_grasp_in_radio")
        # The stock R1Pro ARM CuRobo model targets only left_eef_link. Generate
        # the symmetric right-arm model once so the privileged grasp is planned
        # for the arm that actually holds the radio.
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection, CuRoboMotionGenerator
        source_cfg = Path(__file__).resolve().parents[3] / "datasets/omnigibson-robot-assets/models/r1pro/curobo/r1pro_description_curobo_arm.yaml"
        right_cfg = args.output_dir / "r1pro_description_curobo_right.yaml"
        # The stock ARM model already contains both arms; only switch its
        # commanded end-effector. Keep the original cspace and lock the left
        # arm below, rather than duplicating joint names.
        text_cfg = source_cfg.read_text().replace("ee_link: left_eef_link", "ee_link: right_eef_link")
        # Keep auxiliary links empty: the motion generator appends ee_link and
        # otherwise treats right_eef_link as an unsupported additional-link cost.
        text_cfg = text_cfg.replace("    link_names:\n    - right_eef_link", "    link_names: []")
        right_cfg.write_text(text_cfg)
        primitives._motion_generator = CuRoboMotionGenerator(
            evaluator.robot, robot_cfg_path={CuRoboEmbodimentSelection.ARM: str(right_cfg)},
            batch_size=1, use_cuda_graph=False,
            lock_joint_names=evaluator.robot.arm_joint_names["left"],
        )
        print("RIGHT_CUROBO", primitives._motion_generator.ee_link, primitives._motion_generator.additional_links)
        steps = 0
        error = None
        privileged_assist_used = False
        max_height = initial_height
        try:
            if reference_base_pose is not None:
                for action in primitives._navigate_to_pose_direct(reference_base_pose):
                    _step_target(evaluator, action, capture_observation=False)
                    steps += 1
            # The stock apply_ref reset phase targets the left-arm model; this
            # diagnostic is already at the recorded base pose, so call the
            # radio-specific grasp primitive directly.
            for action in primitives._grasp(radio):
                if action is None:
                    continue
                _step_target(evaluator, action, capture_observation=False)
                steps += 1
                max_height = max(max_height, float(radio.get_position_orientation()[0][2]))
            if evaluator.robot._ag_obj_in_hand["right"] is not radio and args.privileged_assist_fallback:
                link_name = next(iter(radio.links))
                joint_type = evaluator.robot._get_assisted_grasp_joint_type(radio, link_name)
                if joint_type is None:
                    raise RuntimeError("Radio is not assisted-graspable")
                evaluator.robot._establish_grasp(
                    radio, link_name, "right", radio.aabb_center, joint_type
                )
                privileged_assist_used = True
                lift_target = evaluator.robot.get_joint_positions().clone()
                lift_target[list(evaluator.robot.joints.keys()).index("right_arm_joint1")] += 0.35
                for _ in range(120):
                    action = primitives._action_for_joint_target(lift_target)
                    _step_target(evaluator, action, capture_observation=False)
                    steps += 1
                    max_height = max(max_height, float(radio.get_position_orientation()[0][2]))
        except Exception as exc:  # Preserve diagnostics and video for failed TAMP attempts.
            import traceback
            traceback.print_exc()
            error = f"{type(exc).__name__}: {exc}"

        held = evaluator.robot._ag_obj_in_hand["right"] is radio
        final_height = float(radio.get_position_orientation()[0][2])
        summary.update(
            executed_steps=steps,
            right_hand_holds_radio=held,
            initial_radio_height=initial_height,
            final_radio_height=final_height,
            radio_height_delta=final_height - initial_height,
            max_radio_height=max_height,
            privileged_assist_used=privileged_assist_used,
            error=error,
        )
        if held:
            state = og.sim.dump_state(serialized=True).detach().cpu().numpy()
            metadata = {
                "task": "turning_on_radio",
                "instance_id": args.instance,
                "rollout_id": 0,
                "seed": args.seed,
                "mode": "train",
                "decision_index": steps,
                "simulator_step_index": steps,
                "triggers": ["press_retry_tamp"],
            }
            snapshot = args.output_dir / "post-grasp-press-retry.npz"
            temporary = snapshot.with_suffix(".npz.tmp")
            with temporary.open("wb") as file:
                np.savez_compressed(
                    file,
                    format_version=np.asarray(1, dtype=np.int32),
                    label_source=np.asarray("privileged_train_only_tamp"),
                    simulator_state=state,
                    state_size=np.asarray(len(state), dtype=np.int64),
                    metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
                )
            os.replace(temporary, snapshot)
            summary["snapshot"] = str(snapshot.resolve())
        path = args.output_dir / "grasp_summary.json"
        path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
