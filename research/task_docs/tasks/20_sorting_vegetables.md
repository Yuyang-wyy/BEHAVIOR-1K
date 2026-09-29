# 20 · Sorting Vegetables

Task name `sorting_vegetables`, task index 20.

> Sort the vegetables from the two wicker baskets on the kitchen floor into the mixing bowls on the kitchen countertop: put all three bok choy and all three Vidalia onions together into one mixing bowl; put both leeks and both broccoli together into a second mixing bowl; and put all three sweet corn into a third mixing bowl.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 396.8 s mean (11903 steps) |
| episode time limit | 595.2 s (17855 steps at 30 Hz) |
| human base travel | 33.9547 m |
| goal literals (best ground option) | 13 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 27 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.31; ft40k@sulab1 Q=0.23; ft40k@local Q=0.23 |
| demo video | https://player.vimeo.com/video/1114058741 |

## Planner notes

**Tier:** B — 13 vegetables go from two floor baskets into bowls on one countertop, all within ~4 m. Several are wider than the 44 mm span (onion 0.07 m, sweet corn 0.057 m, broccoli 0.06 m, bok choy 0.10 m); the leeks (0.038 m) fit.

### Goal in plain words

All 3 bok choy and all 3 onions must share one mixing bowl.
Both leeks and both broccoli must share one mixing bowl.
All 3 sweet corn must share one mixing bowl.
Each of the three groups picks its bowl independently (`exists` per group), so the groups do NOT have to use different bowls. The three bowls are identical and interchangeable.

### Q traps

- 13 literals, all False at reset (every vegetable starts in a wicker basket on the floor). Each vegetable is worth 1/13.
- 27 ground options: every assignment of the three groups to the three bowls, including all three groups in one bowl. Q takes the best option, so the planner does not need to track which bowl got which group, only keep each group's members together.
- Splitting a group across two bowls loses the minority: e.g. 2 onions in bowl A and 1 in bowl B scores only the 2 in the best option.
- `inside` needs each vegetable's AABB centre in the bowl's volume (PREDICATES §3). A vegetable resting on top of a heap above the rim does not count. A bowl is 0.36 x 0.32 x 0.17 m; putting all 13 in one bowl will overflow. Use the three bowls, one group each.
- A vegetable dropped on the counter or floor scores 0.

### Minimal plan

The two baskets are on the kitchen floor, 0.7-4 m from the start; the bowls are on `countertop_kelzer_0` at 0.96 m. `wicker_basket_220` holds broccoli, leeks and onions; `wicker_basket_221` holds bok choy and sweet corn.

1. `move to the wicker basket`, `pick up the wicker basket from the floors` — basket lifted off the floor. ~13 s + 12 s.
2. `move to the mixing bowl` — base at the countertop with the bowls in view. ~13 s.
3. From basket 220: `pick up the broccoli from the wicker basket`, `place the broccoli in the mixing bowl` (x2), then `pick up the leek from the wicker basket`, `place the leek in the mixing bowl` (x2), all into the same bowl. ~12 s + 4 s each.
4. `pick up the vidalia onion from the wicker basket`, `place the vidalia onion in the mixing bowl` (x3) into a second bowl. ~16 s each.
5. `place the wicker basket on the floors`. ~18 s.
6. Repeat step 1 for the other basket. Then `pick up the bok choy from the wicker basket`, `place the bok choy in the mixing bowl` (x3) into the onion bowl.
7. `pick up the sweet corn from the wicker basket`, `place the sweet corn in the mixing bowl` (x3) into the third bowl.
8. `place the wicker basket on the floors` — optional; no literal needs it. Skip it if time is short.

Budget: about 350 s against a 595 s limit. Placing the basket back on the floor (steps 5 and 8) is only needed to free the hand for the next basket.

### What the demos do differently

- Every demo carries a basket to the counter and sorts from it while holding it. Order of baskets and bowls varies; no two demos share a non-move sequence.
- Humans always put bok choy with onions and leeks with broccoli, as the goal requires, and use three different bowls.
- Both baskets go back to the floor at the end in all demos; that is not required.

### Hard parts and hacks

- Grasp span: leeks (0.038 m) fit easily. Onions (0.07 m), corn (0.057 m round), broccoli (0.06 m) and bok choy (0.10 m) are wider than 44 mm; graspable only on a narrower part (stem, leaf tip, cob end), unverified.
- Holding a basket in one hand while picking with the other: the basket is 0.30 x 0.45 x 0.19 m with no handle link. If carrying the basket fails, walking to the basket on the floor for each vegetable costs ~13 s per extra move.
- Bowl capacity: 3 bok choy (0.17 m each) plus 3 onions in one 0.36 m bowl is tight. Place the bok choy first, flat, then the onions.

### Hints for the VLM

- The bowls are the three identical mixing bowls on the long kitchen countertop. The kitchen also has one other countertop, a sink, a microwave, an oven and a fridge; there are no other bowls or baskets.
- The baskets are woven wicker baskets on the floor. Basket 220 has the green broccoli, long leeks and pale onions; basket 221 has bok choy and yellow corn cobs.
- Done for a group: every member visibly below the rim of the same bowl.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside bok_choy.n.02_1 mixing_bowl.n.01_3)` | no | yes |
| `(inside bok_choy.n.02_2 mixing_bowl.n.01_3)` | no | yes |
| `(inside bok_choy.n.02_3 mixing_bowl.n.01_3)` | no | yes |
| `(inside vidalia_onion.n.01_1 mixing_bowl.n.01_3)` | no | yes |
| `(inside vidalia_onion.n.01_2 mixing_bowl.n.01_3)` | no | yes |
| `(inside vidalia_onion.n.01_3 mixing_bowl.n.01_3)` | no | yes |
| `(inside leek.n.02_2 mixing_bowl.n.01_3)` | no | yes |
| `(inside leek.n.02_1 mixing_bowl.n.01_3)` | no | yes |
| `(inside broccoli.n.02_1 mixing_bowl.n.01_3)` | no | yes |
| `(inside broccoli.n.02_2 mixing_bowl.n.01_3)` | no | yes |
| `(inside sweet_corn.n.02_2 mixing_bowl.n.01_3)` | no | yes |
| `(inside sweet_corn.n.02_1 mixing_bowl.n.01_3)` | no | yes |
| `(inside sweet_corn.n.02_3 mixing_bowl.n.01_3)` | no | yes |

The goal has 27 ground options (13 literals x27); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists 
                (?mixing_bowl.n.01 - mixing_bowl.n.01)
                (and 
                    (forall 
                        (?bok_choy.n.02 - bok_choy.n.02)
                        (inside ?bok_choy.n.02 ?mixing_bowl.n.01)
                    )
                    (forall 
                        (?vidalia_onion.n.01 - vidalia_onion.n.01)
                        (inside ?vidalia_onion.n.01 ?mixing_bowl.n.01)
                    )
                )
            )
            (exists 
                (?mixing_bowl.n.01 - mixing_bowl.n.01)
                (and 
                    (forall 
                        (?leek.n.02 - leek.n.02)
                        (inside ?leek.n.02 ?mixing_bowl.n.01)
                    )
                    (forall 
                        (?broccoli.n.02 - broccoli.n.02)
                        (inside ?broccoli.n.02 ?mixing_bowl.n.01)
                    )
                )
            )
            (exists 
                (?mixing_bowl.n.01 - mixing_bowl.n.01)
                (and 
                    (forall 
                        (?sweet_corn.n.02 - sweet_corn.n.02)
                        (inside ?sweet_corn.n.02 ?mixing_bowl.n.01)
                    )
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
| `mixing_bowl.n.01_1` | mixing_bowl_224 | mixing_bowl / bsgybx | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 1.91 m (range 0.97-3.52) | yes, spread 2.59 m |
| `mixing_bowl.n.01_2` | mixing_bowl_223 | mixing_bowl / bsgybx | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 2.11 m (range 1.03-3.55) | yes, spread 0.66 m |
| `mixing_bowl.n.01_3` | mixing_bowl_222 | mixing_bowl / bsgybx | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 1.97 m (range 0.92-3.78) | yes, spread 2.62 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.62 m (range 1.17-3.59) | no (fixed) |
| `wicker_basket.n.01_1` | wicker_basket_221 | wicker_basket / dgkhyn | kitchen_0 | floor, z 0.09 | 2.44 m (range 0.69-3.84) | yes, spread 4.86 m |
| `wicker_basket.n.01_2` | wicker_basket_220 | wicker_basket / dgkhyn | kitchen_0 | floor, z 0.09 | 2.17 m (range 0.71-4.0) | yes, spread 5.57 m |
| `bok_choy.n.02_1` | bok_choy_219 | bok_choy / bbvcji | kitchen_0 | floor, z 0.07 | 2.52 m (range 0.7-3.84) | yes, spread 4.92 m |
| `bok_choy.n.02_2` | bok_choy_218 | bok_choy / bbvcji | kitchen_0 | floor, z 0.06 | 2.44 m (range 0.7-3.95) | yes, spread 5.0 m |
| `bok_choy.n.02_3` | bok_choy_217 | bok_choy / bbvcji | kitchen_0 | floor, z 0.09 | 2.39 m (range 0.78-3.86) | yes, spread 4.92 m |
| `vidalia_onion.n.01_1` | vidalia_onion_216 | vidalia_onion / buyxll | kitchen_0 | floor, z 0.07 | 2.15 m (range 0.65-4.09) | yes, spread 5.55 m |
| `vidalia_onion.n.01_2` | vidalia_onion_215 | vidalia_onion / buyxll | kitchen_0 | floor, z 0.05 | 2.21 m (range 0.65-3.92) | yes, spread 5.39 m |
| `vidalia_onion.n.01_3` | vidalia_onion_214 | vidalia_onion / buyxll | kitchen_0 | floor, z 0.09 | 2.06 m (range 0.68-4.01) | yes, spread 5.65 m |
| `sweet_corn.n.02_1` | sweet_corn_213 | sweet_corn / qtesku | kitchen_0 | floor, z 0.13 | 2.46 m (range 0.67-3.76) | yes, spread 4.83 m |
| `sweet_corn.n.02_2` | sweet_corn_212 | sweet_corn / qtesku | kitchen_0 | floor, z 0.05 | 2.41 m (range 0.63-3.82) | yes, spread 4.86 m |
| `sweet_corn.n.02_3` | sweet_corn_211 | sweet_corn / qtesku | kitchen_0 | floor, z 0.14 | 2.46 m (range 0.69-3.91) | yes, spread 4.92 m |
| `broccoli.n.02_1` | broccoli_210 | broccoli / wsxavx | kitchen_0 | floor, z 0.08 | 2.12 m (range 0.67-4.05) | yes, spread 5.72 m |
| `broccoli.n.02_2` | broccoli_209 | broccoli / wsxavx | kitchen_0 | floor, z 0.05 | 2.13 m (range 0.63-3.95) | yes, spread 5.78 m |
| `leek.n.02_1` | leek_208 | leek / fyihsq | kitchen_0 | floor, z 0.04 | 2.18 m (range 0.72-4.05) | yes, spread 5.57 m |
| `leek.n.02_2` | leek_207 | leek / fyihsq | kitchen_0 | floor, z 0.07 | 2.17 m (range 0.76-3.99) | yes, spread 5.57 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.41 m (range 0.67-2.36) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside bok_choy.n.02_1 wicker_basket.n.01_1)
(inside bok_choy.n.02_2 wicker_basket.n.01_1)
(inside bok_choy.n.02_3 wicker_basket.n.01_1)
(inside broccoli.n.02_1 wicker_basket.n.01_2)
(inside broccoli.n.02_2 wicker_basket.n.01_2)
(inside leek.n.02_1 wicker_basket.n.01_2)
(inside leek.n.02_2 wicker_basket.n.01_2)
(inside sweet_corn.n.02_1 wicker_basket.n.01_1)
(inside sweet_corn.n.02_2 wicker_basket.n.01_1)
(inside sweet_corn.n.02_3 wicker_basket.n.01_1)
(inside vidalia_onion.n.01_1 wicker_basket.n.01_2)
(inside vidalia_onion.n.01_2 wicker_basket.n.01_2)
(inside vidalia_onion.n.01_3 wicker_basket.n.01_2)
(ontop agent.n.01_1 floor.n.01_1)
(ontop mixing_bowl.n.01_1 countertop.n.01_1)
(ontop mixing_bowl.n.01_2 countertop.n.01_1)
(ontop mixing_bowl.n.01_3 countertop.n.01_1)
(ontop wicker_basket.n.01_1 floor.n.01_1)
(ontop wicker_basket.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 mixing_bowl.n.01_1)
(touching countertop.n.01_1 mixing_bowl.n.01_2)
(touching countertop.n.01_1 mixing_bowl.n.01_3)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 wicker_basket.n.01_1)
(touching floor.n.01_1 wicker_basket.n.01_2)
(touching mixing_bowl.n.01_1 countertop.n.01_1)
(touching mixing_bowl.n.01_2 countertop.n.01_1)
(touching mixing_bowl.n.01_3 countertop.n.01_1)
(touching wicker_basket.n.01_1 floor.n.01_1)
(touching wicker_basket.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 386.25 s (range 207.0-642.7). Skills per demo 41.0 (range 36-47). 195 distinct skill orders; the most common one covers 2% of demos.

Most common skill counts per demo (14% of demos): pick up from x15, place in x13, move to x10, place on x2.

Representative demo `episode_00200530.json` (346.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wicker basket` (0.0-9.0 s)
2. `pick up the wicker basket from the floors` (9.0-34.9 s)
3. `move to the mixing bowl` (34.9-39.0 s)
4. `pick up the broccoli from the wicker basket` (39.0-49.7 s)
5. `place the broccoli in the mixing bowl` (49.8-55.8 s)
6. `pick up the broccoli from the wicker basket` (55.9-66.8 s)
7. `place the broccoli in the mixing bowl` (66.8-70.0 s)
8. `pick up the leek from the wicker basket` (70.0-82.7 s)
9. `place the leek in the mixing bowl` (82.7-86.1 s)
10. `pick up the leek from the wicker basket` (86.1-103.2 s)
11. `place the leek in the mixing bowl` (103.2-107.6 s)
12. `move to the mixing bowl` (107.6-114.8 s)
13. `pick up the vidalia onion from the wicker basket` (114.9-124.1 s)
14. `place the vidalia onion in the mixing bowl` (124.1-127.1 s)
15. `pick up the vidalia onion from the wicker basket` (127.1-134.1 s)
16. `place the vidalia onion in the mixing bowl` (134.1-136.6 s)
17. `pick up the vidalia onion from the wicker basket` (136.6-143.7 s)
18. `place the vidalia onion in the mixing bowl` (143.7-147.9 s)
19. `place the wicker basket on the floors` (147.9-166.9 s)
20. `move to the wicker basket` (166.9-182.7 s)
21. `pick up the wicker basket from the floors` (182.7-201.0 s)
22. `move to the mixing bowl` (201.0-243.7 s)
23. `pick up the bok choy from the wicker basket` (226.8-241.5 s)
24. `place the bok choy in the mixing bowl` (243.7-245.0 s)
25. `pick up the bok choy from the wicker basket` (245.0-255.6 s)
26. `place the bok choy in the mixing bowl` (255.6-258.5 s)
27. `pick up the bok choy from the wicker basket` (258.5-269.0 s)
28. `place the bok choy in the mixing bowl` (269.0-272.9 s)
29. `pick up the sweet corn from the wicker basket` (272.9-289.3 s)
30. `move to the mixing bowl` (289.3-293.7 s)
31. `place the sweet corn in the mixing bowl` (293.7-295.6 s)
32. `pick up the sweet corn from the wicker basket` (295.6-306.8 s)
33. `place the sweet corn in the mixing bowl` (306.8-310.7 s)
34. `pick up the sweet corn from the wicker basket` (310.7-323.7 s)
35. `place the sweet corn in the mixing bowl` (323.7-329.0 s)
36. `place the wicker basket on the floors` (329.0-346.7 s)

Mean duration per skill in this task: move to 12.8 s, pick up from 11.8 s, place in 4.2 s, place on 17.8 s, push to 10.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the mixing bowl` | 1630 |
| `place the vidalia onion in the mixing bowl` | 600 |
| `pick up the bok choy from the wicker basket` | 600 |
| `place the bok choy in the mixing bowl` | 600 |
| `pick up the vidalia onion from the wicker basket` | 599 |
| `pick up the sweet corn from the wicker basket` | 599 |
| `place the sweet corn in the mixing bowl` | 598 |
| `pick up the wicker basket from the floors` | 401 |
| `place the wicker basket on the floors` | 401 |
| `pick up the leek from the wicker basket` | 400 |
| `place the leek in the mixing bowl` | 400 |
| `place the broccoli in the mixing bowl` | 400 |
| `pick up the broccoli from the wicker basket` | 399 |
| `move to the wicker basket` | 398 |
| `move to the floors` | 177 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/20_sorting_vegetables.json`. Planner notes: `task_docs/notes/20_sorting_vegetables.md`.
