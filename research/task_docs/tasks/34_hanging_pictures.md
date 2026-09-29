# 34 · Hanging Pictures

Task name `hanging_pictures`, task index 34.

> Pick up the poster from the kitchen countertop and hang it on one of the wall nails in the kitchen.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 79.6 s mean (2387 steps) |
| episode time limit | 119.4 s (3581 steps at 30 Hz) |
| human base travel | 6.6305 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060330 |

## Planner notes

**Tier:** C — one pick plus an `attached` alignment: the poster's top mount must reach the wall nail at ~1.7 m within 5 cm and 15° while touching it. Single literal, so the score is 0 or 1.

### Goal in plain words

The poster must end up attached to a wall nail. The kitchen has exactly one wall nail (`wall_nail_wlnail_1`), so the `exists` is not a real choice. Nothing else is checked; the poster only needs to latch once and stay attached.

### Q traps

- One literal: Q is 0 or 1. No partial credit for carrying the poster to the wall.
- Attachment is automatic (PREDICATES §10). Every step, if the poster is in contact with the nail and the poster's `displaywallM` link is within 5 cm and 15° of the nail's `displaywallF` link, a fixed joint forms. No release is needed, and success ends the episode on that step.
- Meta links verified in asset metadata: poster `dsrcyt` has one `displaywallM` near its top edge (local z +0.40 before scaling); nail `wlnail` has one `displaywallF` rotated ~90° about y in the nail frame. So the poster must hang flat against the wall, upright, top edge at the nail. A poster held face-up or sideways never latches.
- No other `displaywallF` object in the kitchen, so there is no wrong-parent risk here.
- The joint breaks above 5000 N; slamming the poster into the wall after latching could detach it (§10). Back off gently.
- All three closed-loop runs on 311 scored 0.

### Minimal plan

1. `move to the poster` — poster lying on the bar in view. ~13 s.
2. `pick up the poster from the bar` — poster lifted clear of the bar. ~17 s. If it lies flat and ungraspable, `push the poster to the to_the_edge_of bar` first (4 demos).
3. `hand over the poster with the left` — optional; 102 of 200 demos do it, 94 skip it. Use it only if the grasping hand cannot face the wall. ~16 s.
4. `move to the wall nail` — base stopped facing the wall with the nail centred and high in the head camera. ~13 s.
5. `hang the poster on the wall nail` — poster flat on the wall, top edge at the nail; done when the poster stays on the wall after the gripper opens. ~25 s.

Budget: 119 s limit vs 80 s demo mean. There is time for roughly one retry of step 5, not a second full attempt.

### What the demos do differently

- Only four orders exist; the demos are already minimal.
- About half hand the poster to the left arm before walking to the nail.
- A few push the poster to the bar edge before grasping.

### Hard parts and hacks

- The time limit is very tight (1.5x a short demo). Any failed grasp likely ends the episode at Q 0.
- The nail is very high (z ~1.71 m). The trunk must extend up and the arm reach forward; the poster must be rotated to vertical while doing so.
- The 15° orientation window around the nail's mount frame. A VLA can easily press the poster to the wall slightly tilted and never latch. The planner should watch for the poster staying on the wall after release, and if it drops, re-grasp and retry.
- Poster thickness vs the 44 mm span is unknown (no custom list); the demos grasped it every time with this robot.
- Scripted shortcut (unverified): once the poster touches the wall near the nail, small wrist roll/pitch sweeps can bring it inside 15° without further VLA calls.

### Hints for the VLM

- Everything is in kitchen_0. The poster lies on a bar (`bar_egwapq_0`, one of two bars in the kitchen) at about 1.1 m. The robot starts 0.9-7.3 m from it.
- The wall nail is fixed on a kitchen wall at ~1.7 m (appearance unverified); expect it to be small in the head camera. Look for bare wall above head height.
- Done: the poster hangs on the wall by itself with the gripper open and away.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(attached poster.n.01_1 wall_nail.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?wall_nail.n.01 - wall_nail.n.01)
                (attached ?poster.n.01_1 ?wall_nail.n.01)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `poster.n.01_1` | poster_73 | poster / dsrcyt | kitchen_0 | high (1.1-1.6 m), z 1.11 | 2.75 m (range 0.89-7.27) | yes, spread 2.22 m |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 1.82 m (range 1.25-3.86) | no (fixed) |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 2.64 m (range 1.43-7.28) | no (fixed) |
| `wall_nail.n.01_1` | wall_nail_wlnail_1 | wall_nail / wlnail | kitchen_0 | very high (>1.6 m), z 1.71 | 2.77 m (range 1.6-6.97) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom wall_nail.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop poster.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 poster.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching poster.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 74.8 s (range 31.13-277.9). Skills per demo 5.0 (range 4-6). 4 distinct skill orders; the most common one covers 51% of demos.

Most common skill counts per demo (51% of demos): move to x2, hand over x1, hang x1, pick up from x1.

Representative demo `episode_00342050.json` (82.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the poster` (0.0-17.4 s)
2. `pick up the poster from the bar` (17.4-28.9 s)
3. `hand over the poster with the left` (28.9-48.5 s)
4. `move to the wall nail` (48.5-55.5 s)
5. `hang the poster on the wall nail` (55.5-82.0 s)

Mean duration per skill in this task: hand over 15.6 s, hang 24.5 s, move to 13.1 s, pick up from 16.8 s, push to 66.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the poster` | 200 |
| `pick up the poster from the bar` | 200 |
| `hang the poster on the wall nail` | 200 |
| `move to the wall nail` | 199 |
| `hand over the poster with the left` | 103 |
| `push the poster to the to_the_edge_of bar` | 4 |
| `move to the floors` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/34_hanging_pictures.json`. Planner notes: `task_docs/notes/34_hanging_pictures.md`.
