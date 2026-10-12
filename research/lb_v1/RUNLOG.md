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
- 2026-10-07 00:45 progress 39 episodes, no new failures. Observed wall rates: local 12.0 sim steps/s, remote 15.9,
  sulab1 4.9 (my plan assumed ~25). Projected finish: remote Oct 11 02:00, sulab1 Oct 12 03:00, local Oct 12 12:00.
  Consequence: lb_v1 is the submission; no time for a second full run of a different policy before Oct 16.
  Plan: when remote finishes, stop local's sweep and hand its last tasks to remote (edit lists only at that moment -
  `while read` keeps the old file inode, so in-place edits of a running list do nothing).
  Early per-task numbers (10 instances): picking_up_trash zs 0.50 (3 successes), assembling_gift_baskets 0.44,
  boxing_books 0.15, spraying zs 0.29, canning_food 0.
- 2026-10-07 00:50 killed the stale port-8100 servers (7.8 GB each, idle since Oct 2) on both 4090s. Speed-up check:
  GPU util is only 34-38 % and the eval uses ~10 of 32 cores - the loop is latency-bound (sim step + inference round
  trip). A second evaluator per 4090 is NOT possible: the websocket server keeps ONE shared policy state (reset per
  connection, receding-horizon chunk cache), so two clients would corrupt each other, and a second server + sim needs
  ~14.5 GB more than the 24 GB card has. ETA stands: remote Oct 11, local/sulab1 Oct 12.
- 2026-10-08 13:00 248 episodes / 28 tasks, no failures, running mean 0.197 (long tasks first). hiding_Easter_eggs on
  the zero-shot route: 0.03 over 301-310 (full-length episodes, goal_history shows an egg "hidden" transiently in 4 of
  10 and lost again) - the instance-311 Q 1.0 was a lucky single rollout, as the noise rule predicted. ft40k was 0 at
  311 too, so routing cost nothing. Routed-task means so far: trash 0.50, toys 0.29, spraying 0.25,
  sorting_household 0.23, eggs 0.03 (ft40k had 0 on all five at 311).
- 2026-10-09 01:00 remote HUNG on putting_away_Halloween_decorations instance 306: no result since 17:44 (7 h lost),
  GPU 0 %, evaluator alive and spinning. Killed by PID; the sweep moves on; the task is appended to the remote list so
  its 5 missing instances re-run at the end (`--resume-results`). Added `lb/hang_watch_lb.sh` on all machines: kills the
  evaluator when its task log is idle > 150 min (4090s) / 300 min (sulab1); hangs are logged to logs/lb_v1_hangs.log.
  Progress 350 episodes / 39 tasks, mean 0.185.
- 2026-10-09 07:00 watchdog killed two hung local evaluators: rearrange_your_room (7/10 done, hung at the instance-308
  reset) and tidying_living_room (hung 55 s after start, 0/10). Both logs stop right after the scene-reset warnings
  ("CreateJoint ... disjointed body transforms"). Both tasks appended to the local list for re-run. Watchdog threshold
  lowered to 90 min on the 4090s (max episode ~55 min), 200 min on sulab1. 389 episodes / 44 tasks, mean 0.176.
- 2026-10-10 13:00 local hang #3: polishing_shoes (killed after 96 min idle), requeued. 658 episodes / 71 tasks, mean 0.161.
- 2026-10-10 17:30 failure analysis of 677 episodes written to task_docs/supervision/README.md (commit on the fork).
  Prepared (not started) the post-run supervision test: planner_runs/q_trash_zs.txt = trash v11 reflex on the zero-shot
  checkpoint, instances 301-310, seeds 0/1, plus a seed-1 zero-shot baseline (seed 0 baseline = lb_v1 itself, 0.50).
  Needs exports/zs-pt50 (rsync from sulab1 running) and a free GPU (after Oct 11 night).
- 2026-10-11 19:40 remote SWEEP_DONE (35 tasks + Halloween re-run). 970/1000 at 19:48. Three tasks had ended EARLY with
  partial results (evaluator crash, not hang - the monitor only flagged jsons=0): make_microwave_popcorn 1/10 (sulab1,
  AttributeError 'scroll_y_max' at instance 302), cook_cabbage 2/10 and slicing_vegetables 5/10 (local). Added
  `lb/run_missing.sh` (specific instance indices). Remote now runs popcorn 302-310 + cabbage 303-310; local runs
  slicing 306-310 after its sweep, then starts the trash-reflex test queue (q_trash_zs.txt). sulab1: cook_bacon last.
- 2026-10-11 20:10 crash causes: slicing_vegetables / cook_cabbage die in `_dump_state -> get_joint_positions`
  ('NoneType' has no attribute 'view') at the reset AFTER an episode that created new objects (sliced / cooked
  halves) - an OmniGibson state-dump bug with mid-episode objects; popcorn died on an Omniverse UI error
  (`scroll_y_max`). Re-runs therefore use ONE evaluator process per instance (run_missing.sh spec "task:i;task:j").
- 2026-10-12 00:30 RUN COMPLETE except slicing_vegetables 306-310 (per-instance re-runs on local produced no result;
  retrying on remote). Gathered 995 JSONs into local_eval/eval_out/lb_v1_all (summary.json).
  **FINAL (missing = 0): mean Q 0.1780, full-task SR 3.0 %, 77/100 tasks non-zero.** Top: clean_up_broken_glass 0.63,
  putting_away_toys 0.62, laying_tile_floors 0.61, putting_dirty_dishes_in_sink 0.57, dispose_of_glass 0.55,
  picking_up_trash (zs) 0.50. Videos being pulled from remote/sulab1 to local for the package.
  Trash-reflex test (q_trash_zs) started on local at 20:51.
- 2026-10-12 00:40 slicing 306-310 re-runs on local were killed by hang_watch_lb.sh (it watches the ORIGINAL task log,
  idle since Oct 8). Watchdogs stopped on all machines; slicing re-run moved to remote (no stale log there).
  Trash reflex on zs, seed 0, 301-310: 0.77 / 6 successes vs 0.50 / 3 alone.
