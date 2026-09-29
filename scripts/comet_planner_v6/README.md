# Comet planner harness

Run BEHAVIOR episodes with the Comet pi0.5 checkpoint while a planner switches
the language prompt between skills. Built for the A/B "task sentence vs. skill
sentences" study and for testing whether re-prompting recovers failures.

## What is identical to the official eval

- Episodes are stepped by `omnigibson.eval.evaluator.Evaluator.step()` with the stock
  websocket client. Physics, the 1.5x-human time limit, `RGBDFullResWrapper`, metrics
  and the video are the same code as `python -m omnigibson.eval.eval`.
- `result.json` has the official fields (`q_score`, `success`, `steps`, ...). A copy
  sits in `json/` so existing result tooling can read it.
- Default seed is 0, as in the official eval. Instance indices are public-test
  indices (0-9 leaderboard, 10-19 dev; index 10 = instance 311).
- An interactive episode that ends with `end` keeps the last prompt running until the
  time limit, so its Q is comparable. `end --stop` scores early and is not.

Verified on make_rose_centerpieces instance 311: the harness's goal tracker gives
the same Q as the official metric in all runs.

## The one change on the policy side

`openpi-comet/src/openpi/shared/eval_b1k_wrapper.py` accepts an optional `_prompt`
key in each observation. A new value replaces the prompt and clears the queued
action chunk, so it takes effect on the next step. An empty value restores the task
sentence. Without the key the server behaves exactly as before. The patch is
installed on all three machines. The unpatched original is kept next to it as
`eval_b1k_wrapper.py.pre_planner` (remotes) and in the session scratchpad (local).

## Files

| file | role |
| --- | --- |
| `planner_episode.py` | runs one episode; plan mode (`--plan`) or interactive (file commands) |
| `planner_client.py` | sends one interactive command and prints the reply |
| `planner_session.sh` | starts the Comet server (if none on the port) plus one episode |
| `run_batch.sh` | runs a job list back to back; restarts the server when the task changes; resumable |
| `summarize_sessions.py` | score, prompt segments, and when each goal literal flipped |

## Supervised mode (default for interactive sessions)

The global task sentence drives the robot. Every command runs one checkpoint of
`--check-every` steps (default 150 = 5 s simulated), then the simulator stays paused
until the next command. At each checkpoint the planner reads the panel and chooses:

| command | effect |
| --- | --- |
| `continue` | keep the current prompt and Comet's queued actions for one more checkpoint |
| `global` | switch back to the task sentence |
| `skill "<sentence>"` | switch to a skill sentence (queue cleared, takes effect next step) |
| `base --forward F --left L --turn DEG` | planner drives the base in the robot frame; arms and trunk held at their current joints, jaws keep their last command |
| `grip --arm left\|right [--open]` | planner closes (or opens) one jaw for 1.5 s; arms, trunk and base held still |
| `look [--step-deg 45 --count 8 --no-return]` | turn in place, one head image per stop, plus a labelled mosaic; returns to the start heading by default |

Arm micro-control and development tools (Show-Harness style; robot frozen between commands):

| command | effect |
| --- | --- |
| `hand --arm A --forward F --left L --up U [--yaw D --pitch D] [--no-trunk]` | move one end effector by a delta in the robot base frame, via damped differential IK on the robot's own kinematics, following 1 cm waypoints with orientation weighted 0.3. The trunk is used by default. Use `--no-trunk` when the other hand holds something: bending the trunk moves both arms and dropped the bin once |
| `point --cam C --u X --v Y` | back-project pixel (X, Y) of camera C (native resolution; use the `*_grid.png` images to read coordinates) to a base-frame point from depth, fixed intrinsics and `cam_rel_poses`. It takes the nearest depth in a 9x9 window |
| `reach --arm A --cam C --u X --v Y --above H` | point, then move the hand to H metres above that point |
| `grip --arm A [--open]` | close or open one jaw while everything else holds still |
| `save NAME` / `load NAME or path.pt` | snapshot the full simulator state, step count and gripper commands to `<session>/snapshots/NAME.pt`. It can be loaded into any later session of the same task instance |
| `objinfo`, `fingers` | privileged, for development and bench scoring only: object AABB centres with goal status, and finger link positions |

Each checkpoint reply also carries `monitor` (seconds each arm has hovered open and still, base idle time, time since the last jaw event) and `wrist_center_depth_m`.

`bench_branches.py SESSION SNAPSHOT.pt BRANCHES.json --repeats N --out results.json` replays alternative recoveries from
one snapshot and scores them from simulator state. It is for development only.

Measured on picking_up_trash instance 314, a hover stall with a can lying on its side and the bin held in the right hand:

| branch | can lifted | can in bin |
| --- | --- | --- |
| global prompt, 10 s | 3/4 | 1/4 |
| pick-skill prompt, 10 s | 3/4 | 1/4 |
| micro grasp, then the place prompt (about 12 s) | 4/4 | 3/4 |

Pointing error from the head camera was about 1 cm horizontally and about 4 cm in height, because the point lands on the top surface.
A micro *place* into a held bin failed. The arm alone cannot cross the robot's midline far enough, and pointing through a tilted mouth hits the floor behind it.

Add `--why "<reason>"` to any command; decisions are logged to `trace.jsonl`.
After a base move Comet's action queue is cleared so it re-plans from the new pose.

Base moves use body-velocity odometry from proprioception, which is legal at eval.
Yaw is corrected by factors measured against ground truth (0.82 counter-clockwise,
0.92 clockwise). After correction, turns land within about 5 deg and translations
within about 2.5 cm. There is no obstacle check: a blocked move stops after 3 s
without progress and reports `blocked`. The trace also logs the privileged true
displacement for each move, for checking.

## Plans

```json
{"name": "rose_skills_v1",
 "segments": [
   {"prompt": "move to the rose", "steps": 450, "until": ["base_stopped"]},
   {"prompt": "pick up the rose from the bottom cabinet", "steps": 600, "until": ["grasp_any"]},
   {"prompt": "place the rose in the vase", "steps": 450, "until": ["release_any"]}
 ],
 "tail": "task"}
```

- `prompt`: copy skill sentences from the task page (`task_docs/tasks/NN_<task>.md`,
  "Most frequent skill sentences"). `null` or `""` means the task sentence.
- `until` events come from proprioception only, so they are challenge-legal:
  - `grasp_left`, `grasp_right`, `grasp_any`: the jaw has closed. Thin items such as
    rose stems read as fully closed, so this cannot tell a hold from a miss.
  - `release_*`: the jaw reopened after a closure.
  - `base_stopped`: the base stopped after moving during this segment. `base_moving` is also available.
  - `success`: the episode ended in success.
  - `literal_change` is privileged and needs `--show-goal-status`.
- `tail`: `task` finishes with the task sentence (default). `last` keeps the last
  prompt. `stop` ends early, which is not comparable to the official eval.
- `{"segments": [], "tail": "task"}` is the plain task-sentence baseline, plus logging.

## Running

Local 4090 and cse110-198-106 (same paths):

```bash
B=/home/ywang/Behavior/BEHAVIOR-1K/scripts/comet_planner
# one plan episode
bash $B/planner_session.sh start make_rose_centerpieces 10 ~/Behavior/planner_runs/my_run 8000 \
     --plan ~/Behavior/planner_runs/plans/make_rose_centerpieces_skills.json
# a batch: lines of "TASK INSTANCE_INDEX PLAN_JSON TAG"
bash $B/run_batch.sh jobs.txt ~/Behavior/planner_runs/ab_v1 8000
python3 $B/summarize_sessions.py --table ~/Behavior/planner_runs/ab_v1/*__*
```

sulab1 (policy on the 2080 Ti, simulator on the TITAN RTX):

```bash
LOCAL_EVAL=/data/ywang CONDA_SH=/data/ywang/miniconda3/etc/profile.d/conda.sh SIM_GPU=0 POLICY_GPU=1 \
POLICY_DIR=/data/ywang/ckpt/exports/step-00040000 \
bash /data/ywang/BEHAVIOR-1K/scripts/comet_planner/run_batch.sh jobs.txt /data/ywang/planner_runs/ab_v1 8000
```

Interactive, with a planner in the loop:

```bash
bash $B/planner_session.sh start TASK 10 ~/Behavior/planner_runs/live1 8000          # add --show-goal-status for analysis runs
C="python3 $B/planner_client.py ~/Behavior/planner_runs/live1"
$C run "move to the rose" --steps 450 --until base_stopped   # reply: steps, reason, jaws, events, image paths
$C observe                                                   # head + wrist PNGs and a panel
$C run --task-prompt --steps 600
$C end                                                       # runs out the clock with the last prompt
```

Each command's reply lists `images.panel`, a composite of both wrists and the head
camera at that moment. That image is what the planner should judge.

## Outputs per session

- `result.json`: the official metrics, plus `harness.segments`, `harness.commands` and
  `harness.goal_final` (privileged per-literal status).
- `trace.jsonl`: every 30 steps, the prompt, proprio and partial Q, plus any literals
  that changed. Literal flips come from here.
- `images/`: start image and one set per segment. `<task>_<inst>_0.mp4` is the eval video.

## Cost

About 15 simulator steps per second on a 4090, so wall time is about 2x simulated
time. A rose episode takes about 8 minutes; long tasks take up to about 45.
