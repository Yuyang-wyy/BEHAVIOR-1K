# Submission checklist (rules: behavior.stanford.edu/challenge/evaluation.html; portal: leaderboard space /submit)

Ranking = mean Q over 100 tasks x instances 0-9, 1 rollout each. Latest valid final submission per team counts.

| Required item | Where it is / what to do | Status |
| --- | --- | --- |
| Policy server code (websocket endpoint) | `local_eval/openpi-comet` = mli0603/openpi-comet @ 4bb2aa7 + our diff (`research/lb_v1/openpi-comet_lb_v1.patch`: serve_b1k.py, b1k_policy.py, eval_b1k_wrapper.py, config.py, task_mapping.json, pi0_pytorch.py). Push to a public fork/branch or attach as a stable link. | patch snapshotted |
| Checkpoints | ft40k export (`exports/step-00040000`) for 95 tasks; Comet pt50 zero-shot (`pi05-b1kpt50-cs32`) for 5 tasks. Per-task routing table = `research/lb_v1/zs_tasks.txt`. Upload both to a stable location (HF / OSS) and document the routing in the server launch. | TODO upload |
| Evaluation wrapper code | `omnigibson.eval.wrappers.RGBDFullResWrapper` (upstream BEHAVIOR-1K; RGB + depth + proprio only). Our evaluator patch only adds `goal_history` logging. | ok |
| Robot config | default `omnigibson/eval/r1pro.yaml` (unmodified). | ok |
| Rollout result JSONs | `eval_out/lb_v1/<task>/json/*.json` on local + remote + sulab1 -> gather into one dir (`pull_lb.sh` + local). 1000 files. | running |
| MP4 videos (head + wrist) | `eval_out/lb_v1/<task>/videos/*.mp4` on each machine, ~60-110 GB total -> stable link (OSS bucket / Drive). | running |
| Self-reported Q + full SR | from `lb_map.py` over all 1000 JSONs. | after run |
| Team/affiliation/method text | TBD by user. Method: "Comet pi0.5 fine-tuned on 2026 demos, per-task checkpoint routing". | TODO user |

Timeline: results ~Oct 9-10 -> upload videos (plan 1 day) -> submit by Oct 11 as the safety entry -> any improved policy
needs its own full 1000-episode run (3.5 days) finished before Oct 16 23:59 AoE.
