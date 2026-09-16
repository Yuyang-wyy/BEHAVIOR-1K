"""One reset-and-execute trial for a public visual code policy, never action replay."""

from __future__ import annotations

import argparse
import dataclasses
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
        "mode": "train", "task": {"name": "turning_on_radio"}, "robot": OmegaConf.load(robot_config),
    })
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "policy.py").write_text(source)
    payload = {"task": "turning_on_radio", "instance": args.instance, "seed": args.seed,
               "grounding_backend": args.grounding,
               "policy_inputs": ["RGB-D", "camera calibration", "robot proprioception"],
               "demonstration_actions": False, "ground_truth_object_state": False,
               "task_success": False, "status": "infrastructure_error", "blocks": []}
    try:
        with Evaluator(cfg) as evaluator:
            evaluator.reset(seed=args.seed)
            evaluator.load_task_instance(args.instance)
            evaluator.reset(seed=args.seed)
            if args.record_video:
                evaluator.start_recording(str((args.output_dir / "rollout.mp4").resolve()))
                evaluator._write_video()
            harness = VisualRadioHarness(evaluator, args.output_dir, args.sam3_url)
            try:
                for camera in ("head", "right_wrist", "left_wrist"):
                    harness.save_current_observation(f"initial_{camera}", camera)
                if not args.capture_only:
                    executor = PublicPolicyExecutor(harness.functions())
                    payload["blocks"] = [dataclasses.asdict(block) for block in executor.run_source(source)]
                # Evaluator-only score: never injected into policy APIs or observations.
                payload["task_success"] = bool(evaluator.env.task.success)
                payload["steps"] = harness.steps
                payload["terminated"] = bool(harness.terminated)
                payload["truncated"] = bool(harness.truncated)
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
