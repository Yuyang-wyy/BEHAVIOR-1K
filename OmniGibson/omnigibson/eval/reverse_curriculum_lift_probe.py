"""Probe whether an already-held radio can be lifted by right-arm joint actions."""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instance", type=int, default=199)
    p.add_argument("--seed", type=int, default=291844035)
    p.add_argument("--start-snapshot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--joint", type=int, default=0)
    p.add_argument("--delta", type=float, default=0.25)
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--video", type=Path)
    p.add_argument("--regrasp", action="store_true")
    p.add_argument("--vector", type=float, nargs=7)
    p.add_argument("--retreat", type=float, default=0.0)
    p.add_argument("--retreat-steps", type=int, default=5)
    p.add_argument("--align-radio-xy", type=float, nargs=2)
    p.add_argument("--save-seed", type=Path)
    p.add_argument("--lift-vector", type=float, nargs=7)
    p.add_argument("--inspect-only", action="store_true")
    args = p.parse_args()

    import warp
    import warp.torch  # noqa: F401
    warp.init()
    import omnigibson as og
    import torch as th
    from omegaconf import OmegaConf
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.eval.collect_radio_recovery_oracle import (
        _joint_target_to_action,
        _radio_and_toggle_state,
        _require_physical_grasp_config,
        load_snapshot_metadata,
        _snapshot_identity,
        _step_target,
    )
    from omnigibson.macros import gm

    gm.HEADLESS = True
    seed_everything(args.seed)
    robot_cfg = OmegaConf.load(str(Path(__file__).with_name("r1pro.yaml")))
    _require_physical_grasp_config(robot_cfg)
    cfg = OmegaConf.create({
        "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
        "policy_name": "local", "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
        "headless": True, "partial_scene_load": True, "max_steps": 1000,
        "write_video": False, "write_side_video": False, "chunk_boundary_observations": False,
        "training_fail_fast": False, "mode": "train", "seed": args.seed,
        "task": {"name": "turning_on_radio"}, "robot": robot_cfg,
    })
    results = []
    with Evaluator(cfg) as evaluator:
        evaluator.reset(seed=args.seed)
        evaluator.load_task_instance(args.instance)
        evaluator.reset(seed=args.seed)
        metadata = load_snapshot_metadata(args.start_snapshot, allow_non_press=True)
        evaluator.load_radio_training_recovery_snapshot(
            str(args.start_snapshot), expected_metadata=_snapshot_identity(metadata)
        )
        evaluator.start_recording(str(args.video.resolve()) if args.video else None)
        radio, _ = _radio_and_toggle_state(evaluator)
        initial_q = evaluator.robot.get_joint_positions().clone()
        initial_h = float(radio.get_position_orientation()[0][2])
        pristine_state = og.sim.dump_state(serialized=True)
        right_names = list(evaluator.robot.arm_joint_names["right"])
        indices = [list(evaluator.robot.joints.keys()).index(name) for name in right_names]
        if args.inspect_only:
            robot_pos, robot_quat = evaluator.robot.get_position_orientation()
            eef_pos, eef_quat = evaluator.robot.eef_links["right"].get_position_orientation()
            radio_pos, radio_quat = radio.get_position_orientation()
            result = {
                "robot_position": robot_pos.tolist(), "robot_orientation": robot_quat.tolist(),
                "base_q": evaluator.robot.get_joint_positions()[evaluator.robot.base_control_idx].tolist(),
                "trunk_q": evaluator.robot.get_joint_positions()[evaluator.robot.trunk_control_idx].tolist(),
                "right_arm_q": evaluator.robot.get_joint_positions()[indices].tolist(),
                "right_eef_position": eef_pos.tolist(), "right_eef_orientation": eef_quat.tolist(),
                "radio_position": radio_pos.tolist(), "radio_orientation": radio_quat.tolist(),
                "held": evaluator.robot._ag_obj_in_hand["right"] is radio,
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(result, flush=True)
            return
        if args.regrasp:
            lower_height = initial_h
            if args.vector:
                lower_target = initial_q.clone()
                lower_target[indices] += th.tensor(args.vector)
                for _ in range(args.steps):
                    _step_target(evaluator, _joint_target_to_action(
                        evaluator.robot, lower_target, close_left=False, close_right=True
                    ), capture_observation=bool(args.video))
                lower_height = float(radio.get_position_orientation()[0][2])
            if args.align_radio_xy:
                radio_pos = radio.get_position_orientation()[0]
                robot_pos, robot_quat = evaluator.robot.get_position_orientation()
                delta_xy = th.tensor(args.align_radio_xy) - radio_pos[:2]
                evaluator.robot.set_position_orientation(
                    robot_pos + th.tensor([delta_xy[0], delta_xy[1], 0.0]), robot_quat
                )
                lower_height = float(radio.get_position_orientation()[0][2])
            evaluator.robot.release_grasp_immediately("right")
            if args.save_seed:
                seed_state = og.sim.dump_state(serialized=True).cpu().numpy()
                seed_metadata = dict(metadata)
                seed_metadata["triggers"] = ["reverse_curriculum_exact_contact"]
                args.save_seed.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(
                    args.save_seed, format_version=np.int32(1),
                    label_source=np.array("privileged_reverse_curriculum_seed"),
                    simulator_state=seed_state, state_size=np.int64(seed_state.size),
                    metadata_json=np.array(json.dumps(seed_metadata, sort_keys=True)),
                )
            target = evaluator.robot.get_joint_positions().clone()
            if args.retreat:
                target[indices[0]] -= args.retreat
                for _ in range(args.retreat_steps):
                    _step_target(evaluator, _joint_target_to_action(
                        evaluator.robot, target, close_left=False, close_right=False
                    ), capture_observation=bool(args.video))
                target = lower_target
            regrasp_step = None
            for step in range(args.steps):
                _step_target(evaluator, _joint_target_to_action(
                    evaluator.robot, target, close_left=False, close_right=True
                ), capture_observation=bool(args.video))
                if evaluator.robot._ag_obj_in_hand["right"] is radio:
                    regrasp_step = step
                    break
            regrasp_height = float(radio.get_position_orientation()[0][2])
            if regrasp_step is not None:
                if args.lift_vector:
                    target = evaluator.robot.get_joint_positions().clone()
                    target[indices] += th.tensor(args.lift_vector)
                elif args.vector:
                    target = initial_q
                else:
                    target[indices[0]] -= abs(args.delta)
                for _ in range(args.steps):
                    _step_target(evaluator, _joint_target_to_action(
                        evaluator.robot, target, close_left=False, close_right=True
                    ), capture_observation=bool(args.video))
            final_h = float(radio.get_position_orientation()[0][2])
            results.append({"regrasp_step": regrasp_step, "initial_height": initial_h,
                            "lower_height": lower_height,
                            "retreat": args.retreat,
                            "regrasp_height": regrasp_height, "final_height": final_h,
                            "height_delta_after_regrasp": final_h - regrasp_height,
                            "held": evaluator.robot._ag_obj_in_hand["right"] is radio})
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"snapshot": str(args.start_snapshot), "results": results}, indent=2) + "\n")
            print(results[-1], flush=True)
            return
        candidates = ([(i, d) for i in range(len(indices)) for d in (-args.delta, args.delta)]
                      if args.sweep else [(args.joint, args.delta)])
        for candidate_index, (joint_index, delta) in enumerate(candidates):
            if candidate_index:
                og.sim.load_state(pristine_state, serialized=True)
                og.sim.step_physics()
            name, idx = right_names[joint_index], indices[joint_index]
            target = evaluator.robot.get_joint_positions().clone()
            if args.vector:
                target[indices] += th.tensor(args.vector)
                name, delta = "right_arm_vector", args.vector
            else:
                target[idx] += delta
            max_h = initial_h
            for _ in range(args.steps):
                _step_target(evaluator, _joint_target_to_action(
                    evaluator.robot, target, close_left=False, close_right=True
                ), capture_observation=bool(args.video))
                max_h = max(max_h, float(radio.get_position_orientation()[0][2]))
            final_h = float(radio.get_position_orientation()[0][2])
            results.append({"joint": name, "joint_index": joint_index, "delta": delta,
                            "initial_height": initial_h, "final_height": final_h,
                            "height_delta": final_h - initial_h, "max_height": max_h,
                            "held": evaluator.robot._ag_obj_in_hand["right"] is radio})
            # OmniGibson shutdown terminates this process in some headless builds.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"snapshot": str(args.start_snapshot), "results": results}, indent=2) + "\n")
            if not args.sweep and results[-1]["held"]:
                np.savez_compressed(args.output.with_suffix(".npz"),
                                    simulator_state=og.sim.dump_state(serialized=True).cpu().numpy())
            print(results[-1], flush=True)


if __name__ == "__main__":
    main()
