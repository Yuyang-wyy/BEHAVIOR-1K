# 35 · Attach a Camera to a Tripod

Task name `attach_a_camera_to_a_tripod`, task index 35.

> Attach the digital camera to the camera tripod in the bedroom.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, bedroom_1, bedroom_2 |
| human demo length | 130.4 s mean (3911 steps) |
| episode time limit | 195.6 s (5867 steps at 30 Hz) |
| human base travel | 11.3036 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060393 |

## Planner notes

**Tier:** C — one floor pick plus an `attached` alignment on the tripod head within 5 cm and 15°, including yaw. Single literal, so the score is 0 or 1.

### Goal in plain words

The digital camera must be attached to the camera tripod in bedroom_0. There is one camera and one tripod. Nothing else is checked, and the tripod may stand anywhere.

### Q traps

- One literal: Q is 0 or 1.
- Attachment is automatic while the camera touches the tripod and the camera's `cameratripodM` link is within 5 cm and 15° of the tripod's `cameratripodF` link (PREDICATES §10). No release needed; success ends the episode.
- Meta links verified in asset metadata: tripod `hnpofr` has `cameratripodF` at its top (local z +0.48 above the root, identity orientation). Camera `zcnxuz` has `cameratripodM` near its base, rotated ~90° about z in the camera frame. So the camera must sit upright on the head **and** at one specific yaw relative to the tripod; a camera rotated 90° or 180° on the head does not latch (derived from the link orientations).
- The tripod root is at z 0.8 m and upright (roll and pitch ~0) in all 20 instances, with random yaw. The mount point is therefore at about 1.28 m (derived).
- Knocking the tripod over moves its mount; re-standing it costs a pick and place.
- The camera also has a `togglebutton`; pressing it is harmless for this goal.
- All three closed-loop runs on 311 scored 0.

### Minimal plan

1. `move to the digital camera` — camera on the floor in view. ~19 s.
2. `pick up the digital camera from the floors` — camera lifted off the floor. ~35 s (the slowest step: floor-level grasp).
3. `move to the camera tripod` — tripod head at chest height, centred. ~19 s.
4. `hold the camera tripod` — second gripper closed on a tripod leg or shaft. ~14 s.
5. `attach the digital camera to the camera tripod` — camera sitting on the tripod head; done when it stays there after the camera gripper opens. ~14 s.
6. `release the camera tripod` — only if the episode has not already ended. ~9 s.

Budget: 196 s limit vs 130 s demo mean. Room for one retry of step 5.

### What the demos do differently

- 167 of 200 demos follow exactly the plan above.
- 30 demos also pick up and re-place the tripod (`pick up the camera tripod from the floors`, `place the camera tripod on the floors`), apparently to bring it closer. Not needed unless the tripod stands against furniture.
- Humans always brace the tripod with the second arm before attaching.

### Hard parts and hacks

- Floor pick of a small camera: the trunk must bend low (35 s mean even for humans).
- The yaw constraint: the camera must face the tripod's own "forward". The tripod's yaw varies across instances and is hard to read from RGB. The VLA must learn it from the demo appearance of a mounted camera.
- Pushing the camera down on the head can tip the tripod; holding it is the demo remedy.
- Camera and tripod widths vs the 44 mm span are unknown (no custom list). The demos grasped both.
- Scripted shortcut (unverified): once the camera rests on the head, a slow wrist yaw sweep over ±180° while keeping contact passes through the 15° window and latches the moment it aligns.

### Hints for the VLM

- Everything is in bedroom_0: one camera on the floor, one tripod standing on the floor, 0.6-2.7 m from the start. No distractors of either category.
- The tripod head (mount) is at about 1.3 m, the top of the tripod.
- Done: the camera sits on top of the tripod and stays there with both grippers open.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(attached digital_camera.n.01_1 camera_tripod.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (attached ?digital_camera.n.01_1 ?camera_tripod.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `digital_camera.n.01_1` | digital_camera_87 | digital_camera / zcnxuz | bedroom_0 | floor, z 0.04 | 1.13 m (range 0.61-2.35) | yes, spread 3.38 m |
| `camera_tripod.n.01_1` | camera_tripod_86 | camera_tripod / hnpofr | bedroom_0 | table/counter (0.6-1.1 m), z 0.8 | 1.3 m (range 0.81-2.68) | yes, spread 2.91 m |
| `floor.n.01_1` | floors_nlswvt_0 | floors / nlswvt | bedroom_0 | floor, z -0.15 | 0.67 m (range 0.23-1.67) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop camera_tripod.n.01_1 floor.n.01_1)
(ontop digital_camera.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching camera_tripod.n.01_1 floor.n.01_1)
(touching digital_camera.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 camera_tripod.n.01_1)
(touching floor.n.01_1 digital_camera.n.01_1)
```

## What the human demos did

200 annotated demos. Length 123.8 s (range 61.7-223.23). Skills per demo 6.0 (range 5-9). 4 distinct skill orders; the most common one covers 84% of demos.

Most common skill counts per demo (84% of demos): move to x2, attach x1, hold x1, pick up from x1, release x1.

Representative demo `episode_00352460.json` (117.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the digital camera` (0.0-20.4 s)
2. `pick up the digital camera from the floors` (20.4-62.1 s)
3. `move to the camera tripod` (62.1-73.8 s)
4. `hold the camera tripod` (73.8-86.6 s)
5. `attach the digital camera to the camera tripod` (86.6-108.6 s)
6. `release the camera tripod` (108.6-117.6 s)

Mean duration per skill in this task: attach 14.2 s, hold 13.7 s, move to 19.1 s, pick up from 35.3 s, place on 12.5 s, release 9.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the camera tripod` | 224 |
| `move to the digital camera` | 201 |
| `pick up the digital camera from the floors` | 200 |
| `attach the digital camera to the camera tripod` | 200 |
| `hold the camera tripod` | 199 |
| `release the camera tripod` | 197 |
| `pick up the camera tripod from the floors` | 30 |
| `place the camera tripod on the floors` | 30 |
| `release the digital camera` | 2 |
| `hold the digital camera` | 1 |
| `release the floors` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/35_attach_a_camera_to_a_tripod.json`. Planner notes: `task_docs/notes/35_attach_a_camera_to_a_tripod.md`.
