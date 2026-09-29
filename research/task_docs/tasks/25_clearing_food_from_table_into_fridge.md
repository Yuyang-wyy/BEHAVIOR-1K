# 25 · Clearing Food from Table into Fridge

Task name `clearing_food_from_table_into_fridge`, task index 25.

> Pack the half chicken and the half apple pie from the plates on the breakfast table into the two tupperware containers from the countertop, then put both tupperware containers inside the refrigerator in the kitchen and make sure the refrigerator is closed at the end.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 435.6 s mean (13068 steps) |
| episode time limit | 653.4 s (19602 steps at 30 Hz) |
| human base travel | 31.8313 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.8 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.40; ft40k@sulab1 Q=0.20; ft40k@local Q=0.20 |
| demo video | https://player.vimeo.com/video/1114059394 |

## Planner notes

**Tier:** C — container-in-container: the food goes into tupperware, then both tupperware go into the fridge. The half chicken (0.14 m smallest side) and tupperware (0.22 x 0.22 x 0.14 m) are wider than the 44 mm span; the half pie is 0.037 m thick lying flat on a plate.

### Goal in plain words

The half apple pie must be inside a tupperware, and the half chicken must be inside a tupperware (the same one or different ones; 4 ground options).
Both tupperware containers must be inside the kitchen fridge, and the fridge must be closed at the end.
The plates stay where they are; they have no goal.

### Q traps

- 5 literals. `not open fridge` is already true at reset (fridge joint_pos [0, 0] in all 20 instances), so it never scores. Max partial Q is 0.8; full success still needs the fridge closed.
- Both tupperware must be in the fridge, even an empty one (`forall` over tupperware). If only one tupperware is used for food, the other still has to go in.
- `inside food tupperware` is checked wherever the tupperware is. Food that slides out while the tupperware is carried or tilted into the fridge loses the literal. Place the tupperware level on a shelf.
- The fridge is side-by-side (`left_door`, `right_door`). `not open` fails if either door is past 5 % (PREDICATES §6). Close every door touched, last.
- The tupperware asset has no lid joint (no joint_pos in the template), so there is no lid to close.

### Minimal plan

All in kitchen_0. Food on plates on the breakfast table (1.4-3.4 m from start); tupperware on `bar_egwapq_0` (1.8-7 m); fridge 2-5 m.

1. `move to the tupperware`, `pick up the tupperware from the bar` twice (one per hand). ~22 s + 15 s each.
2. `move to the breakfast table`, `place the tupperware on the breakfast table` twice — both tupperware standing open on the table next to the plates. ~22 s + 7 s each.
3. `move to the half chicken`, `pick up the half chicken from the plate`, `move to the tupperware`, `place the half chicken in the tupperware`. ~22 + 15 + 22 + 14 s. Scores 1/5.
4. `move to the half apple pie`, `push the half apple pie to the to_the_edge_of plate`, `pick up the half apple pie from the plate`, `move to the tupperware`, `place the half apple pie in the tupperware`. ~22 + 23 + 15 + 22 + 14 s. Scores 1/5.
5. `move to the fridge`, `open the door of the right_door fridge` — right door wide open. ~22 s + 24 s.
6. `move to the tupperware`, `pick up the tupperware from the breakfast table` twice — keep them level. ~22 s + 15 s each.
7. `move to the fridge`, `place the tupperware in the layer_4 fridge`, `place the tupperware in the layer_5 fridge`. ~22 s + 14 s each. Each scores 1/5.
8. `close the door of the right_door fridge` — door flush. ~16 s. Success ends the episode.

Budget: about 430 s against a 653 s limit. Opening the fridge before step 1 (while the hands are empty) is an alternative the demos do not use.

### What the demos do differently

- All 200 demos bring both tupperware to the breakfast table first, then load the food there. 148 put the chicken and pie in different tupperware, 52 in the other pairing; none put both in one.
- All 200 push the half pie to the plate edge before picking it; keep that for the thin pie.
- An alternative the goal allows: carry the food to the tupperware on the bar instead. It saves no time because the tupperware must be carried to the fridge anyway.

### Hard parts and hacks

- Half chicken: 0.20 x 0.14 x 0.14 m, no dimension under 44 mm; unverified where a grasp would register (leg bone?).
- Half pie: 0.09 x 0.17 x 0.037 m, flat on a plate. The 0.037 m thickness fits the span only once the pie overhangs the plate edge.
- Tupperware: 0.22 m square, 0.14 m tall, no handle. The grasp must go across a wall. Carrying a loaded one level into a fridge shelf is the riskiest step.
- The fridge door handle width is unknown.

### Hints for the VLM

- The kitchen has one fridge (tall, two vertical doors), one breakfast table with four chairs, two bars (the tupperware sit on `bar_egwapq_0`), a dishwasher, an oven and a microwave.
- The two plates on the breakfast table hold the half chicken and the half apple pie. The two tupperware are identical clear containers.
- Done: breakfast-table plates empty, both tupperware on fridge shelves with food visible inside, both fridge doors flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside half__apple_pie.n.01_1 tupperware.n.01_2)` | no | yes |
| `(inside half__chicken.n.01_1 tupperware.n.01_2)` | no | yes |
| `(inside tupperware.n.01_2 electric_refrigerator.n.01_1)` | no | yes |
| `(inside tupperware.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

The goal has 4 ground options (5 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists 
                (?tupperware.n.01 - tupperware.n.01)
                (inside ?half__apple_pie.n.01_1 ?tupperware.n.01)
            )
            (exists 
                (?tupperware.n.01 - tupperware.n.01)
                (inside ?half__chicken.n.01_1 ?tupperware.n.01)
            )
            (forall 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?tupperware.n.01 ?electric_refrigerator.n.01_1)
            ) 
            (not
                (open ?electric_refrigerator.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `half__chicken.n.01_1` | half_chicken_78 | half_chicken / hkcqlq | kitchen_0 | table/counter (0.6-1.1 m), z 0.76 | 2.26 m (range 1.44-3.41) | yes, spread 1.07 m |
| `half__apple_pie.n.01_1` | half_apple_pie_77 | half_apple_pie / grcock | kitchen_0 | table/counter (0.6-1.1 m), z 0.71 | 2.46 m (range 1.5-3.41) | yes, spread 1.3 m |
| `plate.n.04_1` | plate_76 | plate / fhdyrj | kitchen_0 | table/counter (0.6-1.1 m), z 0.7 | 2.25 m (range 1.44-3.41) | yes, spread 1.06 m |
| `plate.n.04_2` | plate_75 | plate / fhdyrj | kitchen_0 | table/counter (0.6-1.1 m), z 0.7 | 2.45 m (range 1.51-3.4) | yes, spread 1.3 m |
| `breakfast_table.n.01_1` | breakfast_table_xftrki_0 | breakfast_table / xftrki | kitchen_0 | table/counter (0.6-1.1 m), z 0.63 | 2.38 m (range 1.4-3.16) | no |
| `tupperware.n.01_1` | tupperware_74 | tupperware / mkstwr | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 4.92 m (range 1.8-6.84) | yes, spread 1.88 m |
| `tupperware.n.01_2` | tupperware_73 | tupperware / mkstwr | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 4.47 m (range 1.81-7.02) | yes, spread 2.23 m |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 4.81 m (range 1.37-7.19) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.79 m (range 2.08-5.03) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.44 m (range 0.91-3.76) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom breakfast_table.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop half__apple_pie.n.01_1 plate.n.04_2)
(ontop half__chicken.n.01_1 plate.n.04_1)
(ontop plate.n.04_1 breakfast_table.n.01_1)
(ontop plate.n.04_2 breakfast_table.n.01_1)
(ontop tupperware.n.01_1 countertop.n.01_1)
(ontop tupperware.n.01_2 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching breakfast_table.n.01_1 plate.n.04_1)
(touching breakfast_table.n.01_1 plate.n.04_2)
(touching countertop.n.01_1 tupperware.n.01_1)
(touching countertop.n.01_1 tupperware.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching half__apple_pie.n.01_1 plate.n.04_2)
(touching half__chicken.n.01_1 plate.n.04_1)
(touching plate.n.04_1 breakfast_table.n.01_1)
(touching plate.n.04_1 half__chicken.n.01_1)
(touching plate.n.04_2 breakfast_table.n.01_1)
(touching plate.n.04_2 half__apple_pie.n.01_1)
(touching tupperware.n.01_1 countertop.n.01_1)
(touching tupperware.n.01_2 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 429.05 s (range 329.0-640.97). Skills per demo 25.0 (range 24-25). 4 distinct skill orders; the most common one covers 80% of demos.

Most common skill counts per demo (80% of demos): move to x10, pick up from x6, place in x4, place on x2, close door x1, open door x1, push to x1.

Representative demo `episode_00250650.json` (432.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the tupperware` (0.0-15.1 s)
2. `pick up the tupperware from the bar` (15.2-33.4 s)
3. `move to the tupperware` (33.4-34.6 s)
4. `pick up the tupperware from the bar` (34.6-39.3 s)
5. `move to the breakfast table` (39.3-67.3 s)
6. `place the tupperware on the breakfast table` (67.3-75.4 s)
7. `place the tupperware on the breakfast table` (75.4-85.6 s)
8. `move to the half chicken` (85.6-119.0 s)
9. `pick up the half chicken from the plate` (119.0-156.1 s)
10. `move to the tupperware` (156.1-195.5 s)
11. `place the half chicken in the tupperware` (195.5-213.0 s)
12. `move to the half apple pie` (213.0-215.7 s)
13. `push the half apple pie to the to_the_edge_of plate` (215.7-235.3 s)
14. `pick up the half apple pie from the plate` (235.3-246.3 s)
15. `move to the tupperware` (246.3-251.9 s)
16. `place the half apple pie in the tupperware` (251.9-264.2 s)
17. `move to the fridge` (264.2-286.4 s)
18. `open the door of the right_door fridge` (286.4-310.4 s)
19. `move to the tupperware` (310.4-336.1 s)
20. `pick up the tupperware from the breakfast table` (336.1-344.9 s)
21. `pick up the tupperware from the breakfast table` (344.9-350.2 s)
22. `move to the fridge` (350.2-370.8 s)
23. `place the tupperware in the layer_4 fridge` (370.8-405.1 s)
24. `place the tupperware in the layer_5 fridge` (405.1-422.4 s)
25. `close the door of the right_door fridge` (422.4-432.8 s)

Mean duration per skill in this task: close door 16.3 s, move to 21.5 s, open door 24.2 s, pick up from 15.1 s, place in 14.0 s, place on 7.0 s, push to 22.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tupperware` | 963 |
| `pick up the tupperware from the breakfast table` | 401 |
| `move to the fridge` | 400 |
| `place the tupperware on the breakfast table` | 399 |
| `pick up the tupperware from the bar` | 397 |
| `move to the breakfast table` | 200 |
| `pick up the half chicken from the plate` | 200 |
| `place the half chicken in the tupperware` | 200 |
| `move to the half apple pie` | 200 |
| `push the half apple pie to the to_the_edge_of plate` | 200 |
| `pick up the half apple pie from the plate` | 200 |
| `place the half apple pie in the tupperware` | 200 |
| `place the tupperware in the layer_5 fridge` | 200 |
| `move to the half chicken` | 199 |
| `open the door of the right_door fridge` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/25_clearing_food_from_table_into_fridge.json`. Planner notes: `task_docs/notes/25_clearing_food_from_table_into_fridge.md`.
