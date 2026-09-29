# 48 · Canning Food

Task name `canning_food`, task index 48.

> In the kitchen, open the refrigerator and the cabinet. Take the steak and the pineapple out of the refrigerator and take two bowls from the cabinet. On the chopping board on the countertop, use the carving knife to dice the steak and to dice the pineapple. Put only the diced steak into one bowl and only the diced pineapple into the other bowl - do not mix them. Place both bowls back inside the cabinet, then close the refrigerator and close the cabinet.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 765.8 s mean (22975 steps) |
| episode time limit | 1148.8 s (34463 steps at 30 Hz) |
| human base travel | 64.4919 m |
| goal literals (best ground option) | 10 |
| literals already true at start (inferred) | 6 |
| max Q short of full success | 0.4 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114061821 |

## Planner notes

**Tier:** D — two slice-then-dice transitions, two particle transfers that must fill each bowl past 20 %, and container round trips through a tall cabinet and the fridge.

### Goal in plain words

- Steak and pineapple must both be diced. **Tool:** the carving knife `carving_knife_207`, the only slicer, which starts on the cutting board.
- One bowl must be `filled` with diced steak and hold zero diced pineapple. The other bowl must be `filled` with diced pineapple and hold zero diced steak. Either bowl can take either food (4 ground options).
- Both bowls must end inside `bottom_cabinet_fancyy_0`, and the cabinet and the fridge must both be closed.

**Containers:** the two bowls `bowl_209` and `bowl_210` (`belcml`, 255 x 255 x 150 mm). There is no heat source. The board is just a work surface.

### Q traps

- 10 literals, and **6 are true at start**: both `inside bowl cabinet`, both `not contains` (the diced systems do not exist yet, so the argument is `None` and `contains` is False, §0/§13), `not open fridge`, and `not open cabinet`. Max partial Q is 4/10 = 0.4 (page is right).
- The 4 scoring literals are the two `real diced__X` and the two `filled`. Dicing both foods anywhere, even inside the fridge, is worth 0.2 with no object moved except the knife.
- **`filled` is the hard part.** It needs the particle cube volume, (2r)^3 × n, to exceed 20 % of the bowl's fillable volume (§13). Dicing samples particles on a 2r grid inside the half's volume (`DicingRule`, `transition_rules.py:1022-1032`), so the particle volume is roughly the food volume. The steak's bbox is only 1.2 L (130 x 190 x 50 mm), and the bowl is a large 255 x 150 mm bowl. Filling the steak bowl therefore needs **both** steak halves diced and nearly every piece poured in. It may be unreachable. The bowl volume and particle radius are not verified.
- **Cross-contamination.** One stray pineapple piece in the steak bowl (or the reverse) breaks that bowl's `not contains` (§13). Use a different pour target for each, and do not pour over a bowl that already holds the other food.
- For success everything must hold at the end: the bowls back in the cabinet with their pieces still in them, and both doors shut. `bottom_cabinet_fancyy` has no `openable_joint_ids`, so **all 3 of its joints** count toward `open` (`open_state.py:96` fallback, §6).

### Minimal plan

1. `move to the fridge`, `open the door of the fridge`, `pick up the steak from the high_level fridge`, `pick up the pineapple from the low_level fridge` (shelf words vary) — ~11 + 26 + 12 + 12 s.
2. `close the door of the fridge` — ~25 s.
3. `move to the cutting board`, `place the steak on the cutting board`, `place the pineapple on the countertop` — ~11 + 6 + 6 s.
4. `pick up the carving knife from the countertop` (at the start it lies on the board: `pick up the carving knife from the cutting board`) — ~12 s.
5. `chop the carving knife with the steak`, wait 2 s, `chop the carving knife with the half steak 212`, wait 2 s, `chop the carving knife with the half steak 212` — **dice both halves**. ~4 s each.
6. `place the carving knife on the countertop next to the right cutting board` — ~8 s.
7. `move to the bottom cabinet`, `open the door of the left_door bottom cabinet`, `pick up the bowl from the layer_2 bottom cabinet` — ~11 + 26 + 12 s. Leave that door open for now.
8. `move to the countertop`, `place the bowl on the countertop next to the right drop in sink` (or anywhere near the board), `pick up the cutting board from the countertop`, `pour the diced  steak into the cutting board` (sic, double space; board into bowl) — ~11 + 8 + 12 + 13 s.
9. `pick up the bowl from the countertop`, `move to the bottom cabinet`, `place the bowl in the layer_4 bottom cabinet` — ~12 + 11 + 13 s.
10. Repeat steps 3-9 for the pineapple with the second bowl, using `place the pineapple on the cutting board`, `chop the carving knife with the pineapple`, `chop the carving knife with the half pineapple 211` (twice), and `pour the diced  pineapple into the cutting board`.
11. `close the door of the left_door bottom cabinet` — every cabinet door flush. ~25 s.

The plan takes about 600-700 s against a 1149 s limit.

### What the demos do differently

- They move the board onto the sink before pouring (`place the cutting board on the drop in sink`, 771 segments). This probably keeps spilled pieces out of the bowl area; it is not required.
- They put the empty bowl in the sink as a stable pour target (`place the bowl in the drop in sink`). The sink's `particleSink` removes physical particles that reach its drain (KB `default_non_fluid_conditions: []`). Pour into the bowl, not near the drain.
- The pineapple half is often moved off the board and diced separately, with two pours. Both pineapple halves are diced.
- 69 steps and ~950 s in the representative demo, so the humans used most of the time budget.

### Hard parts and hacks

- **Grasp span.** The steak is 130 x 190 x 50 mm and the pineapple 279 x 115 x 110 mm. Neither fits the 44 mm span, and neither do their halves (steak halves ~110 x 125 x 47 mm, pineapple halves ~111 x 111 x 214 mm and 104 x 107 x 67 mm). The realistic grasp-free gain is to **dice both foods where they lie in the fridge** (0.2), then close the fridge.
- **Bowls.** The bowls (255 mm across) can only be held by the rim. They sit on cabinet shelves at z 0.55-1.55 in a tall pantry cabinet (1.97 m) next to the fridge.
- **Knife.** `usqmjc` is 318 x 72 x 16 mm, and the handle width is not verified.
- **Pour aim.** The board is a flat 350 x 250 mm plank with no rim, so pieces slide off during the carry. Carry it level and pour at close range.

### Hints for the VLM

- Kitchen of `house_single_floor`. From left to right along the y ≈ -2 wall: sink (x 5.8), dishwasher, fridge (x 7.8), then the tall pantry cabinet `bottom_cabinet_fancyy_0` at x ≈ 8.7, which also houses the wall oven. The board and knife are on `countertop_kelzer_0` on the same wall.
- The steak is a flat brown-red slab and the pineapple is a tall yellow-green fruit, both in the fridge. There are two identical bowls in the pantry cabinet.
- Done: two bowls on pantry shelves, one visibly heaped with red cubes, one with yellow cubes, and all doors flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real diced__steak.n.01_1)` | no | yes |
| `(real diced__pineapple.n.01_1)` | no | yes |
| `(filled bowl.n.01_1 diced__steak.n.01_1)` | no | yes |
| `(not contains bowl.n.01_1 diced__pineapple.n.01_1))` | yes | never (already true) |
| `(filled bowl.n.01_1 diced__pineapple.n.01_1)` | no | yes |
| `(not contains bowl.n.01_1 diced__steak.n.01_1))` | yes | never (already true) |
| `(inside bowl.n.01_1 cabinet.n.01_1)` | yes | never (already true) |
| `(inside bowl.n.01_2 cabinet.n.01_1)` | yes | never (already true) |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |
| `(not open cabinet.n.01_1))` | yes | never (already true) |

The goal has 4 ground options (10 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?diced__steak.n.01_1)
            (real ?diced__pineapple.n.01_1)
            (exists
                (?bowl.n.01 - bowl.n.01)
                (and 
                    (filled ?bowl.n.01 ?diced__steak.n.01_1)
                    (not
                        (contains ?bowl.n.01 ?diced__pineapple.n.01_1)
                    )
                )
            )
            (exists
                (?bowl.n.01 - bowl.n.01)
                (and 
                    (filled ?bowl.n.01 ?diced__pineapple.n.01_1)
                    (not
                        (contains ?bowl.n.01 ?diced__steak.n.01_1)
                    )
                )
            )
            (forall 
                (?bowl.n.01 - bowl.n.01) 
                (and
                    (inside ?bowl.n.01 ?cabinet.n.01_1)
                )
            ) 
            (not 
                (open ?electric_refrigerator.n.01_1)
            )
            (not
                (open ?cabinet.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `steak.n.01_1` | steak_212 | steak / ppykkp | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.64 m (range 0.87-4.27) | yes, spread 0.32 m |
| `diced__steak.n.01_1` | particle system | diced__steak | - | - | - | - |
| `pineapple.n.02_1` | pineapple_211 | pineapple / wfaybl | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.53 m (range 0.93-4.36) | yes, spread 0.29 m |
| `diced__pineapple.n.01_1` | particle system | diced__pineapple | - | - | - | - |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.56 m (range 0.94-4.31) | no (fixed) |
| `bowl.n.01_1` | bowl_210 | bowl / belcml | kitchen_0 | table/counter (0.6-1.1 m), z 0.62 | 3.47 m (range 1.05-5.12) | yes, spread 0.95 m |
| `bowl.n.01_2` | bowl_209 | bowl / belcml | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.69 m (range 0.95-5.24) | yes, spread 0.92 m |
| `cabinet.n.01_1` | bottom_cabinet_fancyy_0 | bottom_cabinet / fancyy | kitchen_0 | high (1.1-1.6 m), z 1.12 | 3.42 m (range 1.07-4.91) | no (fixed) |
| `chopping_board.n.01_1` | cutting_board_208 | cutting_board / aibvew | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.86 m (range 0.84-3.83) | yes, spread 2.68 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.98 m (range 1.09-3.57) | no (fixed) |
| `carving_knife.n.01_1` | carving_knife_207 | carving_knife / usqmjc | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 1.84 m (range 0.85-3.86) | yes, spread 2.71 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.49 m (range 0.76-2.44) | no (fixed) |

Initial conditions from `:init`:

```lisp
(future diced__pineapple.n.01_1)
(future diced__steak.n.01_1)
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside bowl.n.01_1 cabinet.n.01_1)
(inside bowl.n.01_2 cabinet.n.01_1)
(inside pineapple.n.02_1 electric_refrigerator.n.01_1)
(inside steak.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop carving_knife.n.01_1 chopping_board.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching carving_knife.n.01_1 chopping_board.n.01_1)
(touching chopping_board.n.01_1 carving_knife.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 743.93 s (range 505.9-1282.9). Skills per demo 67.5 (range 59-73). 164 distinct skill orders; the most common one covers 3% of demos.

Most common skill counts per demo (10% of demos): pick up from x18, move to x17, place on x9, chop x6, place on next to x5, place in x4, close door x3, open door x3, pour x3.

Representative demo `episode_00481460.json` (953.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the carving knife` (0.0-2.7 s)
2. `pick up the carving knife from the cutting board` (2.7-15.5 s)
3. `pick up the cutting board from the countertop` (15.5-29.4 s)
4. `move to the drop in sink` (29.4-32.2 s)
5. `place the cutting board on the drop in sink` (32.2-50.6 s)
6. `place the carving knife on the countertop next to the right cutting board` (50.6-62.3 s)
7. `move to the fridge` (62.3-81.9 s)
8. `open the door of the fridge` (82.0-125.6 s)
9. `pick up the steak from the high_level fridge` (125.6-155.7 s)
10. `pick up the pineapple from the low_level fridge` (155.7-201.5 s)
11. `close the door of the fridge` (201.5-241.3 s)
12. `move to the cutting board` (241.3-261.8 s)
13. `place the steak on the cutting board` (261.8-269.8 s)
14. `place the pineapple on the countertop` (269.8-278.3 s)
15. `move to the carving knife` (278.3-279.8 s)
16. `pick up the carving knife from the countertop` (279.8-287.0 s)
17. `move to the steak` (287.0-288.8 s)
18. `chop the carving knife with the steak` (288.8-291.6 s)
19. `chop the carving knife with the half steak 212` (291.6-293.9 s)
20. `chop the carving knife with the half steak 212` (293.9-296.8 s)
21. `place the carving knife on the countertop next to the right cutting board` (296.8-306.5 s)
22. `move to the bottom cabinet` (306.5-331.8 s)
23. `open the door of the left_door bottom cabinet` (331.8-358.9 s)
24. `pick up the bowl from the layer_2 bottom cabinet` (358.9-387.5 s)
25. `pick up the bowl from the layer_4 bottom cabinet` (387.5-416.4 s)
26. `close the door of the left_door bottom cabinet` (416.4-454.1 s)
27. `move to the countertop` (454.1-488.5 s)
28. `place the bowl on the countertop next to the right drop in sink` (488.5-501.2 s)
29. `place the bowl in the drop in sink` (501.2-515.8 s)
30. `move to the cutting board` (515.8-518.1 s)
31. `pick up the cutting board from the drop in sink` (518.1-530.8 s)
32. `pour the diced  steak into the cutting board` (530.8-543.4 s)
33. `place the cutting board on the drop in sink` (543.4-548.8 s)
34. `move to the bowl` (548.8-551.8 s)
35. `pick up the bowl from the drop in sink` (551.8-559.5 s)
36. `move to the bottom cabinet` (559.5-586.8 s)
37. `open the door of the left_door bottom cabinet` (586.8-614.6 s)
38. `place the bowl in the layer_4 bottom cabinet` (614.6-638.7 s)
39. `move to the pineapple` (638.7-660.6 s)
40. `pick up the pineapple from the countertop` (660.6-674.4 s)
41. `move to the cutting board` (674.4-677.7 s)
42. `place the pineapple on the cutting board` (677.7-689.7 s)
43. `move to the carving knife` (689.7-691.6 s)
44. `pick up the carving knife from the countertop` (691.6-696.5 s)
45. `chop the carving knife with the pineapple` (696.5-703.4 s)
46. `pick up the half pineapple 211 from the cutting board` (703.4-710.4 s)
47. `place the half pineapple 211 on the countertop` (710.4-715.9 s)
48. `chop the carving knife with the half pineapple 211` (715.9-719.5 s)
49. `place the carving knife on the countertop next to the right cutting board` (719.5-726.6 s)
50. `pick up the bowl from the countertop` (726.6-733.0 s)
51. `place the bowl in the drop in sink` (733.0-745.5 s)
52. `move to the cutting board` (745.5-746.2 s)
53. `pick up the cutting board from the drop in sink` (746.2-762.8 s)
54. `pour the diced  pineapple into the cutting board` (762.8-801.3 s)
55. `place the cutting board on the drop in sink` (801.3-806.8 s)
56. `pick up the half pineapple 211 from the countertop` (806.8-812.0 s)
57. `place the half pineapple 211 on the cutting board` (812.0-818.7 s)
58. `move to the carving knife` (818.7-820.8 s)
59. `pick up the carving knife from the countertop` (820.8-828.7 s)
60. `chop the carving knife with the half pineapple 211` (828.7-832.3 s)
61. `place the carving knife on the countertop next to the right cutting board` (832.3-839.7 s)
62. `move to the cutting board` (839.7-840.9 s)
63. `pick up the cutting board from the drop in sink` (840.9-854.5 s)
64. `pour the diced  pineapple into the cutting board` (854.5-871.4 s)
65. `place the cutting board on the drop in sink` (871.4-883.5 s)
66. `pick up the bowl from the drop in sink` (883.5-898.2 s)
67. `move to the bottom cabinet` (898.2-916.6 s)
68. `place the bowl in the layer_3 bottom cabinet` (916.6-937.6 s)
69. `close the door of the left_door bottom cabinet` (937.6-953.6 s)

Mean duration per skill in this task: chop 3.5 s, close door 25.3 s, move to 10.8 s, open door 26.1 s, pick up from 12.3 s, place in 13.2 s, place on 6.3 s, place on next to 7.7 s, pour 13.3 s, push to 11.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the carving knife on the countertop next to the right cutting board` | 772 |
| `place the cutting board on the drop in sink` | 771 |
| `pick up the carving knife from the countertop` | 600 |
| `move to the bottom cabinet` | 600 |
| `pick up the cutting board from the drop in sink` | 596 |
| `move to the cutting board` | 581 |
| `move to the carving knife` | 516 |
| `pick up the bowl from the drop in sink` | 400 |
| `chop the carving knife with the half pineapple 211` | 400 |
| `pour the diced  pineapple into the cutting board` | 400 |
| `place the bowl in the drop in sink` | 399 |
| `open the door of the left_door bottom cabinet` | 398 |
| `close the door of the left_door bottom cabinet` | 392 |
| `chop the carving knife with the half steak 212` | 383 |
| `move to the countertop` | 260 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/48_canning_food.json`. Planner notes: `task_docs/notes/48_canning_food.md`.
