# Submission form draft (portal: https://behavior-1k-2026-challenge-leaderboard.hf.space/submit)

| Field | Value |
| --- | --- |
| Team * | <TEAM NAME - please fill> |
| Team member full names * | <names - please fill> |
| Affiliation * | <affiliation - please fill> |
| Method description * | Comet pi0.5 (2025 challenge checkpoint) fine-tuned for 40k steps on the 2026 demonstrations of all 100 tasks (task-sentence prompt, receding-horizon control, action horizon 32), with per-task checkpoint routing: 5 tasks use the zero-shot Comet checkpoint where the fine-tune regressed. Inputs: RGB, depth, proprioception. No test-time planning or scripted behaviour. Self-reported mean Q 0.1796, full-task success 3.1 %. |
| Policy submission method * | Docker image submission |
| Docker image URI * | ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1 (after build + push) |
| Docker image digest | from `docker inspect` after push |
| Evaluation README URL * | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-results/blob/main/EVALUATION_README.md |
| Self-evaluation results URL * | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-results |
| Video recordings URL * | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-videos |
| Open-source / release URL | https://github.com/Yuyang-wyy/BEHAVIOR-1K/tree/experiment/comet-supervision/research/lb_v1 (optional) |
| Primary contact email * | <your email> |
| Human teleoperation | Not applicable (training data = the official 2026 challenge demonstrations only) |
| Heuristics / RL / Other data | Not applicable |
| Additional comments | Result JSONs carry one extra logging-only field (`goal_history`); videos and all other fields are unmodified evaluator output. Each task is served by one container started with TASK_NAME=<task>. |
| Rules confirmation * | tick |
| Survey confirmation * | tick after completing the Participant Background & Experience Survey (link on the portal) |

Before submitting: make the three HF repos (results, videos, the two checkpoint repos) PUBLIC, and the GHCR package public.
