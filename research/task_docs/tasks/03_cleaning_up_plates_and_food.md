# 03 · Cleaning Up Plates and Food

Task name `cleaning_up_plates_and_food`, task index 3.

> From the breakfast table in the kitchen, move both pizzas - keeping each on its plate - into the same refrigerator, put both bowls into one sink, and make sure the refrigerator is closed.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 456.5 s mean (13696 steps) |
| episode time limit | 684.8 s (20544 steps at 30 Hz) |
| human base travel | 35.9744 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | **0.571** realistic; 0.857 from `:init` alone. 0.857 needs the two pizzas swapped between plates; with each pizza kept on its own plate the ceiling is 4/7 (notes). |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114054554 |

## Planner notes

**Tier:** C — carry two plated pizzas into a closed two-door fridge and two bowls into a sink; plate and bowl widths vs the 44 mm span are unverified, and each plate must be carried level so the pizza stays on it.

### Goal in plain words

- Both pizzas must end inside the fridge, each still resting on a plate. Either pizza may sit on either plate (`forpairs`).
- Both bowls must end inside the one sink (`drop_in_sink_lkklqs_0`).
- The fridge must end with both doors shut (within 5 % of closed, PREDICATES §6).
- The kitchen has one fridge and one sink, so there are no container choices to make.

### Q traps

- 7 literals. `not open fridge` is true at reset: it never scores but blocks success. Verified in the template and all 20 instances: both fridge joints are at ~0.
- The page's "best option" (0.857) pairs pizza_2 with plate_1 and pizza_1 with plate_2. That option only pays if the pizzas are swapped between plates. Nobody should do that.
- Keep each pizza on its own plate. Then both `ontop` literals are true at reset and never score. The realistic partial Q is 4/7 = 0.571: 2 pizzas inside the fridge plus 2 bowls inside the sink.
- Full success (1.0) needs both pizzas still `ontop` their plates at the end. A pizza that slides off in transit, or rests half on the fridge shelf, blocks success.
- `inside` tests the pizza's AABB centre, not the plate's. The pizza must be fully on a fridge shelf, not on a door bin (door bins have unverified volume, §16).
- Close the fridge only after both plates are in. Closing can push a plate out or leave a door ajar (§3, §6).
- If the fridge ends open, you lose success but no partial Q. Bowls in the sink still score on their own.
- In instances 306 and 309 the pizza starts ~5 cm higher than on the others (z 0.74-0.75 vs 0.70). It may rest tilted on the plate rim. Unverified.

### Minimal plan

1. `move to the fridge` — base stopped facing the fridge doors. ~26 s.
2. `open the door of the right_door fridge` — right door visibly swung wide, shelves visible. ~40 s.
3. `move to the plate` — plate with pizza centred in the head camera. ~26 s.
4. `pick up the plate from the breakfast table` — plate lifted clear of the table, pizza still on it, gripper stopped short of fully closed. ~24 s.
5. `move to the fridge` — ~26 s.
6. `place the plate in the layer_5 fridge` — plate on a shelf, gripper open and withdrawn, pizza on the plate. ~19 s.
7. Repeat 3-6 with `place the plate in the layer_4 fridge` — second plate on another shelf. ~95 s.
8. `close the door of the right_door fridge` — door flush with the body, no gap visible in depth. ~22 s.
9. `move to the bowl`, then `pick up the bowl from the breakfast table` — bowl lifted. ~50 s.
10. `move to the bowl`, then `pick up the bowl from the breakfast table` — second bowl in the other hand. ~50 s.
11. `move to the drop in sink` — ~26 s.
12. `place the bowl in the drop in sink` twice — both bowls below the sink rim, grippers open. ~38 s.

- Total is about 420 s against a 684.8 s limit. There is ~260 s of slack for retries.
- If time runs low, do the bowls (steps 9-12) first. They are 2/7 of Q and need no door.

### What the demos do differently

- 64 % of demos use exactly the order above: fridge first, then bowls.
- The humans open only the right fridge door. The template has 2 fridge joints; the left door is never touched and stays closed.
- The humans carry one plate per trip, but both bowls in one trip (one per hand).
- 2 of 200 demos use `push the plate to the center fridge` to nudge the plate deeper onto the shelf. That is a useful recovery when the plate sits near the shelf edge.

### Hard parts and hacks

- Grasping the plate: a flat plate has no handle. The rim thickness is not verified against the 44 mm span. The pizza (scale 0.63 x 0.64 x 2.34) rides loose on top.
- Carrying the plate level while the base moves ~36 m in total (human mean). A tilt dumps the pizza, and then `ontop` fails.
- Placing inside the fridge at shelf height: the arm must reach in past the open door without hitting it closed.
- The fridge door handle width is not verified. Closing can be done by pushing with no grasp (§6).
- Sink `inside`: the sink needs a fillable volume in its runtime USD (§3). This is not verified for `drop_in_sink/lkklqs`. Dropping from just above the basin is enough.
- The sink has a ToggledOn state (the faucet). It is not in the goal; leave it alone.
- No scripted shortcut beats the VLA here. Every scoring literal needs a carried object.

### Hints for the VLM

- Everything is in `kitchen_0`. The breakfast table is at z ~0.63 m and holds 2 plates with pizzas and 2 bowls. The plates sit close together near x ~4.0-4.3, y ~1.3-1.9.
- The fridge is the only fridge in the kitchen (`fridge_petcxr_0`), a tall two-door unit.
- The sink is the single drop-in sink set in the counter.
- Distractors in the kitchen: a microwave, oven, dishwasher, 2 top cabinets, and 4 straight chairs around the table. None of these is a valid target.
- Done for the pizzas: both plates visible on fridge shelves with pizzas on top, then the fridge door flush and closed.
- Done for the bowls: both bowls visible inside the sink basin, below the rim, not on the counter beside it.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop pizza.n.01_2 plate.n.04_1)` | no | yes |
| `(ontop pizza.n.01_1 plate.n.04_2)` | no | yes |
| `(inside pizza.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(inside pizza.n.01_2 electric_refrigerator.n.01_1)` | no | yes |
| `(inside bowl.n.01_2 sink.n.01_1)` | no | yes |
| `(inside bowl.n.01_1 sink.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

The goal has 2 ground options (7 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forpairs 
                (?pizza.n.01 - pizza.n.01) 
                (?plate.n.04 - plate.n.04)
                (ontop ?pizza.n.01 ?plate.n.04)
            ) 
            (exists
                (?electric_refrigerator.n.01 - electric_refrigerator.n.01)
                (forall
                    (?pizza.n.01 - pizza.n.01)
                    (inside ?pizza.n.01 ?electric_refrigerator.n.01)
                )
            )
            (exists
                (?sink.n.01 - sink.n.01)
                (forall 
                    (?bowl.n.01 - bowl.n.01)
                    (inside ?bowl.n.01 ?sink.n.01)
                )
            )
            (forall
                (?electric_refrigerator.n.01 - electric_refrigerator.n.01)
                (not
                    (open ?electric_refrigerator.n.01)
                )
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `plate.n.04_1` | plate_94 | plate / itoeew | kitchen_0 | table/counter (0.6-1.1 m), z 0.68 | 2.61 m (range 1.38-3.28) | yes, spread 0.73 m |
| `plate.n.04_2` | plate_93 | plate / itoeew | kitchen_0 | table/counter (0.6-1.1 m), z 0.68 | 2.37 m (range 0.91-3.4) | yes, spread 1.2 m |
| `bowl.n.01_1` | bowl_92 | bowl / adciys | kitchen_0 | table/counter (0.6-1.1 m), z 0.71 | 2.1 m (range 1.32-3.26) | yes, spread 1.47 m |
| `bowl.n.01_2` | bowl_91 | bowl / adciys | kitchen_0 | table/counter (0.6-1.1 m), z 0.71 | 2.29 m (range 1.18-3.41) | yes, spread 1.28 m |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.02 m (range 1.25-3.73) | no (fixed) |
| `pizza.n.01_1` | pizza_90 | pizza / vyfhkm | kitchen_0 | table/counter (0.6-1.1 m), z 0.7 | 2.6 m (range 1.38-3.28) | yes, spread 0.73 m |
| `pizza.n.01_2` | pizza_89 | pizza / vyfhkm | kitchen_0 | table/counter (0.6-1.1 m), z 0.7 | 2.37 m (range 0.91-3.4) | yes, spread 1.2 m |
| `breakfast_table.n.01_1` | breakfast_table_xftrki_0 | breakfast_table / xftrki | kitchen_0 | table/counter (0.6-1.1 m), z 0.63 | 2.22 m (range 1.45-3.11) | no |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.12 m (range 1.4-5.04) | no (fixed) |
| `sink.n.01_1` | drop_in_sink_lkklqs_0 | drop_in_sink / lkklqs | kitchen_0 | table/counter (0.6-1.1 m), z 0.86 | 2.41 m (range 1.66-7.08) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom breakfast_table.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom sink.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bowl.n.01_1 breakfast_table.n.01_1)
(ontop bowl.n.01_2 breakfast_table.n.01_1)
(ontop pizza.n.01_1 plate.n.04_1)
(ontop pizza.n.01_2 plate.n.04_2)
(ontop plate.n.04_1 breakfast_table.n.01_1)
(ontop plate.n.04_2 breakfast_table.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bowl.n.01_1 breakfast_table.n.01_1)
(touching bowl.n.01_2 breakfast_table.n.01_1)
(touching breakfast_table.n.01_1 bowl.n.01_1)
(touching breakfast_table.n.01_1 bowl.n.01_2)
(touching breakfast_table.n.01_1 plate.n.04_1)
(touching breakfast_table.n.01_1 plate.n.04_2)
(touching floor.n.01_1 agent.n.01_1)
(touching pizza.n.01_1 plate.n.04_1)
(touching pizza.n.01_2 plate.n.04_2)
(touching plate.n.04_1 breakfast_table.n.01_1)
(touching plate.n.04_1 pizza.n.01_1)
(touching plate.n.04_2 breakfast_table.n.01_1)
(touching plate.n.04_2 pizza.n.01_2)
```

## What the human demos did

200 annotated demos. Length 455.2 s (range 263.93-617.3). Skills per demo 19.0 (range 17-20). 9 distinct skill orders; the most common one covers 64% of demos.

Most common skill counts per demo (64% of demos): move to x9, pick up from x4, place in x4, close door x1, open door x1.

Representative demo `episode_00031520.json` (470.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-16.6 s)
2. `open the door of the right_door fridge` (16.6-64.2 s)
3. `move to the plate` (64.2-66.8 s)
4. `pick up the plate from the breakfast table` (66.8-82.1 s)
5. `move to the fridge` (82.1-103.7 s)
6. `place the plate in the layer_5 fridge` (103.7-128.4 s)
7. `move to the plate` (128.4-164.0 s)
8. `pick up the plate from the breakfast table` (164.0-201.6 s)
9. `move to the fridge` (201.6-227.7 s)
10. `place the plate in the layer_4 fridge` (227.7-247.1 s)
11. `move to the fridge` (247.1-298.1 s)
12. `close the door of the right_door fridge` (298.1-320.5 s)
13. `move to the bowl` (320.5-338.8 s)
14. `pick up the bowl from the breakfast table` (338.8-361.6 s)
15. `move to the bowl` (361.6-374.0 s)
16. `pick up the bowl from the breakfast table` (374.0-409.7 s)
17. `move to the drop in sink` (409.7-431.0 s)
18. `place the bowl in the drop in sink` (431.0-450.1 s)
19. `place the bowl in the drop in sink` (450.1-470.7 s)

Mean duration per skill in this task: close door 21.5 s, move to 25.8 s, open door 39.7 s, pick up from 24.1 s, place in 18.6 s, push to 10.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the fridge` | 799 |
| `pick up the plate from the breakfast table` | 400 |
| `pick up the bowl from the breakfast table` | 399 |
| `place the bowl in the drop in sink` | 399 |
| `move to the plate` | 376 |
| `move to the bowl` | 345 |
| `open the door of the right_door fridge` | 200 |
| `place the plate in the layer_5 fridge` | 200 |
| `close the door of the right_door fridge` | 200 |
| `move to the drop in sink` | 200 |
| `place the plate in the layer_4 fridge` | 199 |
| `push the plate to the center fridge` | 2 |
| `place the plate in the layer_4 breakfast table` | 1 |
| `place the bowl in the breakfast table` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/03_cleaning_up_plates_and_food.json`. Planner notes: `task_docs/notes/03_cleaning_up_plates_and_food.md`.
