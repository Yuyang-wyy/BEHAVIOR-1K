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
    parser.add_argument("--reference-grasp-pose", type=float, nargs=7)
    parser.add_argument("--pregrasp-retreat", type=float, default=0.10)
    parser.add_argument("--contact-overtravel", type=float, default=0.08)
    parser.add_argument("--contact-step", type=float, default=0.005)
    parser.add_argument("--contact-position-tolerance", type=float, default=0.005)
    parser.add_argument("--cartesian-lift-height", type=float, default=0.0)
    parser.add_argument("--lift-max-joint-step", type=float, default=0.002)
    parser.add_argument("--hold-steps", type=int, default=0)
    parser.add_argument("--reference-base-pose", type=float, nargs=3)
    parser.add_argument("--start-snapshot", type=Path)
    parser.add_argument("--lock-default-trunk", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--grasp-arm", choices=("left", "right"), default="left")
    parser.add_argument("--reference-eef-world", type=float, nargs=7)
    parser.add_argument("--assisted-after-contact", action="store_true")
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
    from omnigibson.eval.collect_radio_recovery_oracle import (
        _radio_and_toggle_state,
        _require_physical_grasp_config,
        _step_target,
    )
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm

    class RightArmPrimitives(StarterSemanticActionPrimitives):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.close_right = False
            self.reference_grasp_in_radio = None
            self.locked_posture = None

        @property
        def arm(self):
            return args.grasp_arm

        def _action_for_joint_target(self, target):
            from omnigibson.eval.collect_radio_recovery_oracle import _joint_target_to_action
            if self.locked_posture is not None:
                target = target.clone()
                posture_idx, posture_q = self.locked_posture
                target[posture_idx] = posture_q
            return _joint_target_to_action(
                self.robot, target,
                close_left=self.close_right and self.arm == "left",
                close_right=self.close_right and self.arm == "right",
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
            if args.reference_eef_world is not None:
                grasp_pose = (th.tensor(args.reference_eef_world[:3]), th.tensor(args.reference_eef_world[3:]))
                pregrasp_pose = (grasp_pose[0] + th.tensor([0.0, 0.0, args.pregrasp_retreat]), grasp_pose[1])
            elif self.reference_grasp_in_radio is None:
                grasp_pose = (center + th.tensor([0.0, 0.0, float(extent[2]) * 0.5 + 0.015]), orientation)
                pregrasp_pose = self.robot.eef_links[self.arm].get_position_orientation()
            else:
                from omnigibson.utils import transform_utils
                radio_pos, radio_quat = obj.get_position_orientation()
                grasp_pose = transform_utils.pose_transform(
                    radio_pos, radio_quat, *self.reference_grasp_in_radio
                )
                pregrasp_local_pos = self.reference_grasp_in_radio[0].clone()
                outward = pregrasp_local_pos[:2]
                outward = outward / th.linalg.vector_norm(outward)
                pregrasp_local_pos[:2] += outward * self.pregrasp_retreat
                pregrasp_pose = transform_utils.pose_transform(
                    radio_pos,
                    radio_quat,
                    pregrasp_local_pos,
                    self.reference_grasp_in_radio[1],
                )
            yield from self._move_hand(pregrasp_pose)
            yield from self._move_hand(grasp_pose, motion_constraint=[1, 1, 1, 1, 1, 0], stop_on_ag=True)
            if self.reference_grasp_in_radio is not None:
                from omnigibson.utils.usd_utils import RigidContactAPI

                radio_links = set(obj.links.values())
                for distance in th.arange(self.contact_step, self.contact_overtravel + 1e-6, self.contact_step):
                    contact_local_pos = self.reference_grasp_in_radio[0].clone()
                    contact_local_pos[:2] -= outward * distance
                    contact_pose = transform_utils.pose_transform(
                        radio_pos,
                        radio_quat,
                        contact_local_pos,
                        self.reference_grasp_in_radio[1],
                    )
                    yield from self._move_hand(contact_pose, motion_constraint=[1, 1, 1, 1, 1, 0])
                    actual_grasp_in_radio = transform_utils.relative_pose_transform(
                        *self.robot.eef_links[self.arm].get_position_orientation(),
                        *obj.get_position_orientation(),
                    )
                    self.approach_distance = float(distance)
                    self.approach_grasp_in_radio = actual_grasp_in_radio
                    reached_depth = (
                        th.dot(actual_grasp_in_radio[0][:2] - self.reference_grasp_in_radio[0][:2], outward)
                        <= self.contact_position_tolerance
                    )
                    finger_contact = any(
                        RigidContactAPI.is_in_contact(
                            scene_idx=self.env.scene.idx,
                            query_set={finger},
                            with_set=radio_links,
                            ignore_set=None,
                            current_only=True,
                        )
                        for finger in self.robot.finger_links[self.arm]
                    )
                    if reached_depth or finger_contact:
                        break
            yield from self._execute_grasp()
            yield from self._settle_robot()
            if args.assisted_after_contact:
                from omnigibson.utils.usd_utils import RigidContactAPI
                if any(RigidContactAPI.is_in_contact(scene_idx=self.env.scene.idx, query_set={finger}, with_set=set(obj.links.values()), ignore_set=None, current_only=True) for finger in self.robot.finger_links[self.arm]):
                    contact = self.robot._find_finger_contact_position(self.arm, next(iter(obj.links.values())).prim_path)
                    joint_type = self.robot._get_assisted_grasp_joint_type(obj, next(iter(obj.links)))
                    if contact is not None and joint_type is not None:
                        self.robot._establish_grasp(obj, next(iter(obj.links)), self.arm, contact, joint_type)

        def _move_hand(self, target_pose, max_joint_step=0.015, **kwargs):
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
            n_steps = max(1, int(th.ceil(th.max(th.abs(target - current)) / max_joint_step).item()))
            yield from self._execute_motion_plan(
                th.stack([current + (target - current) * (i / n_steps) for i in range(1, n_steps + 1)])
            )

    gm.HEADLESS = True
    seed_everything(args.seed)
    robot_config = OmegaConf.load(str(args.robot_config.resolve()))
    robot_config.grasping_mode = "physical"
    _require_physical_grasp_config(robot_config)
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
        joint_name_to_idx = {name: i for i, name in enumerate(evaluator.robot.joints.keys())}
        base_posture_names = [
            name for name in (
                "base_footprint_z_joint", "base_footprint_rx_joint", "base_footprint_ry_joint"
            ) if name in joint_name_to_idx
        ]
        base_posture_idx = th.tensor([joint_name_to_idx[name] for name in base_posture_names], dtype=th.long)
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
        reference_grasp_in_radio = None
        if args.reference_grasp_pose:
            reference_grasp_in_radio = (
                th.tensor(args.reference_grasp_pose[:3]),
                th.tensor(args.reference_grasp_pose[3:]),
            )
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
            if args.grasp_arm == "left":
                delta = reference_base_pose[:2] - reference_radio.get_position_orientation()[0][:2]
                reference_base_pose[:2] = reference_radio.get_position_orientation()[0][:2] + th.stack((delta[1], -delta[0]))
                reference_base_pose[2] -= th.pi / 2
            if reference_grasp_in_radio is None:
                reference_grasp_in_radio = transform_utils.relative_pose_transform(
                    *evaluator.robot.eef_links[args.grasp_arm].get_position_orientation(),
                    *reference_radio.get_position_orientation(),
                )
            og.sim.load_state(initial_state, serialized=True)
            og.sim.step_physics()
            og.sim.render()
        if args.lock_default_trunk:
            evaluator.robot.set_joint_positions(
                evaluator.robot.reset_joint_pos[evaluator.robot.trunk_control_idx],
                indices=evaluator.robot.trunk_control_idx,
            )
            evaluator.robot.set_joint_positions(
                evaluator.robot.reset_joint_pos[base_posture_idx], indices=base_posture_idx
            )
            og.sim.step_physics()
        default_trunk_q = evaluator.robot.reset_joint_pos[evaluator.robot.trunk_control_idx].clone()
        initial_trunk_q = evaluator.robot.get_joint_positions()[evaluator.robot.trunk_control_idx].clone()
        default_base_posture = evaluator.robot.reset_joint_pos[base_posture_idx].clone()
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
        primitives.reference_grasp_in_radio = reference_grasp_in_radio
        if args.lock_default_trunk:
            posture_idx = th.cat((evaluator.robot.trunk_control_idx, base_posture_idx))
            posture_q = th.cat((default_trunk_q, default_base_posture))
            primitives.locked_posture = (posture_idx, posture_q)
        primitives.pregrasp_retreat = args.pregrasp_retreat
        primitives.contact_overtravel = args.contact_overtravel
        primitives.contact_step = args.contact_step
        primitives.contact_position_tolerance = args.contact_position_tolerance
        # The stock R1Pro ARM CuRobo model targets only left_eef_link. Generate
        # the symmetric right-arm model once so the privileged grasp is planned
        # for the arm that actually holds the radio.
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection, CuRoboMotionGenerator
        source_cfg = Path(__file__).resolve().parents[3] / "datasets/omnigibson-robot-assets/models/r1pro/curobo/r1pro_description_curobo_arm.yaml"
        right_cfg = args.output_dir / "r1pro_description_curobo_right.yaml"
        # The stock ARM model already contains both arms; only switch its
        # commanded end-effector. Keep the original cspace and lock the left
        # arm below, rather than duplicating joint names.
        text_cfg = source_cfg.read_text().replace("ee_link: left_eef_link", f"ee_link: {args.grasp_arm}_eef_link")
        # Keep auxiliary links empty: the motion generator appends ee_link and
        # otherwise treats right_eef_link as an unsupported additional-link cost.
        text_cfg = text_cfg.replace("    link_names:\n    - right_eef_link", "    link_names: []")
        right_cfg.write_text(text_cfg)
        lock_joint_names = list(evaluator.robot.arm_joint_names["right" if args.grasp_arm == "left" else "left"])
        if args.lock_default_trunk:
            lock_joint_names.extend(evaluator.robot.trunk_joint_names)
            lock_joint_names.extend(base_posture_names)
        primitives._motion_generator = CuRoboMotionGenerator(
            evaluator.robot, robot_cfg_path={CuRoboEmbodimentSelection.ARM: str(right_cfg)},
            batch_size=1, use_cuda_graph=False,
            lock_joint_names=lock_joint_names,
        )
        print("RIGHT_CUROBO", primitives._motion_generator.ee_link, primitives._motion_generator.additional_links)
        steps = 0
        error = None
        max_height = initial_height
        from omnigibson.utils.usd_utils import RigidContactAPI
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
            from omnigibson.controllers.controller_base import IsGraspingState

            radio_links = set(radio.links.values())
            finger_contacts = [
                RigidContactAPI.is_in_contact(
                    scene_idx=evaluator.env.scene.idx,
                    query_set={finger},
                    with_set=radio_links,
                    ignore_set=None,
                    current_only=True,
                )
                for finger in evaluator.robot.finger_links[args.grasp_arm]
            ]
            controller_grasp = (
                evaluator.robot.is_grasping(args.grasp_arm, candidate_obj=radio) == IsGraspingState.TRUE
            )
            physical_grasp = all(finger_contacts)
            acquisition_gripper_qpos = (
                evaluator.robot.get_joint_positions()[evaluator.robot.gripper_control_idx[args.grasp_arm]]
                .detach()
                .cpu()
                .tolist()
            )
            if physical_grasp:
                if args.cartesian_lift_height:
                    eef_position, eef_orientation = evaluator.robot.eef_links[args.grasp_arm].get_position_orientation()
                    for action in primitives._move_hand(
                        (eef_position + th.tensor([0.0, 0.0, args.cartesian_lift_height]), eef_orientation),
                        max_joint_step=args.lift_max_joint_step,
                    ):
                        _step_target(evaluator, action, capture_observation=False)
                        steps += 1
                        max_height = max(max_height, float(radio.get_position_orientation()[0][2]))
                hold_target = evaluator.robot.get_joint_positions().clone()
                for _ in range(args.hold_steps):
                    _step_target(
                        evaluator,
                        primitives._action_for_joint_target(hold_target),
                        capture_observation=False,
                    )
                    steps += 1
                    max_height = max(max_height, float(radio.get_position_orientation()[0][2]))
        except Exception as exc:  # Preserve diagnostics and video for failed TAMP attempts.
            import traceback
            traceback.print_exc()
            error = f"{type(exc).__name__}: {exc}"

        assisted_constraints = {
            arm: constraint is not None for arm, constraint in evaluator.robot._ag_obj_constraints.items()
        }
        if any(assisted_constraints.values()):
            raise RuntimeError(f"Assisted grasp constraint detected: {assisted_constraints}")
        final_finger_contacts = [
            RigidContactAPI.is_in_contact(
                scene_idx=evaluator.env.scene.idx,
                query_set={finger},
                with_set=set(radio.links.values()),
                ignore_set=None,
                current_only=True,
            )
            for finger in evaluator.robot.finger_links[args.grasp_arm]
        ]
        held = all(final_finger_contacts)
        final_height = float(radio.get_position_orientation()[0][2])
        final_trunk_q = evaluator.robot.get_joint_positions()[evaluator.robot.trunk_control_idx]
        final_base_posture = evaluator.robot.get_joint_positions()[base_posture_idx]
        from omnigibson.utils import transform_utils

        final_eef_pose = evaluator.robot.eef_links[args.grasp_arm].get_position_orientation()
        final_radio_pose = radio.get_position_orientation()
        final_grasp_in_radio = transform_utils.relative_pose_transform(
            *final_eef_pose, *final_radio_pose
        )
        summary.update(
            executed_steps=steps,
            right_hand_holds_radio=held,
            acquired_two_finger_contact=bool(locals().get("physical_grasp", False)),
            controller_grasp=bool(locals().get("controller_grasp", False)),
            acquisition_gripper_qpos=locals().get("acquisition_gripper_qpos"),
            approach_distance=getattr(primitives, "approach_distance", None),
            approach_grasp_in_radio=(
                [value.tolist() for value in primitives.approach_grasp_in_radio]
                if hasattr(primitives, "approach_grasp_in_radio")
                else None
            ),
            physical_grasp=held,
            finger_contacts=final_finger_contacts,
            assisted_constraints=assisted_constraints,
            requested_grasp_in_radio=(
                [value.tolist() for value in reference_grasp_in_radio]
                if reference_grasp_in_radio is not None
                else None
            ),
            final_grasp_in_radio=[value.tolist() for value in final_grasp_in_radio],
            final_eef_pose=[value.tolist() for value in final_eef_pose],
            final_radio_pose=[value.tolist() for value in final_radio_pose],
            initial_radio_height=initial_height,
            final_radio_height=final_height,
            radio_height_delta=final_height - initial_height,
            max_radio_height=max_height,
            lock_default_trunk=args.lock_default_trunk,
            default_trunk_q=default_trunk_q.tolist(),
            initial_trunk_q=initial_trunk_q.tolist(),
            final_trunk_q=final_trunk_q.tolist(),
            final_trunk_max_abs_error=float(th.max(th.abs(final_trunk_q - default_trunk_q))),
            default_base_posture=default_base_posture.tolist(),
            final_base_posture=final_base_posture.tolist(),
            final_base_posture_max_abs_error=float(th.max(th.abs(final_base_posture - default_base_posture))),
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
