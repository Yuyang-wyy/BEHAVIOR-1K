"""One reset-and-execute trial for a public visual code policy, never action replay."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import traceback
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path(__file__).with_name("visual_policy.py"))
    parser.add_argument("--instance", type=int, default=26)
    parser.add_argument("--seed", type=int, default=2026091500)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--robot-config", type=Path)
    parser.add_argument("--grasping-mode", choices=("physical", "assisted"))
    parser.add_argument("--mode", choices=("train", "public_test", "hidden_test"), default="train")
    parser.add_argument("--task", default="turning_on_radio",
                        help="BEHAVIOR activity name; the harness itself is task agnostic")
    parser.add_argument("--sam3-url", default="http://127.0.0.1:8114")
    parser.add_argument("--grounding", choices=("sam3", "codex-pixels"), default="sam3")
    parser.add_argument("--max-steps", type=int, default=2500)
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--record-video", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    from omnigibson.eval.aspire.public_policy import PublicPolicyExecutor, validate_policy

    source = args.policy.read_text()
    validate_policy(source)
    import fcntl
    import resource

    trial_lock = open("/tmp/behavior-aspire-radio.lock", "a")
    fcntl.flock(trial_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Initialize external Warp before Isaac Sim loads its bundled version.
    import warp
    import warp.torch  # noqa: F401

    warp.init()
    from omegaconf import OmegaConf
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.aspire.visual_perception import PerceptionUnavailable
    from omnigibson.eval.aspire.visual_radio_harness import VisualRadioHarness
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm

    gm.HEADLESS = True
    seed_everything(args.seed)
    root = Path(__file__).resolve().parents[2]
    robot_config = args.robot_config or root / "OmniGibson/omnigibson/eval/r1pro.yaml"
    cfg = OmegaConf.create({
        "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
        "policy_name": "aspire_visual_code",
        "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
        "headless": True, "partial_scene_load": True, "max_steps": args.max_steps,
        "write_video": args.record_video, "write_side_video": False,
        "mode": args.mode, "task": {"name": args.task}, "robot": OmegaConf.load(robot_config),
    })
    if args.grasping_mode is not None:
        cfg.robot.grasping_mode = args.grasping_mode
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "policy.py").write_text(source)
    OmegaConf.save(cfg, args.output_dir / "config.yaml")
    source_paths = [args.policy, Path(__file__),
                    root / "OmniGibson/omnigibson/eval/aspire/visual_radio_harness.py",
                    root / "OmniGibson/omnigibson/eval/aspire/visual_perception.py",
                    root / "OmniGibson/omnigibson/utils/aspire_kinematics.py"]
    payload = {"task": args.task, "mode": args.mode, "instance": args.instance, "seed": args.seed,
               "grounding_backend": args.grounding,
               "policy_inputs": ["RGB-D", "robot proprioception", "official relative camera calibration",
                                 "static robot finger geometry", "body-velocity odometry"],
               "oracle_robot_localization": False,
               "grasping_mode": cfg.robot.grasping_mode,
               "source_sha256": {str(path.resolve().relative_to(root)):
                                 hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in source_paths if path.resolve().is_relative_to(root)},
               "policy_sha256": hashlib.sha256(source.encode()).hexdigest(),
               "demonstration_actions": False, "ground_truth_object_state": False,
               "task_success": False, "status": "infrastructure_error", "blocks": []}
    try:
        with Evaluator(cfg) as evaluator:
            evaluator.reset(seed=args.seed)
            evaluator.load_task_instance(args.instance)
            evaluator.reset(seed=args.seed)
            payload["grasping_mode"] = evaluator.robot.grasping_mode
            if payload["grasping_mode"] != cfg.robot.grasping_mode:
                raise ValueError("Loaded robot grasping mode differs from the requested configuration")
            if args.record_video:
                evaluator.start_recording(str((args.output_dir / "rollout.mp4").resolve()))
                evaluator._write_video()
            harness = VisualRadioHarness(evaluator, args.output_dir, args.sam3_url)
            # A stalled trial (trace stops, one core busy, GPU idle) has been
            # seen twice with no way to attach a debugger; dump every thread's
            # stack if the trial runs past 15 minutes.
            import faulthandler
            stack_dump = open(args.output_dir / "stack_dump.txt", "w")
            faulthandler.dump_traceback_later(900, repeat=True, file=stack_dump)
            import os
            if os.environ.get("ASPIRE_DEBUG_AABB"):
                # Evaluator-side debugging only: log where the tool and keyboard
                # are and where the dust sits, every few steps, to a file the
                # policy never sees. Enabled only for diagnostic runs.
                from omnigibson.systems.system_base import VisualParticleSystem
                scene = evaluator.env.scene
                tool_obj = next((o for o in scene.objects if "pipe_cleaner" in o.category), None)
                keyboard_obj = next((o for o in scene.objects if o.category == "keyboard"), None)
                debug_file = open(args.output_dir / "debug_aabb.jsonl", "w")
                original_step = harness._step

                def logged_step(action):
                    original_step(action)
                    if harness.steps % 5 or tool_obj is None or keyboard_obj is None:
                        return
                    record = {"step": harness.steps,
                              "tool": [v.tolist() for v in (x.detach().cpu().numpy() for x in tool_obj.aabb)],
                              "tool_visual": [v.tolist() for v in (x.detach().cpu().numpy()
                                                                   for x in tool_obj.root_link.visual_aabb)],
                              "keyboard": [v.tolist() for v in (x.detach().cpu().numpy() for x in keyboard_obj.aabb)]}
                    try:
                        robot = evaluator.env.robots[0]
                        record["eef"] = robot.get_eef_position(arm="right").detach().cpu().numpy().round(4).tolist()
                        record["base"] = robot.get_position_orientation()[0].detach().cpu().numpy().round(4).tolist()
                    except Exception as error:
                        record["robot_error"] = repr(error)[:120]
                    try:
                        from omnigibson.object_states import ModifiedParticles, ParticleRemover, Saturated
                        dust_system = scene.get_system("dust", force_init=False)
                        record["modified"] = int(tool_obj.states[ModifiedParticles].get_value(dust_system))
                        record["saturated"] = bool(tool_obj.states[Saturated].get_value(system=dust_system))
                        record["remover"] = ParticleRemover in tool_obj.states
                    except Exception as error:
                        record["state_error"] = repr(error)[:120]
                    for system in scene.active_systems.values():
                        if isinstance(system, VisualParticleSystem):
                            group = VisualParticleSystem.get_group_name(obj=keyboard_obj)
                            if group in system.groups and system.num_group_particles(group=group):
                                positions = system.get_group_particles_position_orientation(group=group)[0]
                                record["dust"] = positions.detach().cpu().numpy().round(4).tolist()
                    debug_file.write(json.dumps(record) + "\n")
                    debug_file.flush()

                harness._step = logged_step
            try:
                for camera in ("head", "right_wrist", "left_wrist"):
                    harness.save_current_observation(f"initial_{camera}", camera)
                if not args.capture_only:
                    executor = PublicPolicyExecutor(harness.functions())
                    payload["blocks"] = [dataclasses.asdict(block) for block in executor.run_source(source)]
                # Evaluator-only score: never injected into policy APIs or observations.
                payload["task_success"] = bool(evaluator.env.task.success)
                # Evaluator-only debugging aid with the same standing as the
                # score above: which covering particles are left, in each
                # object's own frame. Written after the policy has finished and
                # never passed to any policy API.
                try:
                    from omnigibson.systems.system_base import VisualParticleSystem
                    remaining = {}
                    scene = evaluator.env.scene
                    for system in scene.active_systems.values():
                        if not isinstance(system, VisualParticleSystem):
                            continue
                        for obj in scene.objects:
                            group = VisualParticleSystem.get_group_name(obj=obj)
                            if group not in system.groups:
                                continue
                            count = int(system.num_group_particles(group=group))
                            local = system.get_group_particles_local_pose(group=group)[0] if count else []
                            remaining[f"{system.name}@{obj.name}"] = {
                                "count": count,
                                "local_positions": [[round(float(v), 4) for v in row] for row in local],
                            }
                    payload["debug_remaining_particles"] = remaining
                except Exception as error:  # diagnostics must never break a trial
                    payload["debug_remaining_particles"] = f"unavailable: {error!r}"
                payload["steps"] = harness.steps
                payload["terminated"] = bool(harness.terminated)
                payload["truncated"] = bool(harness.truncated)
                metrics = {}
                for metric in evaluator.metrics:
                    metrics.update(metric.aggregate(evaluator.env))
                payload.update(metrics)
                errors = "\n".join(block["stderr"] for block in payload["blocks"])
                if args.capture_only:
                    payload["status"] = "capture_only"
                elif payload["task_success"]:
                    payload["status"] = "success"
                elif PerceptionUnavailable.__name__ in errors:
                    payload["status"] = "perception_unavailable"
                else:
                    payload["status"] = "policy_failed"
            finally:
                if args.record_video:
                    evaluator.stop_recording()
                (args.output_dir / "result.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    except Exception:
        payload["error"] = traceback.format_exc()
        (args.output_dir / "result.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
        raise
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
