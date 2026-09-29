# 24 · Storing Food

Task name `storing_food`, task index 24.

> Put away all the food on the kitchen countertop by storing it inside the kitchen cabinets: move the two boxes of oatmeal, two bags of chips, two bottles of olive oil, and two jars of sugar from the countertop into the kitchen cabinets (each item can go into either cabinet).

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 662.3 s mean (19869 steps) |
| episode time limit | 993.5 s (29803 steps at 30 Hz) |
| human base travel | 55.6409 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1679616 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://player.vimeo.com/video/1114059272 |

## Planner notes

**Tier:** B — eight pantry items go from one countertop into kitchen cabinets, all within ~5 m. Most bodies are wider than the 44 mm span (sugar jar 0.078 m, olive-oil bottle 0.082 m body, oatmeal box 0.127 m, chips bag 0.10 m); grasps need a neck, rim or thin edge. The cabinet door must be opened first.

### Goal in plain words

Both oatmeal boxes, both chip bags, both olive-oil bottles and both sugar jars must each be inside some kitchen cabinet.
Every item picks its cabinet independently (`forall ... exists`), and all six kitchen cabinets count (`cabinet.n.01_*` covers the 3 top cabinets, the tall `bottom_cabinet_fancyy_0` and the 2 under-counter `bottom_cabinet_no_top` units). Items do not need to share a cabinet.
There is NO `not open` literal: cabinet doors may be left open.

### Q traps

- 8 literals, all False at reset. Each item is worth 1/8. 1,679,616 ground options (6 cabinets per item); Q takes the best, so the planner never needs to track which cabinet each item used.
- No cabinet needs closing. 198/200 demos close the door at the end; skip it. Closing it can also push an item back out of the volume (PREDICATES §3).
- `inside` needs the item's AABB centre in a cabinet's fillable volume (PREDICATES §3). Whether the `bottom_cabinet_no_top` units and the top cabinets have volumes in their USD is unverified; the demos only use `bottom_cabinet_fancyy_0`, so use it.
- All six cabinets start closed (every joint_pos 0 in the template and all 20 instances).
- An item left on the cabinet's open door or on top of the cabinet scores 0.

### Minimal plan

All items are on `countertop_kelzer_0`; the target cabinet `bottom_cabinet_fancyy_0` (1.97 m tall) is 1.1-5.1 m from the start.

1. `move to the bottom cabinet`, `open the door of the left_door bottom cabinet` — left door swung wide, shelves visible. ~21 s + 29 s.
2. `move to the bottle of olive oil`, `pick up the bottle of olive oil from the countertop`, twice (one per hand). ~21 s + 17 s each.
3. `move to the bottom cabinet`, `place the bottle of olive oil in the layer_2 bottom cabinet` twice. ~21 s + 17 s each.
4. Same pattern for the chips: `pick up the bag of chips from the countertop`, `place the bag of chips in the layer_3 bottom cabinet`.
5. Same for the sugar: `pick up the jar of sugar from the countertop`, `place the jar of sugar in the layer_2 bottom cabinet`.
6. Each oatmeal box, one at a time: `move to the box of oatmeal`, `tip over the box of oatmeal`, `push the box of oatmeal to the to_the_edge_of countertop`, `pick up the box of oatmeal from the countertop`, `move to the bottom cabinet`, `place the box of oatmeal in the layer_4 bottom cabinet`, `push the box of oatmeal to the center bottom cabinet`. ~21 + 8 + 12 + 17 + 21 + 17 + 12 s.
7. Stop. Do not close the door.

Done-check per item: item no longer on the countertop and visible on a shelf behind the door line.
Budget: about 580 s against a 994 s limit.

### What the demos do differently

- All 200 demos use only `bottom_cabinet_fancyy_0` and open its `left_door`.
- 198/200 close the door at the end; not needed for the goal.
- Every demo tips each oatmeal box onto its side, then pushes it to the counter edge before picking. The follow-up `push the box of oatmeal to the center bottom cabinet` shoves it deeper onto the shelf.
- The order of item types varies freely (top sequences cover only 2 demos each).

### Hard parts and hacks

- Grasp span: no item body is under 44 mm. The bottle neck is the likely grasp (width not in metadata; unverified). The sugar jar (0.078 m) may only be graspable at a lid rim, unverified.
- Oatmeal box (0.13 x 0.27 x 0.23 m): the tip-over + edge-push routine is how humans got a grip; it is in-distribution.
- Shelf heights of the tall cabinet (layers 2-4 in the prompts) are unknown; the cabinet is 1.97 m tall.
- If the door swings back while the arms are busy, it blocks the shelves. Open it wide.

### Hints for the VLM

- Target: the tall pantry-style cabinet (`bottom_cabinet_fancyy_0`, 0.65 x 1.23 x 1.97 m), the only full-height cabinet in the kitchen. The other five cabinets (three wall cabinets at 1.8 m, two under-counter runs) also count but are untested.
- All eight items start on the long kitchen countertop, which also holds the sink area. Another countertop exists; nothing is on it.
- Done: countertop clear of the eight items, all visible inside cabinets. The door can stay open.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside box__of__oatmeal.n.01_2 cabinet.n.01_3)` | no | yes |
| `(inside box__of__oatmeal.n.01_1 cabinet.n.01_3)` | no | yes |
| `(inside bag__of__chips.n.01_2 cabinet.n.01_3)` | no | yes |
| `(inside bag__of__chips.n.01_1 cabinet.n.01_3)` | no | yes |
| `(inside bottle__of__olive_oil.n.01_1 cabinet.n.01_3)` | no | yes |
| `(inside bottle__of__olive_oil.n.01_2 cabinet.n.01_3)` | no | yes |
| `(inside jar__of__sugar.n.01_2 cabinet.n.01_3)` | no | yes |
| `(inside jar__of__sugar.n.01_1 cabinet.n.01_3)` | no | yes |

The goal has 1679616 ground options (8 literals x1679616); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall
                (?box__of__oatmeal.n.01 - box__of__oatmeal.n.01)
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?box__of__oatmeal.n.01 ?cabinet.n.01)
                )
            )
            (forall
                (?bag__of__chips.n.01 - bag__of__chips.n.01)
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?bag__of__chips.n.01 ?cabinet.n.01)
                )
            )
            (forall
                (?bottle__of__olive_oil.n.01 - bottle__of__olive_oil.n.01)
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?bottle__of__olive_oil.n.01 ?cabinet.n.01)
                )
            )
            (forall
                (?jar__of__sugar.n.01 - jar__of__sugar.n.01)
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?jar__of__sugar.n.01 ?cabinet.n.01)
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
| `box__of__oatmeal.n.01_1` | box_of_oatmeal_214 | box_of_oatmeal / zkggxm | kitchen_0 | table/counter (0.6-1.1 m), z 1.0 | 2.75 m (range 0.97-3.82) | yes, spread 2.53 m |
| `box__of__oatmeal.n.01_2` | box_of_oatmeal_213 | box_of_oatmeal / zkggxm | kitchen_0 | table/counter (0.6-1.1 m), z 1.0 | 2.98 m (range 0.92-3.74) | yes, spread 2.61 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 2.28 m (range 1.09-3.62) | no (fixed) |
| `bag__of__chips.n.01_1` | bag_of_chips_212 | bag_of_chips / bryahw | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 2.18 m (range 1.05-3.76) | yes, spread 2.7 m |
| `bag__of__chips.n.01_2` | bag_of_chips_211 | bag_of_chips / bryahw | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 2.55 m (range 1.13-3.48) | yes, spread 2.22 m |
| `bottle__of__olive_oil.n.01_1` | bottle_of_olive_oil_210 | bottle_of_olive_oil / ajswsh | kitchen_0 | table/counter (0.6-1.1 m), z 1.01 | 1.87 m (range 0.81-3.89) | yes, spread 3.0 m |
| `bottle__of__olive_oil.n.01_2` | bottle_of_olive_oil_209 | bottle_of_olive_oil / ajswsh | kitchen_0 | table/counter (0.6-1.1 m), z 1.01 | 2.26 m (range 0.94-3.73) | yes, spread 2.68 m |
| `jar__of__sugar.n.01_1` | jar_of_sugar_208 | jar_of_sugar / pnbbfb | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.24 m (range 0.85-3.8) | yes, spread 2.89 m |
| `jar__of__sugar.n.01_2` | jar_of_sugar_207 | jar_of_sugar / pnbbfb | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.28 m (range 1.11-3.8) | yes, spread 2.46 m |
| `cabinet.n.01_1` | top_cabinet_lkxmne_0 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 3.14 m (range 1.48-4.36) | no (fixed) |
| `cabinet.n.01_2` | bottom_cabinet_no_top_rkgjer_0 | bottom_cabinet_no_top / rkgjer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 2.36 m (range 1.17-3.67) | no (fixed) |
| `cabinet.n.01_3` | bottom_cabinet_fancyy_0 | bottom_cabinet / fancyy | kitchen_0 | high (1.1-1.6 m), z 1.12 | 3.66 m (range 1.1-5.1) | no (fixed) |
| `cabinet.n.01_4` | bottom_cabinet_no_top_gjeoer_0 | bottom_cabinet_no_top / gjeoer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 1.9 m (range 1.1-4.27) | no (fixed) |
| `cabinet.n.01_5` | top_cabinet_lkxmne_2 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 1.91 m (range 1.21-4.56) | no (fixed) |
| `cabinet.n.01_6` | top_cabinet_lkxmne_1 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 2.17 m (range 1.22-4.32) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.55 m (range 0.83-2.37) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 kitchen)
(inroom cabinet.n.01_2 kitchen)
(inroom cabinet.n.01_3 kitchen)
(inroom cabinet.n.01_4 kitchen)
(inroom cabinet.n.01_5 kitchen)
(inroom cabinet.n.01_6 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bag__of__chips.n.01_1 countertop.n.01_1)
(ontop bag__of__chips.n.01_2 countertop.n.01_1)
(ontop bottle__of__olive_oil.n.01_1 countertop.n.01_1)
(ontop bottle__of__olive_oil.n.01_2 countertop.n.01_1)
(ontop box__of__oatmeal.n.01_1 countertop.n.01_1)
(ontop box__of__oatmeal.n.01_2 countertop.n.01_1)
(ontop jar__of__sugar.n.01_1 countertop.n.01_1)
(ontop jar__of__sugar.n.01_2 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bag__of__chips.n.01_1 countertop.n.01_1)
(touching bag__of__chips.n.01_2 countertop.n.01_1)
(touching bottle__of__olive_oil.n.01_1 countertop.n.01_1)
(touching bottle__of__olive_oil.n.01_2 countertop.n.01_1)
(touching box__of__oatmeal.n.01_1 countertop.n.01_1)
(touching box__of__oatmeal.n.01_2 countertop.n.01_1)
(touching countertop.n.01_1 bag__of__chips.n.01_1)
(touching countertop.n.01_1 bag__of__chips.n.01_2)
(touching countertop.n.01_1 bottle__of__olive_oil.n.01_1)
(touching countertop.n.01_1 bottle__of__olive_oil.n.01_2)
(touching countertop.n.01_1 box__of__oatmeal.n.01_1)
(touching countertop.n.01_1 box__of__oatmeal.n.01_2)
(touching countertop.n.01_1 jar__of__sugar.n.01_1)
(touching countertop.n.01_1 jar__of__sugar.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching jar__of__sugar.n.01_1 countertop.n.01_1)
(touching jar__of__sugar.n.01_2 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 631.07 s (range 532.7-867.0). Skills per demo 37.5 (range 33-43). 116 distinct skill orders; the most common one covers 5% of demos.

Most common skill counts per demo (19% of demos): move to x13, pick up from x8, place in x8, push to x4, tip over x2, close door x1, open door x1.

Representative demo `episode_00240270.json` (723.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bottom cabinet` (0.0-29.9 s)
2. `open the door of the left_door bottom cabinet` (29.9-60.0 s)
3. `move to the bottle of olive oil` (60.0-77.5 s)
4. `pick up the bottle of olive oil from the countertop` (77.5-93.5 s)
5. `move to the bottle of olive oil` (93.5-108.2 s)
6. `pick up the bottle of olive oil from the countertop` (108.2-122.1 s)
7. `move to the bottom cabinet` (122.1-151.1 s)
8. `place the bottle of olive oil in the layer_2 bottom cabinet` (151.1-175.8 s)
9. `place the bottle of olive oil in the layer_2 bottom cabinet` (175.8-184.0 s)
10. `move to the bag of chips` (184.0-200.2 s)
11. `pick up the bag of chips from the countertop` (200.2-215.2 s)
12. `move to the bag of chips` (215.2-231.2 s)
13. `pick up the bag of chips from the countertop` (231.2-246.2 s)
14. `move to the bottom cabinet` (246.2-270.6 s)
15. `place the bag of chips in the layer_3 bottom cabinet` (270.7-280.0 s)
16. `place the bag of chips in the layer_3 bottom cabinet` (280.0-300.2 s)
17. `move to the jar of sugar` (300.2-318.6 s)
18. `pick up the jar of sugar from the countertop` (318.7-335.2 s)
19. `move to the jar of sugar` (335.2-345.2 s)
20. `pick up the jar of sugar from the countertop` (345.2-364.1 s)
21. `move to the bottom cabinet` (364.1-387.2 s)
22. `place the jar of sugar in the layer_2 bottom cabinet` (387.2-417.0 s)
23. `place the jar of sugar in the layer_2 bottom cabinet` (417.0-440.1 s)
24. `move to the box of oatmeal` (440.1-457.1 s)
25. `tip over the box of oatmeal` (457.1-469.1 s)
26. `push the box of oatmeal to the to_the_edge_of countertop` (469.1-482.5 s)
27. `pick up the box of oatmeal from the countertop` (482.5-514.5 s)
28. `move to the bottom cabinet` (514.5-532.5 s)
29. `place the box of oatmeal in the layer_4 bottom cabinet` (532.5-550.1 s)
30. `push the box of oatmeal to the center bottom cabinet` (550.1-561.1 s)
31. `move to the box of oatmeal` (561.1-585.2 s)
32. `tip over the box of oatmeal` (585.2-591.2 s)
33. `push the box of oatmeal to the to_the_edge_of countertop` (591.2-604.1 s)
34. `pick up the box of oatmeal from the countertop` (604.1-631.0 s)
35. `move to the bottom cabinet` (631.0-663.0 s)
36. `place the box of oatmeal in the layer_4 bottom cabinet` (663.0-681.0 s)
37. `push the box of oatmeal to the center bottom cabinet` (681.0-695.2 s)
38. `close the door of the left_door bottom cabinet` (695.2-723.0 s)

Mean duration per skill in this task: close door 19.3 s, move to 21.0 s, open door 28.6 s, pick up from 16.9 s, place in 16.5 s, place on 5.7 s, push to 12.0 s, tip over 8.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bottom cabinet` | 1200 |
| `push the box of oatmeal to the to_the_edge_of countertop` | 457 |
| `pick up the box of oatmeal from the countertop` | 434 |
| `pick up the bag of chips from the countertop` | 400 |
| `place the bag of chips in the layer_3 bottom cabinet` | 400 |
| `pick up the jar of sugar from the countertop` | 400 |
| `place the jar of sugar in the layer_2 bottom cabinet` | 400 |
| `move to the box of oatmeal` | 400 |
| `tip over the box of oatmeal` | 400 |
| `pick up the bottle of olive oil from the countertop` | 400 |
| `place the box of oatmeal in the layer_4 bottom cabinet` | 398 |
| `place the bottle of olive oil in the layer_2 bottom cabinet` | 397 |
| `push the box of oatmeal to the center bottom cabinet` | 393 |
| `move to the bag of chips` | 345 |
| `move to the bottle of olive oil` | 319 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/24_storing_food.json`. Planner notes: `task_docs/notes/24_storing_food.md`.
