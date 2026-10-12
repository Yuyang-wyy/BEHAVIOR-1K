# BEHAVIOR-1K 2026 Challenge submission: Comet pi0.5 fine-tune with per-task checkpoint routing

**Self-reported:** mean Q-score 0.1796 over 100 tasks (public instances 0-9, one rollout each, default 1.5x human
timeouts), full-task success rate 3.1 % (31/1000), 77 of 100 tasks with non-zero Q, mean normalized time 0.673.

## Policy
* Base: Comet (2025 challenge, NVIDIA) pi0.5 pt50 checkpoint, openpi fork `mli0603/openpi-comet` @ 4bb2aa7.
* Fine-tune `ft40k`: 40k steps on the 2026 challenge demos (all 100 tasks), batch 192, peak LR 2.5e-5 cosine, EMA 0.999,
  action horizon 32, receding-horizon control (max_len 32), task-sentence prompt (50 % skill-sentence prompts in training).
* Per-task routing: 95 tasks use `ft40k`; 5 tasks (hiding_Easter_eggs, picking_up_trash, picking_up_toys,
  spraying_for_bugs, sorting_household_items) use the zero-shot pt50 checkpoint, chosen on dev instance 311 where the
  fine-tune had lost them. Routing is a per-task `--policy.dir` choice when the server is started for that task.
* No test-time supervision, planners, or scripted behaviours.

## Inputs
RGB + depth + proprioception only, via `omnigibson.eval.wrappers.RGBDFullResWrapper` (unmodified) and the default
`omnigibson/eval/r1pro.yaml`. Evaluator patch: result JSONs carry an extra `goal_history` field (satisfied / total
goal conditions per step, logging only).

## Package contents
* `code/openpi-comet.patch` + `code/websocket_b1k_server.py`: policy server diff over the base commit; `serve_comet.sh`.
* `checkpoints/`: links to `ft40k` export and the zero-shot pt50 checkpoint (openpi format).
* `results/<task>/json/*.json`: 1000 rollout JSONs (q_score, time, agent_distance, success, steps).
* `videos/<task>/<task>_<instance>_0.mp4`: head + wrist video for every rollout.
* `summary.json`: per-task x instance Q and the mean.
* `routing.txt`: the 5 zero-shot tasks.

## Reproduction
`POLICY_DIR=<ckpt> bash serve_comet.sh <task> 8000 0` then
`python -m omnigibson.eval.eval --task-name <task> --robot-config omnigibson/eval/r1pro.yaml --mode public_test
 --instance-indices 0 1 2 3 4 5 6 7 8 9 --env-wrapper omnigibson.eval.wrappers.RGBDFullResWrapper --write-video`.
