# Evaluation README - Comet pi0.5 fine-tune with per-task checkpoint routing (BEHAVIOR-1K 2026 Challenge)

## Summary
Self-reported on public instances 0-9 (ids 301-310), one rollout each, default 1.5x human timeouts:
**mean Q-score 0.1796 over 100 tasks, full-task success 3.1 % (31/1000)**, 77/100 tasks with non-zero Q,
mean normalized time 0.673. Inputs: RGB, depth, proprioception only.

## Policy
* Base model: Comet pi0.5 (NVIDIA, 2025 challenge, `mli0603/openpi-comet` @ 4bb2aa7), checkpoint `pi05-b1kpt50-cs32`.
* `ft40k`: fine-tuned 40k steps on the 2026 challenge demonstrations (all 100 tasks; batch 192, peak LR 2.5e-5
  cosine, EMA 0.999, action horizon 32, 50 % skill-sentence prompts), served with the task sentence prompt,
  receding-horizon control (`--control_mode=receeding_horizon --max_len=32`).
* Per-task routing: 95 tasks use `ft40k`; 5 tasks use the zero-shot pt50 checkpoint
  (`routing_zero_shot_tasks.txt`: hiding_Easter_eggs, picking_up_trash, picking_up_toys, spraying_for_bugs,
  sorting_household_items). The choice is a per-task `--policy.dir` when the server starts for that task.
* No test-time planners, scripted behaviours, or privileged information.

## Docker image
* Image: `<REGISTRY>/b1k-2026-comet:lb_v1` (see `docker/Dockerfile`, `docker/entrypoint.sh`).
* Run (one container per task, the task name selects prompt + checkpoint):
  `docker run --gpus all -e TASK_NAME=<task_name> -p 8000:8000 <REGISTRY>/b1k-2026-comet:lb_v1`
  The server listens on websocket port 8000 (`/healthz` for readiness) and speaks the official
  `omnigibson.eval.utils.network_utils` protocol (metadata on connect, `{"reset": true, "seed": s}`, observation ->
  action chunk).
* Checkpoints: HuggingFace `YuyoungWang/b1k-2026-comet-ft40k` (ft40k export) and
  `YuyoungWang/b1k-2026-comet-zs-pt50` (zero-shot pt50), downloaded at image build time.

## Exact evaluator command (per task; what produced the submitted JSONs and videos)
```
python -m omnigibson.eval.eval --task-name <task_name> \
  --robot-config omnigibson/eval/r1pro.yaml --mode public_test \
  --host 127.0.0.1 --port 8000 --instance-indices 0 1 2 3 4 5 6 7 8 9 \
  --env-wrapper omnigibson.eval.wrappers.RGBDFullResWrapper \
  --output-dir <out>/<task_name> --write-video
```
* Wrapper: `omnigibson.eval.wrappers.RGBDFullResWrapper` (upstream BEHAVIOR-1K, unmodified) -> RGB + depth + proprio.
* Robot config: `OmniGibson/omnigibson/eval/r1pro.yaml` (upstream, unmodified; copy in `robot_config/r1pro.yaml`).
* Evaluator: BEHAVIOR-1K at the challenge release; the only local change is logging-only: each result JSON carries an
  extra `goal_history` field (satisfied/total goal conditions per step), patch in `code/evaluator_goal_history_logging.patch`.
  Result JSON and video files are otherwise unmodified evaluator output.

## Package layout
* `results/<task>/json/<task>_<instance>_0.json` - 1000 rollout metrics JSONs (q_score, time, agent_distance, success, steps)
* `videos/<task>/<task>_<instance>_0.mp4` - 1000 head + wrist rollout videos (hosted separately: see Video recordings URL)
* `summary.json` - per-task x instance Q and the mean; `routing.txt` - the 5 zero-shot tasks
* `code/` - policy server patch over `mli0603/openpi-comet@4bb2aa7`, server module, launch scripts, evaluator logging patch
* `docker/` - Dockerfile + entrypoint
