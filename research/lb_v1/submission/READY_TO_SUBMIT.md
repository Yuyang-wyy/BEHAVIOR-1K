# READY TO SUBMIT - team coco (status file; the DIGEST line is filled in automatically when the image is pushed)

Portal: https://behavior-1k-2026-challenge-leaderboard.hf.space/submit     Deadline: Oct 16 23:59 AoE (= Oct 17 04:59 PDT)
Before the form: Participant Survey https://forms.gle/Y7XYBPqf1UPcFKj59  (and team registration https://forms.gle/Kf4ABLmDKbuK5Yhj6 if not done)

| Form field | Value |
| --- | --- |
| Team | coco |
| Team member full names | Yuyang Wang, Zeyu Lai, Weikang Wan |
| Affiliation | Caltech, UCSD |
| Method description | Comet pi0.5 finetune: the Comet pi0.5 checkpoint (2025 challenge) fine-tuned on the 2026 demonstrations of all 100 tasks (task-sentence prompt, receding-horizon control, action horizon 32); 5 tasks use the zero-shot Comet checkpoint where the fine-tune regressed. Inputs: RGB, depth, proprioception. No test-time planning or scripted behaviour. Self-reported mean Q 0.1796, full-task success 3.1 %. |
| Policy submission method | Docker image submission |
| Docker image URI | ghcr.io/yuyang-wyy/b1k-2026-comet:lb_v1 |
| Docker image digest | ghcr.io/yuyang-wyy/b1k-2026-comet@sha256:714dac05e84097f47f32299505f2aabbbb79e0e856d7fcddaa4c81d0046b34f8 |
| Evaluation README URL | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-results/blob/main/EVALUATION_README.md |
| Self-evaluation results URL | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-results |
| Video recordings URL | https://huggingface.co/datasets/YuyoungWang/b1k-2026-lb_v1-videos |
| Open-source / release URL (optional) | https://github.com/Yuyang-wyy/b1k-2026-submission |
| Primary contact email | ywang10@caltech.edu |
| Human teleoperation / Heuristics / Data from RL / Other data | Not applicable (training data = official 2026 challenge demonstrations only) |
| Additional comments | One container per task: `docker run --gpus all -e TASK_NAME=<task> -p 8000:8000 <image>`; the websocket server listens on 8000 (/healthz). Result JSONs carry one extra logging-only field (goal_history); videos and all other fields are unmodified evaluator output. |
| Checkboxes | rules: tick; survey: tick (after completing it); release-link acknowledgement: tick |

## Verification status (updated automatically)
- HF repos public + anonymously reachable: results (1000 JSONs), videos (1000 mp4), ft40k, zs-pt50 (+ zs-pt50.tar) - OK 2026-10-16 12:52
- Docker image: FINAL = Actions run 4 (Dockerfile with the transformers_replace fix). Build 2 had lacked that post-install step for the PyTorch path; found by the container test, fixed, rebuilt.
- Image pushed to GHCR and anonymously pullable: OK 2026-10-16 13:52:42 digest sha256:714dac05e84097f47f32299505f2aabbbb79e0e856d7fcddaa4c81d0046b34f8
- Container checks: checkpoints present (ft40k 6.8G, zs 12G) OK; tokenizer OK; torch 2.7.1+cu126 + openpi imports OK; routing OK (trash->zs, hot_dogs->ft40k); server start OK for both checkpoints; GPU container (bind-mounted driver, CUDA on RTX 4090) served the official evaluator for a full cook_hot_dogs rollout (instance 301, 13718 steps) - END-TO-END OK 2026-10-16 13:54
- Published image pulled back by digest 714dac05 and checked: transformers_replace present, both checkpoints inside (6.8G + 12G), transformers 4.53.2 - OK 2026-10-16 14:27. ALL CHECKS PASSED.
