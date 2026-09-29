# 26 · Assembling Gift Baskets

Task name `assembling_gift_baskets`, task index 26.

> Place one candle, one butter cookie, one piece of Swiss cheese, and one bow from the table into each of the four wicker baskets on the floor in the living room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 868.7 s mean (26060 steps) |
| episode time limit | 1303.0 s (39090 steps at 30 Hz) |
| human base travel | 79.7083 m |
| goal literals (best ground option) | 16 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 331776 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.44; ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114059476 |

## Planner notes

**Tier:** B — 16 plain pick-and-place moves into open baskets; no doors, no state changes. Item widths vs the 44 mm span are unknown (no custom list), so graspability of the pillar candle and cheese is unverified.

### Goal in plain words

Each of the four wicker baskets must contain exactly one pillar candle, one butter cookie, one swiss cheese and one bow. Items of a kind are interchangeable and so are the baskets. `forpairs` needs a perfect matching, so two candles in one basket and none in another loses one literal. Where the baskets stand at the end does not matter. Nothing else is checked: no `not open`, no `ontop`.

### Q traps

- 16 literals, none true at reset. Every item placed in a distinct basket earns 1/16.
- Doubling up breaks the matching. Two of the same kind in one basket count once. Keep a per-basket tally of the four kinds.
- `inside` tests only the item's AABB centre (PREDICATES §3). An item on the rim or poking out still counts if the centre is in the basket volume.
- Knocking a basket over spills its items and loses those literals. Do not bump filled baskets with the base or arm.
- Past results on 311: Q 0.44-0.50 (7-8 items in). That confirms the wicker basket has a working fillable volume.

### Minimal plan

All 200 demos first lift all four baskets from the floor onto the living-room bottom cabinet, two per trip, then fill them. That relocation is not in the goal, but every trained `place ... in the wicker basket` frame shows baskets on the cabinet. Keep it unless the VLA fails to lift baskets; then fill them on the floor (out of distribution).

1. `move to the wicker basket` — basket centred and close in the head camera. ~15 s.
2. `pick up the wicker basket from the floors` — gripper closed but not fully, basket lifted off the floor in view. ~16 s. Repeat 1-2 for a second basket with the other hand.
3. `move to the bottom cabinet` — base stopped facing the cabinet. ~15 s.
4. `place the wicker basket on the bottom cabinet` (x2) — both baskets resting on the cabinet top, grippers open and empty. ~6 s each.
5. Repeat 1-4 for the other two baskets. Leave the four baskets side by side, not stacked.
6. For each kind (swiss cheese, pillar candle, butter cookie, bow), twice:
   - `move to the swiss cheese` — item on the coffee table in view. ~15 s.
   - `pick up the swiss cheese from the coffee table` — gripper closed on the item, table spot now empty. ~16 s. Repeat for a second item with the other hand.
   - `move to the bottom cabinet`. ~15 s.
   - `place the swiss cheese in the wicker basket` (x2, different baskets) — item visible inside the basket rim in depth. ~8 s each.
7. Swap in `pillar candle`, `butter cookie`, `bow` with the same sentences.

Budget: ~870 s demo mean vs a 1303 s limit. Two-handed carrying roughly halves the trips; a one-hand plan needs ~32 trips and may run out of time.

### What the demos do differently

- All 200 demos move all four baskets onto the bottom cabinet (4 × `place ... on the bottom cabinet`). The goal does not need it.
- Humans carry two items of the same kind per trip, one in each hand, and drop them into two different baskets.
- 119 distinct orders; the modal one (26 %) goes cheese, candle, cookie, bow, then repeats.
- `move to the bottom cabinet` is the top sentence (2000 uses): it is the hub of every trip.

### Hard parts and hacks

- Grasping four different small shapes from a low coffee table (z ~0.36 m). Bow and cheese widths are unknown vs the 44 mm span.
- Lifting a basket from the floor: basket and handle dimensions are unknown; humans managed it in every demo (teleop, not assisted-grasp evidence).
- Assignment bookkeeping is the planner's job: track which basket already holds which kind. Comet has no memory of this.
- Clutter: 16 items on one coffee table. Picking one can knock others off; items on the floor still need picking (`pick up the swiss cheese from the floors` occurs once in demos).
- Robot start varies across instances, baskets spread up to ~5 m between instances. The coffee table is fixed.
- Cheap fallback: if basket lifting fails, fill baskets where they lie on the floor with the same `place ... in the wicker basket` sentence.

### Hints for the VLM

- Everything is in `living_room_0`. One coffee table (items), one bottom cabinet (basket staging), one sofa, a fireplace, a shelf.
- Distractors: none of the target categories exist outside the 16 targets and 4 baskets in this room.
- Item appearance (unverified from assets): pillar candle, butter cookie, swiss cheese and gift bow are all small objects sitting together on the one coffee table.
- Done per literal: the item lies inside a basket rim in RGB and its depth sits below the rim. Done overall: each basket shows four distinct items, coffee table empty.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside candle.n.01_4 wicker_basket.n.01_1)` | no | yes |
| `(inside candle.n.01_3 wicker_basket.n.01_2)` | no | yes |
| `(inside candle.n.01_1 wicker_basket.n.01_3)` | no | yes |
| `(inside candle.n.01_2 wicker_basket.n.01_4)` | no | yes |
| `(inside swiss_cheese.n.01_4 wicker_basket.n.01_1)` | no | yes |
| `(inside swiss_cheese.n.01_3 wicker_basket.n.01_2)` | no | yes |
| `(inside swiss_cheese.n.01_1 wicker_basket.n.01_3)` | no | yes |
| `(inside swiss_cheese.n.01_2 wicker_basket.n.01_4)` | no | yes |
| `(inside butter_cookie.n.01_3 wicker_basket.n.01_1)` | no | yes |
| `(inside butter_cookie.n.01_2 wicker_basket.n.01_2)` | no | yes |
| `(inside butter_cookie.n.01_4 wicker_basket.n.01_3)` | no | yes |
| `(inside butter_cookie.n.01_1 wicker_basket.n.01_4)` | no | yes |
| `(inside bow.n.08_4 wicker_basket.n.01_1)` | no | yes |
| `(inside bow.n.08_2 wicker_basket.n.01_2)` | no | yes |
| `(inside bow.n.08_1 wicker_basket.n.01_3)` | no | yes |
| `(inside bow.n.08_3 wicker_basket.n.01_4)` | no | yes |

The goal has 331776 ground options (16 literals x331776); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forpairs 
                (?wicker_basket.n.01 - wicker_basket.n.01) 
                (?candle.n.01 - candle.n.01) 
                (inside ?candle.n.01 ?wicker_basket.n.01)
            ) 
            (forpairs 
                (?wicker_basket.n.01 - wicker_basket.n.01) 
                (?swiss_cheese.n.01 - swiss_cheese.n.01) 
                (inside ?swiss_cheese.n.01 ?wicker_basket.n.01)
            ) 
            (forpairs 
                (?wicker_basket.n.01 - wicker_basket.n.01) 
                (?butter_cookie.n.01 - butter_cookie.n.01) 
                (inside ?butter_cookie.n.01 ?wicker_basket.n.01)
            ) 
            (forpairs 
                (?wicker_basket.n.01 - wicker_basket.n.01) 
                (?bow.n.08 - bow.n.08) 
                (inside ?bow.n.08 ?wicker_basket.n.01)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `wicker_basket.n.01_1` | wicker_basket_92 | wicker_basket / dgkhyn | living_room_0 | floor, z 0.09 | 2.28 m (range 0.85-3.53) | yes, spread 4.91 m |
| `wicker_basket.n.01_2` | wicker_basket_91 | wicker_basket / dgkhyn | living_room_0 | floor, z 0.09 | 2.25 m (range 0.64-3.47) | yes, spread 4.7 m |
| `wicker_basket.n.01_3` | wicker_basket_90 | wicker_basket / dgkhyn | living_room_0 | floor, z 0.09 | 1.95 m (range 0.84-3.93) | yes, spread 5.2 m |
| `wicker_basket.n.01_4` | wicker_basket_89 | wicker_basket / dgkhyn | living_room_0 | floor, z 0.09 | 1.89 m (range 0.93-3.87) | yes, spread 4.95 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.5 m (range 0.74-2.1) | no (fixed) |
| `candle.n.01_1` | pillar_candle_88 | pillar_candle / bhaqam | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.59 m (range 0.98-2.45) | yes, spread 1.61 m |
| `candle.n.01_2` | pillar_candle_87 | pillar_candle / bhaqam | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.77 m (range 0.91-2.31) | yes, spread 1.61 m |
| `candle.n.01_3` | pillar_candle_86 | pillar_candle / bhaqam | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.66 m (range 0.77-2.16) | yes, spread 1.59 m |
| `candle.n.01_4` | pillar_candle_85 | pillar_candle / bhaqam | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.95 m (range 0.97-2.45) | yes, spread 1.45 m |
| `butter_cookie.n.01_1` | butter_cookie_84 | butter_cookie / kukrla | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.58 m (range 0.8-2.39) | yes, spread 1.54 m |
| `butter_cookie.n.01_2` | butter_cookie_83 | butter_cookie / kukrla | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.55 m (range 1.01-2.63) | yes, spread 1.67 m |
| `butter_cookie.n.01_3` | butter_cookie_82 | butter_cookie / kukrla | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.56 m (range 0.78-2.3) | yes, spread 1.68 m |
| `butter_cookie.n.01_4` | butter_cookie_81 | butter_cookie / kukrla | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.7 m (range 1.08-2.24) | yes, spread 1.61 m |
| `swiss_cheese.n.01_1` | swiss_cheese_80 | swiss_cheese / hwxeto | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.39 m (range 0.7-2.6) | yes, spread 1.58 m |
| `swiss_cheese.n.01_2` | swiss_cheese_79 | swiss_cheese / hwxeto | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.44 m (range 0.76-2.36) | yes, spread 1.69 m |
| `swiss_cheese.n.01_3` | swiss_cheese_78 | swiss_cheese / hwxeto | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.6 m (range 0.92-2.51) | yes, spread 1.55 m |
| `swiss_cheese.n.01_4` | swiss_cheese_77 | swiss_cheese / hwxeto | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.59 m (range 0.69-2.39) | yes, spread 1.58 m |
| `bow.n.08_1` | bow_76 | bow / fhchql | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.58 m (range 0.93-2.4) | yes, spread 1.53 m |
| `bow.n.08_2` | bow_75 | bow / fhchql | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.61 m (range 0.83-2.29) | yes, spread 1.49 m |
| `bow.n.08_3` | bow_74 | bow / fhchql | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.71 m (range 0.92-2.65) | yes, spread 1.61 m |
| `bow.n.08_4` | bow_73 | bow / fhchql | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.49 m (range 0.9-2.15) | yes, spread 1.48 m |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.55 m (range 1.11-2.01) | no |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom table.n.02_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bow.n.08_1 table.n.02_1)
(ontop bow.n.08_2 table.n.02_1)
(ontop bow.n.08_3 table.n.02_1)
(ontop bow.n.08_4 table.n.02_1)
(ontop butter_cookie.n.01_1 table.n.02_1)
(ontop butter_cookie.n.01_2 table.n.02_1)
(ontop butter_cookie.n.01_3 table.n.02_1)
(ontop butter_cookie.n.01_4 table.n.02_1)
(ontop candle.n.01_1 table.n.02_1)
(ontop candle.n.01_2 table.n.02_1)
(ontop candle.n.01_3 table.n.02_1)
(ontop candle.n.01_4 table.n.02_1)
(ontop swiss_cheese.n.01_1 table.n.02_1)
(ontop swiss_cheese.n.01_2 table.n.02_1)
(ontop swiss_cheese.n.01_3 table.n.02_1)
(ontop swiss_cheese.n.01_4 table.n.02_1)
(ontop wicker_basket.n.01_1 floor.n.01_1)
(ontop wicker_basket.n.01_2 floor.n.01_1)
(ontop wicker_basket.n.01_3 floor.n.01_1)
(ontop wicker_basket.n.01_4 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bow.n.08_1 table.n.02_1)
(touching bow.n.08_2 table.n.02_1)
(touching bow.n.08_3 table.n.02_1)
(touching bow.n.08_4 table.n.02_1)
(touching butter_cookie.n.01_1 table.n.02_1)
(touching butter_cookie.n.01_2 table.n.02_1)
(touching butter_cookie.n.01_3 table.n.02_1)
(touching butter_cookie.n.01_4 table.n.02_1)
(touching candle.n.01_1 table.n.02_1)
(touching candle.n.01_2 table.n.02_1)
(touching candle.n.01_3 table.n.02_1)
(touching candle.n.01_4 table.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 wicker_basket.n.01_1)
(touching floor.n.01_1 wicker_basket.n.01_2)
(touching floor.n.01_1 wicker_basket.n.01_3)
(touching floor.n.01_1 wicker_basket.n.01_4)
(touching swiss_cheese.n.01_1 table.n.02_1)
(touching swiss_cheese.n.01_2 table.n.02_1)
(touching swiss_cheese.n.01_3 table.n.02_1)
(touching swiss_cheese.n.01_4 table.n.02_1)
(touching table.n.02_1 bow.n.08_1)
(touching table.n.02_1 bow.n.08_2)
(touching table.n.02_1 bow.n.08_3)
(touching table.n.02_1 bow.n.08_4)
(touching table.n.02_1 butter_cookie.n.01_1)
(touching table.n.02_1 butter_cookie.n.01_2)
(touching table.n.02_1 butter_cookie.n.01_3)
(touching table.n.02_1 butter_cookie.n.01_4)
(touching table.n.02_1 candle.n.01_1)
(touching table.n.02_1 candle.n.01_2)
(touching table.n.02_1 candle.n.01_3)
(touching table.n.02_1 candle.n.01_4)
(touching table.n.02_1 swiss_cheese.n.01_1)
(touching table.n.02_1 swiss_cheese.n.01_2)
(touching table.n.02_1 swiss_cheese.n.01_3)
(touching table.n.02_1 swiss_cheese.n.01_4)
(touching wicker_basket.n.01_1 floor.n.01_1)
(touching wicker_basket.n.01_2 floor.n.01_1)
(touching wicker_basket.n.01_3 floor.n.01_1)
(touching wicker_basket.n.01_4 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 806.9 s (range 628.0-1525.37). Skills per demo 68.0 (range 55-70). 119 distinct skill orders; the most common one covers 26% of demos.

Most common skill counts per demo (26% of demos): move to x30, pick up from x20, place in x16, place on x4.

Representative demo `episode_00260160.json` (831.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wicker basket` (0.0-8.0 s)
2. `pick up the wicker basket from the floors` (8.0-33.5 s)
3. `move to the wicker basket` (33.5-38.7 s)
4. `pick up the wicker basket from the floors` (38.7-60.0 s)
5. `move to the bottom cabinet` (60.0-73.0 s)
6. `place the wicker basket on the bottom cabinet` (73.0-88.2 s)
7. `place the wicker basket on the bottom cabinet` (88.2-94.0 s)
8. `move to the wicker basket` (94.0-107.9 s)
9. `pick up the wicker basket from the floors` (107.9-123.7 s)
10. `move to the wicker basket` (123.7-128.0 s)
11. `pick up the wicker basket from the floors` (128.0-138.8 s)
12. `move to the bottom cabinet` (138.8-151.5 s)
13. `place the wicker basket on the bottom cabinet` (151.5-164.3 s)
14. `place the wicker basket on the bottom cabinet` (164.3-167.8 s)
15. `move to the swiss cheese` (167.8-187.0 s)
16. `pick up the swiss cheese from the coffee table` (187.0-207.5 s)
17. `move to the swiss cheese` (207.5-213.0 s)
18. `pick up the swiss cheese from the coffee table` (213.0-220.0 s)
19. `move to the bottom cabinet` (220.0-233.9 s)
20. `place the swiss cheese in the wicker basket` (233.9-249.0 s)
21. `place the swiss cheese in the wicker basket` (249.0-261.4 s)
22. `move to the pillar candle` (261.4-278.8 s)
23. `pick up the pillar candle from the coffee table` (278.8-285.9 s)
24. `move to the pillar candle` (285.9-296.0 s)
25. `pick up the pillar candle from the coffee table` (296.0-307.8 s)
26. `move to the bottom cabinet` (307.8-322.0 s)
27. `place the pillar candle in the wicker basket` (322.0-335.0 s)
28. `place the pillar candle in the wicker basket` (335.0-350.5 s)
29. `move to the butter cookie` (350.5-365.6 s)
30. `pick up the butter cookie from the coffee table` (365.6-376.0 s)
31. `move to the butter cookie` (376.0-378.3 s)
32. `pick up the butter cookie from the coffee table` (378.3-395.0 s)
33. `move to the bottom cabinet` (395.0-411.7 s)
34. `place the butter cookie in the wicker basket` (411.7-420.5 s)
35. `place the butter cookie in the wicker basket` (420.5-434.0 s)
36. `move to the bow` (434.0-455.4 s)
37. `pick up the bow from the coffee table` (455.4-465.3 s)
38. `move to the bow` (465.3-474.0 s)
39. `pick up the bow from the coffee table` (474.0-483.0 s)
40. `move to the bottom cabinet` (483.0-497.0 s)
41. `place the bow in the wicker basket` (497.0-509.4 s)
42. `place the bow in the wicker basket` (509.4-521.5 s)
43. `move to the swiss cheese` (521.5-536.0 s)
44. `pick up the swiss cheese from the coffee table` (536.0-550.0 s)
45. `move to the swiss cheese` (550.0-553.0 s)
46. `pick up the swiss cheese from the coffee table` (553.0-564.2 s)
47. `move to the bottom cabinet` (564.2-580.9 s)
48. `place the swiss cheese in the wicker basket` (580.9-590.3 s)
49. `place the swiss cheese in the wicker basket` (590.3-597.0 s)
50. `move to the pillar candle` (597.0-620.0 s)
51. `pick up the pillar candle from the coffee table` (620.0-632.0 s)
52. `move to the pillar candle` (632.0-633.0 s)
53. `pick up the pillar candle from the coffee table` (633.0-645.0 s)
54. `move to the bottom cabinet` (645.0-661.1 s)
55. `place the pillar candle in the wicker basket` (661.1-671.0 s)
56. `place the pillar candle in the wicker basket` (671.0-681.0 s)
57. `move to the bow` (681.0-697.9 s)
58. `pick up the bow from the coffee table` (697.9-708.2 s)
59. `move to the bow` (708.2-712.0 s)
60. `pick up the bow from the coffee table` (712.0-727.0 s)
61. `move to the bottom cabinet` (727.0-740.4 s)
62. `place the bow in the wicker basket` (740.4-746.8 s)
63. `place the bow in the wicker basket` (746.8-754.0 s)
64. `move to the butter cookie` (754.0-774.0 s)
65. `pick up the butter cookie from the coffee table` (774.0-782.0 s)
66. `move to the butter cookie` (782.0-784.0 s)
67. `pick up the butter cookie from the coffee table` (784.0-791.8 s)
68. `move to the bottom cabinet` (791.8-808.5 s)
69. `place the butter cookie in the wicker basket` (808.5-815.0 s)
70. `place the butter cookie in the wicker basket` (815.0-831.1 s)

Mean duration per skill in this task: hand over 10.0 s, move to 14.6 s, pick up from 15.5 s, place in 7.8 s, place on 6.4 s, push to 8.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bottom cabinet` | 2000 |
| `pick up the pillar candle from the coffee table` | 800 |
| `pick up the bow from the coffee table` | 800 |
| `pick up the butter cookie from the coffee table` | 799 |
| `pick up the swiss cheese from the coffee table` | 799 |
| `pick up the wicker basket from the floors` | 798 |
| `move to the wicker basket` | 762 |
| `place the pillar candle in the wicker basket` | 758 |
| `move to the swiss cheese` | 757 |
| `move to the bow` | 747 |
| `place the wicker basket on the bottom cabinet` | 742 |
| `place the swiss cheese in the wicker basket` | 740 |
| `place the bow in the wicker basket` | 739 |
| `move to the pillar candle` | 733 |
| `move to the butter cookie` | 729 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/26_assembling_gift_baskets.json`. Planner notes: `task_docs/notes/26_assembling_gift_baskets.md`.
