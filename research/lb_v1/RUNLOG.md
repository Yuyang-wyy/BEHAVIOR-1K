# Leaderboard run lb_v1 — official eval, instances 0-9 (ids 301-310), 1 rollout each, 1.5x human timeout, videos on

Started 2026-10-06 ~16:30 PDT. Deadline Oct 16 23:59 AoE. Policy frozen for this run; a later run may replace it
(latest valid submission counts).

## Policy = Comet pi0.5, per-task checkpoint routing (no supervisor, no reflexes)
* ft40k (`exports/step-00040000`, Comet pt50 fine-tuned 40k steps on the 2026 demos, 50% skill prompts) on 95 tasks.
* zero-shot Comet pt50 (`openpi_comet/pi05-b1kpt50-cs32`, sulab1 only) on the 5 tasks the fine-tune forgot
  (instance 311, n=1: zs vs ft): hiding_Easter_eggs 1.0/0, picking_up_trash 1.0/0, picking_up_toys 0.83/0,
  spraying_for_bugs 0.5/0, sorting_household_items 0.5/0. Smaller zs>ft gaps (< 0.3) were treated as n=1 noise.
* Prompt: task sentence. Wrapper: RGBDFullResWrapper (RGB + depth + proprio). Seed: evaluator default.
* Expected from the instance-311 map: ~0.22 mean Q (current board: 0.322, 0.211, 0.127, 0.099 self-reported).

## Machines / lists (local_eval/lb/tasks_*.txt, balanced by 1.5x human steps; sulab1 ~2.5x slower)
* local 4090: 35 ft tasks (~74 h) | remote 4090: 35 ft tasks (~74 h) | sulab1 (TITAN RTX sim + 2080Ti policy): 5 zs + 25 short ft (~70 h)
* Sweep: `lb/sweep_lb.sh` (resume-safe: skips tasks with 10 JSONs, `--resume-results` per instance; 14 h timeout/task).
* Remote evaluator carries the other session's uncommitted collection features; all gated to train mode, public_test
  path unchanged (checked 2026-10-06). All three evaluators log `goal_history` into each result JSON.

## Recording for supervision research
* Every result JSON has `goal_history`: [satisfied, total] goal literals after every env step -> literal-flip timeline
  per episode without the harness.
* Head + wrist videos for all 1000 episodes (submission requirement) -> replayable failure evidence.
* After the run: per-task x instance Q table, tasks ranked by (Comet near 0 but one cheap literal) and by
  (partial progress that stalls = reflex candidates), written to task_docs/supervision/lb_v1_map.md.

## Timeline
- 2026-10-06 16:34:58 launched on local/remote/sulab1
- 2026-10-06 17:27 first result: local assembling_gift_baskets 301 Q 0.4375, 39091 steps (= 1.5x human), ~50 min incl. sim
  start; goal_history has one entry per step; video 109 MB (-> ~60-110 GB per 1000 episodes; remote had 148 GB free).
- 2026-10-06 17:30 sulab1: all 27 tasks tried so far SERVE_FAILED - policy server OOM on the 2080Ti (GPU 1): a leftover
  process from the Oct 2 harness runs held ~7.6 GB. Nothing recorded as done, so the list simply re-runs. Fixed by killing
  the holder and relaunching.
- 2026-10-06 17:32 sulab1 relaunched. Second failure cause: sulab1's older `eval.py` has no `--resume-results`; its
  sweep copy runs with RESUME_ARGS="" (task-level skip only; an interrupted task re-runs all 10 instances there).
  sulab1's evaluator is older than local/remote (no seed arg); results assumed protocol-equivalent (instance-311 Q
  matched local on sorting_vegetables earlier) - compare an overlap task if time allows.
