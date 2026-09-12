"""Websocket evaluation runner for the BEHAVIOR-1K challenge.

Drives the OmniGibson ``Evaluator`` against a policy served over a websocket
(e.g. the openpi or GR00T ``scripts/b1k/serve_b1k.py`` server). For each test instance of a
task it runs a rollout and writes a per-rollout result JSON compatible with
``omnigibson/eval/utils/score_utils.py`` (``q_score``, ``time``,
``agent_distance`` / ``normalized_agent_distance``).

Example:
    python -m omnigibson.eval.eval \
        --task-name turning_on_radio \
        --robot-config omnigibson/eval/r1pro.yaml \
        --mode public_test \
        --host 127.0.0.1 --port 8000 \
        --instance-indices 0 --max-steps 500 \
        --output-dir outputs/b1k_eval --write-video
"""

import argparse
import json
import logging
import os
from pathlib import Path

from omegaconf import OmegaConf

from omnigibson.eval.diagnostics import MilestoneConfig, PrimitiveMilestoneTracker
from omnigibson.eval.evaluator import Evaluator, resolve_instance_ids
from omnigibson.eval.utils.eval_utils import DEFAULT_EVAL_SEED, seed_everything
from omnigibson.macros import gm
from omnigibson.utils.ui_utils import create_module_logger


logger = create_module_logger(module_name=__name__)
logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-name", required=True, help="BEHAVIOR task name, e.g. turning_on_radio.")
    parser.add_argument("--host", default="127.0.0.1", help="Policy websocket server host.")
    parser.add_argument("--port", type=int, default=8000, help="Policy websocket server port.")
    parser.add_argument(
        "--robot-config",
        type=str,
        default=None,
        help=(
            "Optional path to YAML/JSON file containing one complete robot config dictionary with canonical "
            "'model' and 'name' fields. Add eval.camera_sensor_names to configure eval camera roles."
        ),
    )
    parser.add_argument(
        "--instance-indices",
        type=int,
        nargs="+",
        default=[0],
        help=(
            "Instance indices for the selected mode. For train these are direct train instance IDs; "
            "for public_test / hidden_test these index into that 20-instance split."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("train", "public_test", "hidden_test"),
        default="public_test",
        help="Instance split to evaluate. Default: public_test.",
    )
    parser.add_argument("--num-rollouts", type=int, default=1, help="Rollouts per instance.")
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_EVAL_SEED,
        help="Base simulator and policy seed. Default: %(default)s.",
    )
    parser.add_argument(
        "--rollout-seeds",
        type=int,
        nargs="+",
        default=None,
        help="Optional explicit seeds, one per rollout. The same seed list is used for every instance.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Episode timeout in steps. Default (None) = 1.5x mean human-demo length.",
    )
    parser.add_argument(
        "--env-wrapper",
        default="omnigibson.eval.wrappers.DefaultWrapper",
        help="Target path of the EnvironmentWrapper to apply.",
    )
    parser.add_argument(
        "--camera-resolution",
        type=int,
        default=None,
        help=(
            "Optional square camera render resolution applied before environment creation. "
            "Intended for memory-constrained collection; omit for challenge-protocol evaluation."
        ),
    )
    parser.add_argument(
        "--chunk-boundary-observations",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Collection-only fast path: render and read cameras only when the cached action chunk is exhausted. "
            "Disabled by default and forbidden outside train mode."
        ),
    )
    parser.add_argument(
        "--training-fail-fast",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Collection-only early failure for an exhausted policy retry budget or persistent table displacement. "
            "Disabled by default and forbidden outside train mode."
        ),
    )
    parser.add_argument("--fail-fast-table-displacement", type=float, default=0.03)
    parser.add_argument("--fail-fast-table-patience", type=int, default=2)
    parser.add_argument(
        "--resume-results",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Reuse validated per-rollout JSON files already present in output-dir.",
    )
    parser.add_argument(
        "--policy",
        choices=("websocket", "local"),
        default="websocket",
        help="Policy backend to use. local emits zero actions and is intended for eval smoke tests.",
    )
    parser.add_argument("--output-dir", default="/tmp/b1k_eval", help="Where to write result JSONs.")
    parser.add_argument(
        "--write-video",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Save an MP4 rollout video (head + wrist cameras) per rollout under <output-dir>/videos.",
    )
    parser.add_argument(
        "--write-privileged-training-trace",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Write simulator-grounded radio events at policy decision boundaries for offline critic training. "
            "This is restricted to train mode and is never sent to the policy server."
        ),
    )
    parser.add_argument(
        "--write-training-recovery-snapshots",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Save bounded serialized simulator states at radio grasp/press retries for train-only recovery work. "
            "Requires --write-privileged-training-trace and is never available during challenge evaluation."
        ),
    )
    parser.add_argument(
        "--initial-training-recovery-snapshot",
        default=None,
        help=(
            "Start one train-only radio rollout from a serialized recovery snapshot. "
            "The snapshot identity must match the requested task, instance, rollout, and seed."
        ),
    )
    parser.add_argument(
        "--write-side-video",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Save a second MP4 from a side camera that follows and frames the entire robot.",
    )
    parser.add_argument("--video-fps", type=int, default=30, help="Frame rate for saved rollout videos.")
    parser.add_argument(
        "--diagnostic-milestones",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Write evaluator-only navigation and primitive milestones into each rollout JSON.",
    )
    parser.add_argument(
        "--diagnostic-target-scope",
        help="Exact target key in env.task.object_scope, e.g. vidalia_onion.n.01_1.",
    )
    parser.add_argument(
        "--diagnostic-workspace-scope",
        help="Optional exact workspace key in env.task.object_scope, e.g. sink.n.01_1.",
    )
    parser.add_argument("--diagnostic-approach-m", type=float, default=0.8)
    parser.add_argument("--diagnostic-workspace-m", type=float, default=1.5)
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run OmniGibson headless (default: True).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.diagnostic_milestones and not args.diagnostic_target_scope:
        raise ValueError("--diagnostic-milestones requires --diagnostic-target-scope")

    gm.HEADLESS = args.headless

    if args.num_rollouts < 1:
        raise ValueError("--num-rollouts must be positive.")
    if args.rollout_seeds is not None and len(args.rollout_seeds) != args.num_rollouts:
        raise ValueError(
            f"Expected {args.num_rollouts} --rollout-seeds values, got {len(args.rollout_seeds)}."
        )
    if args.camera_resolution is not None and args.camera_resolution < 1:
        raise ValueError("--camera-resolution must be positive.")
    if (args.chunk_boundary_observations or args.training_fail_fast) and args.mode != "train":
        raise ValueError("Collection fast paths are allowed only with --mode train.")
    if args.write_privileged_training_trace and args.mode != "train":
        raise ValueError("--write-privileged-training-trace is restricted to --mode train.")
    if args.write_privileged_training_trace and args.task_name != "turning_on_radio":
        raise ValueError("Privileged training traces currently support only turning_on_radio.")
    if args.write_training_recovery_snapshots and not args.write_privileged_training_trace:
        raise ValueError("--write-training-recovery-snapshots requires --write-privileged-training-trace.")
    if args.write_training_recovery_snapshots and args.mode != "train":
        raise ValueError("--write-training-recovery-snapshots is restricted to --mode train.")
    if args.initial_training_recovery_snapshot is not None:
        if args.mode != "train" or args.task_name != "turning_on_radio":
            raise ValueError("--initial-training-recovery-snapshot is restricted to train-mode radio rollouts.")
        if len(args.instance_indices) != 1 or args.num_rollouts != 1:
            raise ValueError("A recovery snapshot replay requires exactly one instance and one rollout.")
    if args.chunk_boundary_observations and (args.write_video or args.write_side_video):
        raise ValueError("--chunk-boundary-observations cannot be combined with rollout video output.")
    if args.fail_fast_table_displacement <= 0:
        raise ValueError("--fail-fast-table-displacement must be positive.")
    if args.fail_fast_table_patience < 1:
        raise ValueError("--fail-fast-table-patience must be positive.")
    rollout_seeds = args.rollout_seeds or [args.seed + rollout_id for rollout_id in range(args.num_rollouts)]

    seed = seed_everything(args.seed)
    logger.info(f"Seeded Python, NumPy, and Torch with seed={seed}")
    logger.info(f"Using deterministic rollout seeds: {rollout_seeds}")

    instance_ids = resolve_instance_ids(args.task_name, args.instance_indices, mode=args.mode)
    logger.info(f"Resolved {args.mode} instance ids for {args.task_name}: {instance_ids}")

    robot_config = None
    if args.robot_config is not None:
        robot_config_path = Path(args.robot_config).expanduser()
        robot_config = OmegaConf.load(str(robot_config_path))
        logger.info(f"Loaded robot config from {robot_config_path}")
        if args.camera_resolution is not None:
            for dimension in ("image_height", "image_width"):
                OmegaConf.update(
                    robot_config,
                    f"sensor_config.VisionSensor.sensor_kwargs.{dimension}",
                    args.camera_resolution,
                    merge=True,
                )
            logger.info(f"Overrode initial camera render resolution to {args.camera_resolution}x{args.camera_resolution}")

    if args.policy == "websocket":
        model_cfg = {
            "_target_": "omnigibson.eval.policies.WebsocketPolicy",
            "host": args.host,
            "port": args.port,
        }
    else:
        model_cfg = {"_target_": "omnigibson.eval.policies.LocalPolicy", "action_dim": None}

    cfg = OmegaConf.create(
        {
            "env_wrapper": {"_target_": args.env_wrapper},
            "policy_name": args.policy,
            "model": model_cfg,
            "headless": args.headless,
            "partial_scene_load": True,
            "max_steps": args.max_steps,
            "write_video": args.write_video,
            "write_side_video": args.write_side_video,
            "write_privileged_training_trace": args.write_privileged_training_trace,
            "write_training_recovery_snapshots": args.write_training_recovery_snapshots,
            "initial_training_recovery_snapshot": args.initial_training_recovery_snapshot,
            "chunk_boundary_observations": args.chunk_boundary_observations,
            "training_fail_fast": args.training_fail_fast,
            "fail_fast_table_displacement": args.fail_fast_table_displacement,
            "fail_fast_table_patience": args.fail_fast_table_patience,
            "mode": args.mode,
            "seed": seed,
            "task": {"name": args.task_name},
            "robot": robot_config,
        }
    )

    json_dir = os.path.join(os.path.expanduser(args.output_dir), "json")
    os.makedirs(json_dir, exist_ok=True)
    video_dir = os.path.join(os.path.expanduser(args.output_dir), "videos")
    if args.write_video or args.write_side_video:
        os.makedirs(video_dir, exist_ok=True)
    privileged_trace_dir = os.path.join(os.path.expanduser(args.output_dir), "privileged_training_traces")
    if args.write_privileged_training_trace:
        os.makedirs(privileged_trace_dir, exist_ok=True)
    recovery_snapshot_dir = os.path.join(os.path.expanduser(args.output_dir), "training_recovery_snapshots")
    if args.write_training_recovery_snapshots:
        os.makedirs(recovery_snapshot_dir, exist_ok=True)

    results = []
    with Evaluator(cfg) as evaluator:
        for instance_id in instance_ids:
            try:
                evaluator.reset(seed=seed)
                evaluator.load_task_instance(int(instance_id))
            except Exception:
                logger.exception(f"Failed to load task instance {instance_id}.")
                raise
            for rollout_id in range(args.num_rollouts):
                rollout_seed = rollout_seeds[rollout_id]
                video_path = os.path.join(video_dir, f"{args.task_name}_{instance_id}_{rollout_id}.mp4")
                side_video_path = os.path.join(video_dir, f"{args.task_name}_{instance_id}_{rollout_id}_side.mp4")
                out_path = os.path.join(json_dir, f"{args.task_name}_{instance_id}_{rollout_id}.json")
                if args.resume_results and os.path.isfile(out_path):
                    with open(out_path, "r") as f:
                        existing = json.load(f)
                    identity = {
                        "task": args.task_name,
                        "instance_id": int(instance_id),
                        "rollout_id": rollout_id,
                        "seed": rollout_seed,
                    }
                    mismatches = {
                        key: (existing.get(key), value)
                        for key, value in identity.items()
                        if existing.get(key) != value
                    }
                    if mismatches:
                        raise ValueError(f"Existing rollout result identity mismatch in {out_path}: {mismatches}")
                    logger.info("Resume: reusing completed rollout result %s", out_path)
                    results.append(existing)
                    continue
                try:
                    evaluator.reset(seed=rollout_seed)
                    if args.initial_training_recovery_snapshot is not None:
                        evaluator.load_radio_training_recovery_snapshot(
                            args.initial_training_recovery_snapshot,
                            expected_metadata={
                                "task": args.task_name,
                                "instance_id": int(instance_id),
                                "rollout_id": rollout_id,
                                "seed": rollout_seed,
                                "mode": args.mode,
                            },
                        )
                    diagnostic_tracker = None
                    if args.diagnostic_milestones:
                        diagnostic_tracker = PrimitiveMilestoneTracker(
                            evaluator.env,
                            evaluator.robot,
                            MilestoneConfig(
                                target_scope=args.diagnostic_target_scope,
                                workspace_scope=args.diagnostic_workspace_scope,
                                approach_distance_m=args.diagnostic_approach_m,
                                workspace_distance_m=args.diagnostic_workspace_m,
                            ),
                        )
                        diagnostic_tracker.observe(0)
                    if args.write_privileged_training_trace:
                        evaluator.start_radio_privileged_trace()
                    if args.write_training_recovery_snapshots:
                        evaluator.start_radio_training_recovery_snapshots(
                            os.path.join(
                                recovery_snapshot_dir,
                                f"{args.task_name}_{instance_id}_{rollout_id}_seed-{rollout_seed}",
                            ),
                            metadata={
                                "task": args.task_name,
                                "instance_id": int(instance_id),
                                "rollout_id": rollout_id,
                                "seed": rollout_seed,
                                "mode": args.mode,
                            },
                        )
                    if args.write_video or args.write_side_video:
                        evaluator.start_recording(
                            video_path if args.write_video else None,
                            rate=args.video_fps,
                            side_fpath=side_video_path if args.write_side_video else None,
                        )
                    terminated = truncated = False
                    steps = 0
                    while not (terminated or truncated):
                        terminated, truncated = evaluator.step()
                        steps += 1
                        if diagnostic_tracker is not None:
                            diagnostic_tracker.observe(steps)

                    success = bool(evaluator.env.task.success)
                    metrics = {}
                    for metric in evaluator.metrics:
                        metrics.update(metric.aggregate(evaluator.env))
                    if diagnostic_tracker is not None:
                        metrics["diagnostic_milestones"] = diagnostic_tracker.aggregate()

                    rollout_metadata = {
                        "task": args.task_name,
                        "instance_id": int(instance_id),
                        "rollout_id": rollout_id,
                        "seed": rollout_seed,
                        "mode": args.mode,
                        "early_termination_reason": evaluator.early_termination_reason,
                    }
                    if args.initial_training_recovery_snapshot is not None:
                        rollout_metadata["initial_training_recovery_snapshot"] = os.path.abspath(
                            os.path.expanduser(args.initial_training_recovery_snapshot)
                        )
                    result = {
                        **rollout_metadata,
                        "steps": steps,
                        "success": success,
                        **metrics,
                    }
                    policy_rollout_status = getattr(evaluator.policy, "rollout_status", None)
                    if policy_rollout_status is not None:
                        result["policy_rollout_status"] = policy_rollout_status
                    if args.training_fail_fast or args.chunk_boundary_observations:
                        result["collection"] = evaluator.collection_stats
                    if args.write_privileged_training_trace:
                        privileged_trace_path = evaluator.finish_radio_privileged_trace(
                            os.path.join(
                                privileged_trace_dir,
                                f"{args.task_name}_{instance_id}_{rollout_id}_seed-{rollout_seed}.npz",
                            ),
                            success=success,
                            metadata=rollout_metadata,
                        )
                        result["privileged_training_trace_path"] = privileged_trace_path
                    if args.write_training_recovery_snapshots:
                        result["training_recovery_snapshot_paths"] = (
                            evaluator.finish_radio_training_recovery_snapshots()
                        )
                    replay_path = evaluator.finish_rollout(
                        success=success,
                        metadata=rollout_metadata,
                    )
                    if replay_path is not None:
                        result["replay_path"] = replay_path
                    with open(out_path, "w") as f:
                        json.dump(result, f, indent=2, default=float)
                    q_score = metrics.get("q_score", {}).get("final")
                    video_msg = f" | video -> {video_path}" if args.write_video else ""
                    if args.write_side_video:
                        video_msg += f" | side video -> {side_video_path}"
                    logger.info(
                        f"Result: instance={instance_id} rollout={rollout_id} seed={rollout_seed} steps={steps} "
                        f"success={success} q_score={q_score} -> {out_path}{video_msg}"
                    )
                    results.append(result)
                except Exception:
                    logger.exception(f"Instance {instance_id} rollout {rollout_id} failed.")
                    raise
                finally:
                    if args.write_video or args.write_side_video:
                        evaluator.stop_recording()

        # OmniGibson's shutdown closes the application process from Evaluator.__exit__, so persist
        # the aggregate while the context is still active instead of placing unreachable code
        # after the with block.
        n = len(results)
        n_success = sum(r["success"] for r in results)
        mean_q = (sum(r.get("q_score", {}).get("final", 0.0) for r in results) / n) if n else 0.0
        per_instance = {}
        for instance_id in instance_ids:
            instance_results = [result for result in results if result["instance_id"] == instance_id]
            instance_successes = sum(result["success"] for result in instance_results)
            per_instance[str(instance_id)] = {
                "num_results": len(instance_results),
                "num_successes": instance_successes,
                "success_rate": instance_successes / len(instance_results) if instance_results else 0.0,
                "successful_seeds": [result["seed"] for result in instance_results if result["success"]],
            }
        summary = {
            "task": args.task_name,
            "mode": args.mode,
            "instance_indices": args.instance_indices,
            "instance_ids": instance_ids,
            "num_rollouts": args.num_rollouts,
            "rollout_seeds": rollout_seeds,
            "num_results": n,
            "num_successes": n_success,
            "success_rate": n_success / n if n else 0.0,
            "mean_q_score": mean_q,
            "per_instance": per_instance,
        }
        summary_path = os.path.join(os.path.expanduser(args.output_dir), "summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(
            f"Eval summary: {n_success}/{n} success | mean q_score={mean_q:.3f} | "
            f"task={args.task_name} -> {summary_path}"
        )


if __name__ == "__main__":
    main()
