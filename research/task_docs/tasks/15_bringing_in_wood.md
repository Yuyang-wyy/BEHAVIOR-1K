# 15 · Bringing in Wood

Task name `bringing_in_wood`, task index 15.

> Bring the three plywood sheets from the garden into the corridor and place them on the floor there.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | corridor, garden |
| rooms loaded | corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 451.2 s mean (13535 steps) |
| episode time limit | 676.8 s (20303 steps at 30 Hz) |
| human base travel | 36.3806 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114058068 |

## Planner notes

**Tier:** C — three flat plywood boards (0.07 x 0.47 x 0.02 m each) lie flat on the garden floor. The only dimension under 44 mm is the vertical 0.02 m, which a gripper cannot straddle from above. They must be carried 5-15 m through a closed door.

### Goal in plain words

All three plywood boards must rest on the corridor floor.
The boards are interchangeable, and any spot on the corridor floor works.
Nothing has to be closed afterwards.

### Q traps

- 3 literals, all False at reset. Max partial Q is 1.0; each board is worth 1/3.
- `ontop` needs direct contact (PREDICATES §4). A board stacked on another board does not touch the floor and does not score. Lay them side by side.
- The board must rest on the corridor floor (`floors_xorxro_0`), not the garden floor just outside the door. A board resting across the threshold may touch both floors. It scores only if the ray down from its AABB centre hits the corridor floor; place it fully inside.
- The corridor has two `hall_tree` stands. A board leaning on one of them may not touch the floor.
- A board dropped on the way (on the garden floor) scores 0.

### Minimal plan

The corridor-garden door `door_vudhlc_1` starts closed (template joint_pos ~0). Every demo opens it on the first trip. The boards start anywhere in the garden (per-instance spread up to 16 m), 0.7-14 m from the robot.

1. `move to the plywood` — board centred in view on the ground. ~44 s.
2. `pick up the plywood from the floors` — board lifted off the ground; depth shows a gap below it. ~22 s.
3. `move to the door`, `open the door of the door` — door swung open, corridor visible. ~44 s + 56 s.
4. `move to the floors`, `place the plywood on the floors` — board lying on the corridor floor, gripper open. ~44 s + 17 s.
5. Repeat for the other two boards. Carry one per hand: `move to the plywood`, `pick up the plywood from the floors` twice, then `move to the floors` and `place the plywood on the floors` twice. ~44 + 22 + 44 + 22 + 44 + 17 + 17 s.

Budget: about 440 s against a 677 s limit. The two-per-trip second leg matters; three single trips probably do not fit.

### What the demos do differently

- The demos are uniform: all 200 open `door_vudhlc_1`, carry one board first, then two boards together. The order of the three boards varies freely.
- 3-4 demos put a board down on the garden floor and regrasp; that is recovery, not a needed step.
- No push or hand-over is used.

### Hard parts and hacks

- The grasp is the hard part. A board lying flat has 0.07 m width (too wide) and 0.02 m thickness (vertical, finger cannot get under it). A likely working approach is to tilt it first or grasp its end from the side with fingers low; unverified.
- Scripted pushing along the floor is a legal fallback: `ontop floor` only needs the board resting on the corridor floor. It is 5-15 m of pushing through a doorway; no push prompt exists in this task's demos (closest trained verb: `push the <obj> to the <target>` from other tasks).
- The door must stay open between trips. If it swings shut, it blocks the second trip.
- The garden is large (17.6 x 5.3 m floor, 55 bushes, 26 trees). Boards on the lawn can be hard to see; scan low.

### Hints for the VLM

- Plywood boards are thin light-brown planks about half a metre long, lying on the garden ground. There are exactly three, and no other plywood in the scene.
- The target door is between the garden and the corridor. The corridor has two garden doors (`door_vudhlc_0`, `door_vudhlc_1`); the demos use `_1`. Either leads to the same corridor floor.
- The corridor is a long narrow hall (2.6 x 9 m) with two hall trees, a standing mirror and pictures on the walls.
- Done for each board: lying flat on the corridor tiles, clear of the doorway and not on another board.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop plywood.n.01_1 floor.n.01_2)` | no | yes |
| `(ontop plywood.n.01_2 floor.n.01_2)` | no | yes |
| `(ontop plywood.n.01_3 floor.n.01_2)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?plywood.n.01 - plywood.n.01) 
                (ontop ?plywood.n.01 ?floor.n.01_2)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `plywood.n.01_1` | plywood_203 | plywood / fkmkqa | garden_0 | floor, z 0.01 | 5.81 m (range 0.93-13.06) | yes, spread 16.14 m |
| `plywood.n.01_2` | plywood_202 | plywood / fkmkqa | garden_0 | floor, z 0.01 | 3.95 m (range 1.18-14.25) | yes, spread 15.67 m |
| `plywood.n.01_3` | plywood_201 | plywood / fkmkqa | garden_0 | floor, z 0.01 | 4.01 m (range 0.71-14.28) | yes, spread 16.83 m |
| `floor.n.01_1` | floors_qadhjb_0 | floors / qadhjb | garden_0 | floor, z -0.15 | 3.76 m (range 0.5-7.52) | no (fixed) |
| `floor.n.01_2` | floors_xorxro_0 | floors / xorxro | corridor_0 | floor, z -0.15 | 10.37 m (range 5.3-15.23) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 garden)
(inroom floor.n.01_2 corridor)
(ontop agent.n.01_1 floor.n.01_1)
(ontop plywood.n.01_1 floor.n.01_1)
(ontop plywood.n.01_2 floor.n.01_1)
(ontop plywood.n.01_3 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 plywood.n.01_1)
(touching floor.n.01_1 plywood.n.01_2)
(touching floor.n.01_1 plywood.n.01_3)
(touching plywood.n.01_1 floor.n.01_1)
(touching plywood.n.01_2 floor.n.01_1)
(touching plywood.n.01_3 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 450.18 s (range 270.0-578.07). Skills per demo 13.0 (range 13-16). 6 distinct skill orders; the most common one covers 98% of demos.

Most common skill counts per demo (98% of demos): move to x6, pick up from x3, place on x3, open door x1.

Representative demo `episode_00150430.json` (454.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the plywood` (7.3-22.5 s)
2. `pick up the plywood from the floors` (22.5-51.3 s)
3. `move to the door` (54.0-90.5 s)
4. `open the door of the door` (90.6-136.7 s)
5. `move to the floors` (136.7-162.0 s)
6. `place the plywood on the floors` (162.0-185.0 s)
7. `move to the plywood` (188.0-264.2 s)
8. `pick up the plywood from the floors` (264.2-291.8 s)
9. `move to the plywood` (291.8-307.0 s)
10. `pick up the plywood from the floors` (307.0-333.6 s)
11. `move to the plywood` (335.5-415.0 s)
12. `place the plywood on the floors` (415.0-440.7 s)
13. `place the plywood on the floors` (440.7-461.4 s)

Mean duration per skill in this task: move to 43.8 s, open door 55.7 s, pick up from 22.2 s, place on 17.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the plywood` | 605 |
| `pick up the plywood from the floors` | 605 |
| `place the plywood on the floors` | 605 |
| `move to the floors` | 397 |
| `open the door of the door` | 200 |
| `move to the door` | 196 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/15_bringing_in_wood.json`. Planner notes: `task_docs/notes/15_bringing_in_wood.md`.
