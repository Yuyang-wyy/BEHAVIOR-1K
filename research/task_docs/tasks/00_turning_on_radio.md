# 00 · Turning On Radio

Task name `turning_on_radio`, task index 0.

> Turn on the radio receiver that's on the table in the living room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 71.7 s mean (2149 steps) |
| episode time limit | 107.5 s (3224 steps at 30 Hz) |
| human base travel | 5.6955 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00; ft10k@sulab1 Q=0.00; ft24k_local@local Q=0.00; smoke@sulab1 Q=0.00 |
| demo video | https://player.vimeo.com/video/1109198872 |

## Planner notes

**Tier:** A. The goal is a single `toggled_on`; a fingertip press on the radio's control is enough, no grasp needed.

### Goal in plain words

The one radio (`radio_89`, asset `radio/wxnicr`) on the living-room coffee table must end toggled on.
Nothing else is checked: the radio may stay on the table, be moved, or end anywhere.
There is only one radio and one coffee table in the living room, so there is no object choice.
The episode ends with Q = 1.0 on the first step the radio is on.

### Q traps

- One literal, false at reset in all 20 public instances (`ToggledOn.value = False` in every `-tro_state.json`). Q is 0 or 1; there is no partial credit.
- The toggle fires only when a robot finger link touches the radio **and** overlaps an ~11 mm sphere at the `togglebutton` meta link for exactly 5 consecutive steps (PREDICATES.md §11). Touching the body elsewhere does nothing.
- A second separate 5-step touch would flip it back, but success ends the episode on the first flip, so this cannot bite in practice.
- Knocking the radio over is the real trap. The body is only ~0.138 m deep; a push aimed past the cap surface toppled it on instance 315 (`radio_generalization_20260920/RESULTS.md`). On its side the control face points somewhere unexpected.

### Minimal plan

Option A (recommended, press in place; shorter than the demo):
1. `move to the radio` — done when the radio fills a large part of the head image and the base has stopped. ~18 s.
2. `press the radio` — done when the episode terminates (success ends it). ~10 s per attempt; retry once or twice, then reposition.

Option B (the demo order, in distribution for Comet):
1. `move to the radio` — as above. ~18 s.
2. `pick up the radio from the coffee table` — done when the radio is off the table and a gripper is stopped short of fully closed. ~25 s.
3. `press the radio` — done when the episode terminates. ~10 s.
4. `place the radio on the coffee table` is never needed: the episode already ended at step 3.

- Scripted alternative: `code: press_marker_policy.py` (`BEHAVIOR-1K/scripts/aspire_radio/`). It presses the control in place from RGB-D + proprioception only and scored 7/20 on public 301-320 (4/10 on the leaderboard ids 301-310). Its successes took 323-3000 steps, all under the 3224-step limit.
- Time limit: 107.5 s (3224 steps). Option B at demo pace (~53 s) fits; Option A leaves room for 3-4 press retries.

### What the demos do differently

- All 200 demos do move to, pick up, press, place on, in that order (the one skill order, 100%).
- Picking the radio up is unnecessary. So is putting it back: the evaluator ends the episode at the press.
- The demo press is annotated `coordinated`: one hand holds the radio while the other presses. Comet has therefore mostly seen `press the radio` with the radio held in the air, not resting on the table. Pressing on the table is out of distribution (unverified how much that hurts).
- Comet closed-loop on instance 311: Q = 0.00 for every checkpoint tried (zs_pt50, ft10k, ft24k, ft40k).

### Hard parts and hacks

- Hardest step: hitting an ~11 mm sphere with a fingertip while in contact with the radio. Centimetre-scale aim error decides success.
- Grasping is the dominant failure of grasp-first pipelines ("No visually verified radio grasp"). Whether any part of the radio fits the 44 mm jaw span is unverified; prefer Option A.
- The radio yaw is random across instances (full circle, -166° to +166°), so the control face often points away from the robot. Orbit the coffee table to the face that shows the control before pressing.
- In 7/20 public instances the radio starts more than 90° off the robot's initial heading (305, 306, 311, 313, 316, 318, 319). A rotate-in-place scan is needed before the first `move to`.
- In the scripted runs, the largest failure was never sighting the control face (9 of 20 in the v10 arm), not the press itself. Search and viewpoint matter more than press accuracy.
- Push along the face normal and stop at the cap surface. Driving 12-42 mm past it tipped the radio over.
- Rotation odometry drifts; re-ground the radio visually after every drive instead of trusting a pose from an earlier scan.

### Hints for the VLM

- Scene `house_double_floor_lower`, living room. The robot starts 0.75-2.25 m from the radio.
- The radio is a small red box on the low coffee table (radio root z 0.53 m, table root z 0.36 m; table top height not measured). It is the only radio and the only coffee table in the living room. Other living-room objects: sofa, shelf, wall-mounted TV, fireplace, bottom cabinet, pictures.
- The control is a small raised red cap in the centre of the dark speaker face, ~10 cm above the table. It looks 8-14 mm across in RGB at 0.36-1.4 m.
- If no dark speaker face with a red cap is visible, you are looking at the back or a side: move around the table.
- The cap turns from red to green when the radio is on. You will rarely see it, because the episode ends on success.
- "Done" for step 2 is episode termination, not anything seen in the image.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(toggled_on radio_receiver.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (toggled_on ?radio_receiver.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `radio_receiver.n.01_1` | radio_89 | radio / wxnicr | living_room_0 | low (0.25-0.6 m), z 0.53 | 1.69 m (range 0.75-2.25) | yes, spread 1.4 m |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.63 m (range 1.19-2.01) | no |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.27 m (range 0.75-2.11) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom table.n.02_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop radio_receiver.n.01_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching radio_receiver.n.01_1 table.n.02_1)
(touching table.n.02_1 radio_receiver.n.01_1)
```

## What the human demos did

200 annotated demos. Length 66.23 s (range 31.03-142.0). Skills per demo 4.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x1, pick up from x1, place on x1, press x1.

Representative demo `episode_00001540.json` (66.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the radio` (0.0-17.3 s)
2. `pick up the radio from the coffee table` (17.3-39.8 s)
3. `press the radio` (39.8-50.0 s)
4. `place the radio on the coffee table` (50.0-66.3 s)

Mean duration per skill in this task: move to 17.8 s, pick up from 25.1 s, place on 13.5 s, press 9.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the radio from the coffee table` | 200 |
| `press the radio` | 200 |
| `place the radio on the coffee table` | 200 |
| `move to the radio` | 198 |
| `move to the coffee table` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/00_turning_on_radio.json`. Planner notes: `task_docs/notes/00_turning_on_radio.md`.
