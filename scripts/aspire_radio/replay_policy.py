"""Replay one ASPIRE-style radio policy in the current BEHAVIOR simulator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from omegaconf import OmegaConf

from omnigibson.eval.aspire.code_policy_executor import AspireCodePolicyExecutor
from omnigibson.eval.aspire.radio_harness import RadioHarness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path(__file__).with_name("policy.py"))
    parser.add_argument("--instance", type=int, default=26)
    parser.add_argument("--seed", type=int, default=2026091500)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--robot-config", type=Path, default=Path("omnigibson/eval/r1pro.yaml"))
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--record-video", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--replay-reference", action="store_true")
    parser.add_argument("--demo-root", type=Path, default=Path("../data/2026-challenge-demos"))
    args = parser.parse_args()

    # CuRobo needs the external Warp runtime initialized before Isaac Sim imports its bundle.
    import warp
    import warp.torch  # noqa: F401

    warp.init()
    import omnigibson as og
    from omnigibson.eval.evaluator import Evaluator
    from omnigibson.eval.utils.eval_utils import seed_everything
    from omnigibson.macros import gm

    gm.HEADLESS = True
    seed_everything(args.seed)
    robot_config = OmegaConf.load(str(args.robot_config.resolve()))
    cfg = OmegaConf.create(
        {
            "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
            "policy_name": "aspire_code",
            "model": {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None},
            "headless": True,
            "partial_scene_load": True,
            "max_steps": args.max_steps,
            "write_video": args.record_video,
            "write_side_video": False,
            "mode": "train",
            "task": {"name": "turning_on_radio"},
            "robot": robot_config,
        }
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with Evaluator(cfg) as evaluator:
        evaluator.reset(seed=args.seed)
        evaluator.load_task_instance(args.instance)
        evaluator.reset(seed=args.seed)
        if args.record_video:
            evaluator.start_recording(str((args.output_dir / "rollout.mp4").resolve()))
        if args.replay_reference:
            import pyarrow.parquet as pq
            import torch as th

            metadata = None
            for path in args.demo_root.resolve().glob("meta/episodes/chunk-*/*.parquet"):
                for row in pq.read_table(path).to_pylist():
                    if row["task_index"] == 0 and row["task_instance_id"] == args.instance:
                        metadata = row
                        break
                if metadata:
                    break
            if metadata is None:
                raise ValueError(f"No radio demonstration for instance {args.instance}")
            path = args.demo_root.resolve() / "data" / f"chunk-{metadata['data/chunk_index']:03d}" / f"file-{metadata['data/file_index']:03d}.parquet"
            actions = pq.read_table(path, columns=["action"]).slice(
                metadata["dataset_from_index"], metadata["dataset_to_index"] - metadata["dataset_from_index"]
            )["action"].to_pylist()
            for action in actions:
                evaluator.env.step(th.tensor(action), n_render_iterations=1, skip_obs=True)
                if args.record_video:
                    evaluator._write_video()
            payload = {"task": "turning_on_radio", "instance": args.instance, "reference_actions": len(actions), "task_success": bool(evaluator.env.task.success)}
            (args.output_dir / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
            print(json.dumps(payload, indent=2))
            if args.record_video:
                evaluator.stop_recording()
            return
        harness = RadioHarness(
            evaluator,
            args.output_dir,
            instance_id=args.instance,
            demo_root=args.demo_root,
            reference_only=True,
        )
        executor = AspireCodePolicyExecutor(harness.functions())
        blocks = executor.run_path(args.policy, observation={"instance": args.instance, "seed": args.seed})
        payload = {
            "task": "turning_on_radio",
            "instance": args.instance,
            "seed": args.seed,
            "policy": str(args.policy.resolve()),
            "task_success": bool(evaluator.env.task.success),
            "blocks": [block.__dict__ for block in blocks],
        }
        (args.output_dir / "result.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
        print(json.dumps(payload, indent=2, default=str))
        if args.record_video:
            evaluator.stop_recording()


if __name__ == "__main__":
    main()
