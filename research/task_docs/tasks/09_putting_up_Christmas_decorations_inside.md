# 09 · Putting Up Christmas Decorations Inside

Task name `putting_up_Christmas_decorations_inside`, task index 9.

> In the living room, take the wreath, three candy canes, and two pillar candles out of the wicker basket. Place the wreath and two of the candy canes on the same living-room sofa. Put the remaining candy cane on top of a dining-room table. Put both pillar candles together on top of one dining-room table (they can share the same table). Finally, place all three gift boxes under or right next to the Christmas tree in the living room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | dining_room, living_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 457.3 s mean (13718 steps) |
| episode time limit | 685.9 s (20578 steps at 30 Hz) |
| human base travel | 41.3256 m |
| goal literals (best ground option) | 9 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 3888 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.33; ft40k@sulab1 Q=0.22; ft40k@local Q=0.22 |
| demo video | https://player.vimeo.com/video/1114056731 |

## Planner notes

**Tier:** C — nine pick-and-place literals across two rooms, 0.20 m gift boxes wider than the jaw span, and a basket dump; no state change needed.

### Goal in plain words

All three gift boxes end next to, under, or touching the Christmas tree (any mix of the three per box). Both pillar candles end on the dining-room breakfast table. Exactly one candy cane ends on that table. The wreath ends on any living-room sofa, and exactly two candy canes end on one sofa (not necessarily the wreath's sofa, despite the instruction wording). The wicker basket's final place does not matter.

### Q traps

- 9 literals, none true at start per `:init`. But gift boxes spawn randomly on the living-room floor: by an AABB estimate from the instance poses (tree asset 1.30 x 1.32 x 1.90 m, nextto gap limit ~0.28 m), at least one box already starts within the gap or inside the tree footprint in instances 306, 307, 308, 312 (two boxes), 315, 316. Those literals may be true at reset and then never score (ray part of `nextto` unverified). Instance 311: no box close.
- `forn` is exact (PREDICATES §0). Success needs exactly 1 cane on the table and exactly 2 canes on one sofa. Three canes on a sofa, or two on the table, blocks success; partial Q still picks the best 2-of-3 option.
- Only one table is in scope: `breakfast_table_rhjoby_0` in dining_room_0 (the template has no other table in the dining room). The living-room coffee table does NOT count for candles or the cane.
- Four sofas qualify (sofa_lugrhk_0/1, sofa_hiphpn_0, sofa_wnzdke_0, all living_room_0).
- `ontop` on a sofa needs the item's centre over sofa geometry and in contact; an item that slides into the seat-back gap or onto the floor scores 0.
- Everything scored reads only the final state: a cane knocked off the sofa while fetching the others loses its literal.
- Pillar candles inside a basket that sits on the table are not `ontop` the table (they touch the basket, not the table).

### Minimal plan

1. `move to the wicker basket` — basket centred in view, base stopped. ~14 s.
2. `pick up the wicker basket from the floors` — basket off the floor, gripper closed short of full. ~18 s.
3. `move to the sofa` — sofa seat fills lower image. ~14 s.
4. `pour the candy cane and candy cane and candy cane and pillar candle and pillar candle and wreath into the wicker basket` (the demo string; it means tipping the basket out over the sofa) — basket empty, items visible on the seat. ~23 s. This scores wreath + 2 canes at once (3/9).
5. `place the wicker basket on the coffee table` — frees the hand; any drop spot is fine. ~13 s.
6. Gift boxes x3 (living room, do before the long dining trips): `move to the gift box`, `pick up the gift box from the floors`, `move to the christmas tree`, `place the gift box on the floors next to the in_front_of christmas tree`, then `push the gift box to the center christmas tree` — box on the floor touching or under the tree skirt. ~55 s per box. If the grasp fails, push only.
7. `move to the candy cane`, `pick up the candy cane from the sofa`, `move to the breakfast table`, `place the candy cane on the breakfast table` — one cane on the table, two left on the sofa. ~60 s.
8. Pillar candles x2: `move to the pillar candle`, `pick up the pillar candle from the sofa`, `move to the breakfast table`, `place the pillar candle on the breakfast table`. ~60 s each.
- Total ~390 s against a 686 s limit; the demo mean is 457 s.

### What the demos do differently

- Nearly all demos use the same order: dump basket on sofa, park basket on coffee table, cane then both candles to the table, gift boxes last (52% exact order, 29 variants).
- Gift boxes are placed then pushed toward the tree centre (404 push segments over 571 placements).
- Seven demos push the wreath (`push the wreath to the away robot`); not needed.
- Parking the basket on the coffee table is not needed for the goal.
- Moving boxes earlier than the demos do banks 3 literals before the 7 m dining-room trips.

### Hard parts and hacks

- Gift box asset is 0.20 x 0.19 x 0.19 m, far over the 44 mm assisted-grasp span; humans lift it, the robot likely cannot. Pushing along the floor to the tree is legal and is a trained skill.
- Pillar candle is 0.05 x 0.05 x 0.07 m after scale 0.5: 50 mm across, just over 44 mm. Grasp may not register; unverified in sim.
- Candy cane is ~0.12 x 0.05 x 0.015 m after scaling; graspable but tiny and flat on a patterned cushion.
- Wreath is 0.20 x 0.20 x 0.04 m; it arrives on the sofa by the dump, so it never needs a grasp.
- Basket 0.26 x 0.41 x 0.19 m; handle width unverified. If it cannot be lifted, pushing it over is `tip over` (no demo prompt; closest: the pour string above).
- Hack: after picking the wreath and two canes out onto a sofa, carry the basket with 2 candles + 1 cane to the breakfast table and tip it there; all three land on the table. Rolling candles are the risk. Table asset is 1.16 x 2.90 m, so there is room.
- The tree moves between instances (spread 7.4 m) and so do the basket and boxes (spread ~9 m); nothing can be hard-coded.
- Breakfast table is 7.2 m (median) from the start pose through a doorway; base odometry drift is the navigation risk.

### Hints for the VLM

- Tree: 1.9 m tall conifer in living_room_0, the only one. "Next to" = within ~0.28 m of the tree's bounding box; pushing the box against the trunk/skirt (touching) is safest.
- Gift boxes: three identical wrapped boxes on the floor; any box to the tree counts.
- Sofas: four in living_room_0; pick the nearest one to the basket.
- Breakfast table: the long table (2.9 m) with six straight chairs in dining_room_0. The coffee table in the living room is a distractor.
- Done: one cane on the table and two on a sofa (count them), both candles upright on the table, wreath on a sofa, three boxes at the tree.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(nextto gift_box.n.01_2 christmas_tree.n.05_1)` | no | yes |
| `(nextto gift_box.n.01_1 christmas_tree.n.05_1)` | no | yes |
| `(nextto gift_box.n.01_3 christmas_tree.n.05_1)` | no | yes |
| `(ontop pillar_candle.n.01_1 table.n.02_1)` | no | yes |
| `(ontop pillar_candle.n.01_2 table.n.02_1)` | no | yes |
| `(ontop candy_cane.n.01_3 table.n.02_1)` | no | yes |
| `(ontop wreath.n.01_1 sofa.n.01_2)` | no | yes |
| `(ontop candy_cane.n.01_3 sofa.n.01_2)` | no | yes |
| `(ontop candy_cane.n.01_1 sofa.n.01_2)` | no | yes |

The goal has 3888 ground options (9 literals x3888); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?gift_box.n.01 - gift_box.n.01)
                (or 
                    (nextto ?gift_box.n.01 ?christmas_tree.n.05_1)
                    (under ?gift_box.n.01 ?christmas_tree.n.05_1)
                    (touching ?gift_box.n.01 ?christmas_tree.n.05_1)
                )
            )
            (exists
                (?table.n.02 - table.n.02)
                (forall
                    (?pillar_candle.n.01 - pillar_candle.n.01)
                    (ontop ?pillar_candle.n.01 ?table.n.02)
                )
            )
            (exists
                (?table.n.02 - table.n.02)
                (forn
                    (1)
                    (?candy_cane.n.01 - candy_cane.n.01)
                    (ontop ?candy_cane.n.01 ?table.n.02)
                )
            )
            (exists
                (?sofa.n.01 - sofa.n.01)
                (forall
                    (?wreath.n.01 - wreath.n.01)
                    (ontop ?wreath.n.01 ?sofa.n.01)
                )
            )
            (exists
                (?sofa.n.01 - sofa.n.01)
                (forn
                    (2)
                    (?candy_cane.n.01 - candy_cane.n.01)
                    (ontop ?candy_cane.n.01 ?sofa.n.01)
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
| `christmas_tree.n.05_1` | christmas_tree_228 | christmas_tree / eadukw | living_room_0 | table/counter (0.6-1.1 m), z 0.83 | 2.48 m (range 1.18-5.67) | yes, spread 7.42 m |
| `wreath.n.01_1` | wreath_227 | wreath / rkrxno | living_room_0 | floor, z 0.15 | 2.67 m (range 1.17-6.95) | yes, spread 8.72 m |
| `candy_cane.n.01_1` | candy_cane_226 | candy_cane / qfomjj | living_room_0 | floor, z 0.04 | 2.67 m (range 1.09-6.87) | yes, spread 8.77 m |
| `candy_cane.n.01_2` | candy_cane_225 | candy_cane / qfomjj | living_room_0 | floor, z 0.05 | 2.57 m (range 1.12-6.87) | yes, spread 8.53 m |
| `candy_cane.n.01_3` | candy_cane_224 | candy_cane / qfomjj | living_room_0 | floor, z 0.03 | 2.62 m (range 1.11-6.91) | yes, spread 8.58 m |
| `pillar_candle.n.01_1` | pillar_candle_223 | pillar_candle / cxswbc | living_room_0 | floor, z 0.05 | 2.58 m (range 1.14-6.85) | yes, spread 8.68 m |
| `pillar_candle.n.01_2` | pillar_candle_222 | pillar_candle / cxswbc | living_room_0 | floor, z 0.05 | 2.58 m (range 1.07-6.86) | yes, spread 8.59 m |
| `gift_box.n.01_1` | gift_box_221 | gift_box / mfalrc | living_room_0 | floor, z 0.08 | 2.87 m (range 0.85-6.95) | yes, spread 9.06 m |
| `gift_box.n.01_2` | gift_box_220 | gift_box / mfalrc | living_room_0 | floor, z 0.08 | 3.54 m (range 0.97-5.94) | yes, spread 9.56 m |
| `gift_box.n.01_3` | gift_box_219 | gift_box / mfalrc | living_room_0 | floor, z 0.08 | 2.82 m (range 0.77-6.68) | yes, spread 8.29 m |
| `wicker_basket.n.01_1` | wicker_basket_218 | wicker_basket / dgkhyn | living_room_0 | floor, z 0.09 | 2.65 m (range 1.15-6.9) | yes, spread 8.63 m |
| `floor.n.01_1` | floors_uzsntg_0 | floors / uzsntg | living_room_0 | floor, z -0.14 | 2.46 m (range 0.53-4.07) | no (fixed) |
| `table.n.02_1` | breakfast_table_rhjoby_0 | breakfast_table / rhjoby | dining_room_0 | table/counter (0.6-1.1 m), z 0.76 | 7.16 m (range 2.7-9.46) | no |
| `sofa.n.01_1` | sofa_lugrhk_1 | sofa / lugrhk | living_room_0 | low (0.25-0.6 m), z 0.27 | 3.49 m (range 1.97-6.17) | no (fixed) |
| `sofa.n.01_2` | sofa_hiphpn_0 | sofa / hiphpn | living_room_0 | floor, z 0.25 | 3.71 m (range 1.29-6.33) | no (fixed) |
| `sofa.n.01_3` | sofa_wnzdke_0 | sofa / wnzdke | living_room_0 | low (0.25-0.6 m), z 0.3 | 4.46 m (range 3.54-7.05) | no (fixed) |
| `sofa.n.01_4` | sofa_lugrhk_0 | sofa / lugrhk | living_room_0 | low (0.25-0.6 m), z 0.27 | 4.08 m (range 2.09-5.77) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom sofa.n.01_1 living_room)
(inroom sofa.n.01_2 living_room)
(inroom sofa.n.01_3 living_room)
(inroom sofa.n.01_4 living_room)
(inroom table.n.02_1 dining_room)
(inside candy_cane.n.01_1 wicker_basket.n.01_1)
(inside candy_cane.n.01_2 wicker_basket.n.01_1)
(inside candy_cane.n.01_3 wicker_basket.n.01_1)
(inside pillar_candle.n.01_1 wicker_basket.n.01_1)
(inside pillar_candle.n.01_2 wicker_basket.n.01_1)
(inside wreath.n.01_1 wicker_basket.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop christmas_tree.n.05_1 floor.n.01_1)
(ontop gift_box.n.01_1 floor.n.01_1)
(ontop gift_box.n.01_2 floor.n.01_1)
(ontop gift_box.n.01_3 floor.n.01_1)
(ontop wicker_basket.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching christmas_tree.n.05_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 christmas_tree.n.05_1)
(touching floor.n.01_1 gift_box.n.01_1)
(touching floor.n.01_1 gift_box.n.01_2)
(touching floor.n.01_1 gift_box.n.01_3)
(touching floor.n.01_1 wicker_basket.n.01_1)
(touching gift_box.n.01_1 floor.n.01_1)
(touching gift_box.n.01_2 floor.n.01_1)
(touching gift_box.n.01_3 floor.n.01_1)
(touching wicker_basket.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 444.25 s (range 323.0-660.8). Skills per demo 32.0 (range 23-34). 29 distinct skill orders; the most common one covers 52% of demos.

Most common skill counts per demo (55% of demos): move to x15, pick up from x7, place on x4, place on next to x3, push to x2, pour x1.

Representative demo `episode_00092630.json` (456.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wicker basket` (1.0-10.6 s)
2. `pick up the wicker basket from the floors` (10.6-26.1 s)
3. `move to the sofa` (26.1-57.4 s)
4. `pour the candy cane and candy cane and candy cane and pillar candle and pillar candle and wreath into the wicker basket` (57.4-85.5 s)
5. `move to the coffee table` (85.5-91.1 s)
6. `place the wicker basket on the coffee table` (91.1-100.4 s)
7. `move to the candy cane` (100.4-111.4 s)
8. `pick up the candy cane from the sofa` (111.4-147.8 s)
9. `move to the breakfast table` (147.8-158.4 s)
10. `place the candy cane on the breakfast table` (158.4-165.8 s)
11. `move to the pillar candle` (165.8-177.4 s)
12. `pick up the pillar candle from the sofa` (177.4-213.0 s)
13. `move to the breakfast table` (213.0-227.3 s)
14. `place the pillar candle on the breakfast table` (227.3-239.9 s)
15. `move to the pillar candle` (240.0-249.6 s)
16. `pick up the pillar candle from the sofa` (249.6-280.2 s)
17. `move to the breakfast table` (280.2-293.3 s)
18. `place the pillar candle on the breakfast table` (293.3-304.0 s)
19. `move to the gift box` (304.0-332.5 s)
20. `pick up the gift box from the floors` (332.5-348.9 s)
21. `move to the christmas tree` (348.9-361.3 s)
22. `place the gift box on the floors next to the in_front_of christmas tree` (361.3-367.6 s)
23. `push the gift box to the center christmas tree` (367.6-376.5 s)
24. `move to the gift box` (376.5-382.6 s)
25. `pick up the gift box from the floors` (382.6-390.3 s)
26. `move to the christmas tree` (390.3-394.0 s)
27. `place the gift box on the floors next to the in_front_of christmas tree` (394.0-403.0 s)
28. `push the gift box to the center christmas tree` (403.0-410.4 s)
29. `move to the gift box` (410.4-425.1 s)
30. `pick up the gift box from the floors` (425.1-432.8 s)
31. `move to the christmas tree` (432.8-447.0 s)
32. `place the gift box on the floors next to the in_front_of christmas tree` (447.0-457.8 s)

Mean duration per skill in this task: move to 14.1 s, pick up from 18.2 s, place on 13.5 s, place on next to 9.2 s, pour 23.4 s, push to 8.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the breakfast table` | 600 |
| `move to the gift box` | 579 |
| `pick up the gift box from the floors` | 571 |
| `place the gift box on the floors next to the in_front_of christmas tree` | 571 |
| `move to the christmas tree` | 568 |
| `push the gift box to the center christmas tree` | 404 |
| `pick up the pillar candle from the sofa` | 400 |
| `place the pillar candle on the breakfast table` | 400 |
| `move to the pillar candle` | 394 |
| `pick up the wicker basket from the floors` | 200 |
| `move to the sofa` | 200 |
| `move to the coffee table` | 200 |
| `place the wicker basket on the coffee table` | 200 |
| `pick up the candy cane from the sofa` | 200 |
| `place the candy cane on the breakfast table` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/09_putting_up_Christmas_decorations_inside.json`. Planner notes: `task_docs/notes/09_putting_up_Christmas_decorations_inside.md`.
