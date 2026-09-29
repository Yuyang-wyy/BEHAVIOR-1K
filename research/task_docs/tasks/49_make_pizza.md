# 49 · Make Pizza

Task name `make_pizza`, task index 49.

> Make a pizza on the cookie sheet in the kitchen: take the grated cheese, the four pieces of pepperoni, and the two mushrooms from their tupperware containers in the refrigerator; chop the Vidalia onion on the chopping board with the knife, and also chop the two whole mushrooms in half; top the pizza dough that's already on the cookie sheet with the cheese, pepperoni, halved mushrooms, and chopped onion; bake it in the oven until it becomes a pizza, and leave the finished pizza on the cookie sheet.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 639.6 s mean (19186 steps) |
| episode time limit | 959.3 s (28780 steps at 30 Hz) |
| human base travel | 56.8705 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114061917 |

## Planner notes

**Tier:** D — a cooking recipe in the oven, which first needs a slice-then-dice (onion), a slice (mushroom), two particle pours and several small placements. It is the longest recipe chain in this block.

### Goal in plain words

A `pizza` object must exist and rest on the cookie sheet `baking_sheet_79`. It can only come from a `CookingObjectRule` recipe in `heat_cook.json`. The full `pizza` recipe needs tomato sauce, marjoram and 7 pepperoni, none of which exist in this scene, so it is never active. The recipe that can fire is **`simple_pizza`**. It needs all of the following:

- The dough is in or `ontop` the cookie sheet. This is already true at start.
- At least **1** `pepperoni` is `ontop` the dough.
- At least **1** `half__mushroom` is `ontop` the dough.
- The dough is `covered` by `grated_cheese`, meaning at least 1 particle touches it (§12, `covered.py` `PHYSICAL_PARTICLE_THRESHOLD` = 1).
- The dough is `covered` by `diced__vidalia_onion`, at least 1 particle touching.
- **Container:** the cookie sheet. **Heat source:** the oven `oven_ffitak_0`, which must heat the sheet. That means the sheet is Inside the oven, the oven is toggled on, and the oven is fully closed (§2).

With `timesteps` null the recipe fires on the first step these all hold (`CookingRule`, `transition_rules.py:2323-2349`). The pizza spawns `OnTop` the sheet (`_spawn_object_in_container`, `transition_rules.py:1783`), so both goal literals flip together and the episode ends.

**Tool:** the carving knife `carving_knife_77`, for the onion and the mushrooms.

### Q traps

- Two literals, both flipping on one step. Q is 0 or 1.
- The toppings need only one of each: 1 pepperoni, 1 mushroom half, one particle of cheese, one piece of onion. The four pepperoni and two mushrooms in the instruction are not required.
- **The knife destroys things.** `pizza_dough`, `pepperoni` and `mushroom` are all `sliceable`, and `half__mushroom` and `half__vidalia_onion` are `diceable` (KB). A knife touching the dough removes it for good, and then no pizza is possible. A second touch on a mushroom half dices it (§7). Do all cutting on the board, away from the dough, and put the knife down before topping.
- **Order on the dough:** place the pepperoni and the mushroom half **before** pouring the cheese and onion. `ontop` needs the piece to touch the dough itself (§4). A pepperoni lying on a heap of cheese does not count.
- **Oven "open" means any joint.** `oven/ffitak` has no `openable_joint_ids`, so all 3 joints count: the door and two rack joints (`open_state.py:96` fallback). A rack left pulled out more than 5 % keeps the oven "open", and it does not heat.
- Extra objects on the sheet do not block the recipe (`ignore_nonrecipe_objects` is True).

### Minimal plan

1. `pick up the carving knife from the bar` — ~12 s. The onion already sits on the chopping board.
2. `chop the carving knife with the vidalia onion`, wait 2 s, then `chop the carving knife with the half vidalia onion 80` — at least one pile of onion pieces. ~4 s each.
3. `move to the fridge`, `open the door of the right_door fridge`, `pick up the tupperware from the layer_4 fridge` (the mushroom box), `pick up the tupperware from the layer_5 fridge` (cheese or pepperoni; check what is inside) — ~7 + 24 + 12 + 12 s. The contents vary by layer and instance, so pick by appearance.
4. `move to the chopping board`, `pour the mushroom and mushroom into the tupperware` (sic; tupperware onto board) — ~7 + 8 s.
5. `chop the carving knife with the mushroom` — one cut only, then **put the knife down**: `place the carving knife on the bar`. ~4 + 7 s.
6. Place one mushroom half and one pepperoni on the dough. No trained prompt; closest: `place the vidalia onion on the chopping board` shape. ~12 s each. Get the pepperoni by pouring its tupperware onto the board or dough: `pour the pepperoni and pepperoni and pepperoni and pepperoni into the tupperware` (sic).
7. `pick up the chopping board from the bar`, move over the dough, `pour the diced  vidalia onion into the chopping board` (sic) — some onion pieces on the dough. ~12 + 8 s.
8. With the cheese tupperware: `pour the grated cheese into the tupperware` (sic; tupperware onto dough) — cheese on the dough. ~8 s.
9. `move to the oven`, `open the door of the oven` — ~7 + 24 s.
10. `pick up the baking sheet from the bar`, `move to the oven`, `place the baking sheet in the high_level oven` — ~12 + 7 + 13 s. Carry it level. If the rack is pulled first (`pull tray the high_level oven`), push it back with `push tray the high_level oven`.
11. `close the door of the oven`, `turn on the oven` — ~17 + 7 s. Success fires on the next step.

The plan takes about 400 s against a 959 s limit.

### What the demos do differently

- They gather everything in the bowl: onion, mushroom halves and pepperoni are poured into `bowl_76`, then the bowl is poured over the dough. This takes more pours than needed.
- They move the baking sheet next to the oven early (`place the baking sheet on the bar next to the left oven`), which shortens the final carry.
- They pull the rack out, place the sheet, then push the rack back. After `turn on the oven` they open the door again (not needed; the pizza is already made).
- They halve both mushrooms and dice both onion halves (only one of each is needed).

### Hard parts and hacks

- **Grasps that fit the jaws.** Pepperoni is a 30 mm disc 5 mm thick, and a top-down pinch across its diameter works. The mushroom is a 30 mm cube, and its halves are 30 x 29 x 14 mm. The knife `fqqbop` is 323 x 39 x 24 mm.
- **Grasps that do not fit.** The onion is 100 x 70 x 71 mm but never needs moving. The tupperwares (219 mm) can only be held by the rim. The **cookie sheet** is 270 x 300 x 30 mm and lies flat, so only its edge can be pinched. It must be carried level with the dough on it, which is the riskiest step.
- **Fridge.** `fridge_petcxr` has two doors. The tupperwares are at z 0.77-1.86, so the top one needs the trunk raised.
- **Oven.** It is low (the root sits at z 0.54), under the cooktop, on the far counter from the dough. The robot must lower the trunk to slide the sheet in.
- The oven has two `togglebutton` links, and only the first one toggles (`link_based_state_mixin.py:90`). Which one is first is not verified.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. The dough on the cookie sheet, the chopping board with the onion, the knife and the bowl are on `bar_egwapq_0` along the x ≈ 8.2 wall, near the sink. The oven is under the cooktop at (6.91, -0.65) on the other counter. The two-door fridge is at (5.2, -0.57).
- The three tupperwares are in the fridge: one holds grated cheese (white shreds), one two small mushrooms, one four pepperoni discs.
- Done: the episode ends by itself on success. Nothing visible changes until the oven is closed and on.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real pizza.n.01_1)` | no | yes |
| `(ontop pizza.n.01_1 cookie_sheet.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?pizza.n.01_1) 
            (ontop ?pizza.n.01_1 ?cookie_sheet.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `pizza_dough.n.01_1` | pizza_dough_87 | pizza_dough / jguwbv | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.13 m (range 1.17-7.36) | yes, spread 1.75 m |
| `grated_cheese.n.01_1` | particle system | grated_cheese | - | - | - | - |
| `pepperoni.n.01_1` | pepperoni_86 | pepperoni / xcurfr | kitchen_0 | high (1.1-1.6 m), z 1.33 | 3.33 m (range 1.4-4.6) | yes, spread 0.71 m |
| `pepperoni.n.01_2` | pepperoni_85 | pepperoni / xcurfr | kitchen_0 | high (1.1-1.6 m), z 1.34 | 3.3 m (range 1.39-4.64) | yes, spread 0.69 m |
| `pepperoni.n.01_3` | pepperoni_84 | pepperoni / xcurfr | kitchen_0 | high (1.1-1.6 m), z 1.33 | 3.32 m (range 1.46-4.72) | yes, spread 0.79 m |
| `pepperoni.n.01_4` | pepperoni_83 | pepperoni / xcurfr | kitchen_0 | high (1.1-1.6 m), z 1.33 | 3.33 m (range 1.4-4.58) | yes, spread 0.84 m |
| `mushroom.n.05_1` | mushroom_82 | mushroom / zlukhz | kitchen_0 | high (1.1-1.6 m), z 1.34 | 3.3 m (range 1.44-5.11) | yes, spread 0.75 m |
| `mushroom.n.05_2` | mushroom_81 | mushroom / zlukhz | kitchen_0 | high (1.1-1.6 m), z 1.34 | 3.25 m (range 1.39-5.12) | yes, spread 0.76 m |
| `vidalia_onion.n.01_1` | vidalia_onion_80 | vidalia_onion / buyxll | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 3.39 m (range 1.52-7.02) | yes, spread 2.08 m |
| `pizza.n.01_1` | does not exist at reset; created by a transition (slicing, cooking, etc.) | pizza | - | - | - | - |
| `oven.n.01_1` | oven_ffitak_0 | oven / ffitak | kitchen_0 | low (0.25-0.6 m), z 0.54 | 3.38 m (range 1.31-6.4) | no (fixed) |
| `cookie_sheet.n.01_1` | baking_sheet_79 | baking_sheet / yhurut | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.13 m (range 1.17-7.36) | yes, spread 1.75 m |
| `chopping_board.n.01_1` | chopping_board_78 | chopping_board / sygezm | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.32 m (range 1.53-6.92) | yes, spread 1.93 m |
| `carving_knife.n.01_1` | carving_knife_77 | carving_knife / fqqbop | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.08 m (range 1.49-7.63) | yes, spread 2.17 m |
| `bowl.n.01_1` | bowl_76 | bowl / szgdpc | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 2.8 m (range 1.14-6.77) | yes, spread 0.42 m |
| `tupperware.n.01_1` | tupperware_75 | tupperware / mkstwr | kitchen_0 | high (1.1-1.6 m), z 1.38 | 3.29 m (range 0.96-4.84) | yes, spread 0.68 m |
| `tupperware.n.01_2` | tupperware_74 | tupperware / mkstwr | kitchen_0 | high (1.1-1.6 m), z 1.38 | 3.27 m (range 1.44-5.08) | yes, spread 0.68 m |
| `tupperware.n.01_3` | tupperware_73 | tupperware / mkstwr | kitchen_0 | high (1.1-1.6 m), z 1.38 | 3.33 m (range 1.44-4.66) | yes, spread 0.67 m |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.45 m (range 1.29-5.02) | no (fixed) |
| `cabinet.n.01_1` | top_cabinet_tynnnw_0 | top_cabinet / tynnnw | kitchen_0 | very high (>1.6 m), z 1.89 | 3.71 m (range 2.33-7.46) | no (fixed) |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 3.23 m (range 1.86-7.09) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.01 m (range 0.91-3.68) | no (fixed) |

Initial conditions from `:init`:

```lisp
(filled tupperware.n.01_1 grated_cheese.n.01_1)
(future pizza.n.01_1)
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom oven.n.01_1 kitchen)
(inside mushroom.n.05_1 tupperware.n.01_2)
(inside mushroom.n.05_2 tupperware.n.01_2)
(inside pepperoni.n.01_1 tupperware.n.01_3)
(inside pepperoni.n.01_2 tupperware.n.01_3)
(inside pepperoni.n.01_3 tupperware.n.01_3)
(inside pepperoni.n.01_4 tupperware.n.01_3)
(inside tupperware.n.01_1 electric_refrigerator.n.01_1)
(inside tupperware.n.01_2 electric_refrigerator.n.01_1)
(inside tupperware.n.01_3 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bowl.n.01_1 countertop.n.01_1)
(ontop carving_knife.n.01_1 countertop.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop cookie_sheet.n.01_1 countertop.n.01_1)
(ontop pizza_dough.n.01_1 cookie_sheet.n.01_1)
(ontop vidalia_onion.n.01_1 chopping_board.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bowl.n.01_1 countertop.n.01_1)
(touching carving_knife.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_1 vidalia_onion.n.01_1)
(touching cookie_sheet.n.01_1 countertop.n.01_1)
(touching cookie_sheet.n.01_1 pizza_dough.n.01_1)
(touching countertop.n.01_1 bowl.n.01_1)
(touching countertop.n.01_1 carving_knife.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 cookie_sheet.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching pizza_dough.n.01_1 cookie_sheet.n.01_1)
(touching vidalia_onion.n.01_1 chopping_board.n.01_1)
```

## What the human demos did

200 annotated demos. Length 723.5 s (range 361.8-921.7). Skills per demo 64.0 (range 54-74). 197 distinct skill orders; the most common one covers 1% of demos.

Most common skill counts per demo (6% of demos): pick up from x15, move to x11, place on x7, place on next to x6, pour x6, chop x5, open door x4, close door x3, place in x2, pull tray x1, push tray x1, turn on switch x1.

Representative demo `episode_00492920.json` (750.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the baking sheet` (0.7-9.4 s)
2. `pick up the baking sheet from the bar` (9.4-22.6 s)
3. `move to the oven` (22.6-30.9 s)
4. `place the baking sheet on the bar next to the left oven` (30.9-39.8 s)
5. `move to the carving knife` (39.8-47.9 s)
6. `pick up the carving knife from the bar` (47.9-62.7 s)
7. `place the carving knife on the bar next to the left drop in sink` (62.7-68.0 s)
8. `pick up the bowl from the bar` (68.0-75.6 s)
9. `place the bowl on the to_the_edge_of bar` (75.6-84.5 s)
10. `move to the vidalia onion` (84.5-90.8 s)
11. `pick up the vidalia onion from the chopping board` (90.8-116.0 s)
12. `move to the chopping board` (116.0-119.0 s)
13. `pick up the chopping board from the bar` (119.0-139.7 s)
14. `move to the bowl` (139.7-148.4 s)
15. `place the chopping board on the bar next to the right bowl` (148.4-159.9 s)
16. `place the vidalia onion on the chopping board` (159.9-172.1 s)
17. `pick up the carving knife from the bar` (172.1-182.7 s)
18. `chop the carving knife with the vidalia onion` (182.7-186.7 s)
19. `chop the carving knife with the half vidalia onion 80` (186.7-189.0 s)
20. `chop the carving knife with the half vidalia onion 80` (189.0-191.0 s)
21. `place the carving knife on the bar next to the right chopping board` (191.0-195.5 s)
22. `pick up the chopping board from the bar` (195.5-202.9 s)
23. `pour the diced  vidalia onion into the chopping board` (202.9-211.2 s)
24. `place the chopping board on the bar next to the right bowl` (211.2-221.3 s)
25. `move to the fridge` (221.3-235.1 s)
26. `open the door of the right_door fridge` (235.1-268.5 s)
27. `pick up the tupperware from the layer_4 fridge` (268.5-289.4 s)
28. `pick up the tupperware from the layer_5 fridge` (289.4-311.0 s)
29. `move to the baking sheet` (311.0-318.3 s)
30. `place the tupperware on the drop in sink next to the left baking sheet` (318.3-328.2 s)
31. `pour the mushroom and mushroom into the tupperware` (328.2-336.1 s)
32. `place the tupperware in the drop in sink` (336.1-345.8 s)
33. `move to the fridge` (345.8-355.4 s)
34. `close the door of the right_door fridge` (355.4-378.6 s)
35. `open the door of the left_door fridge` (378.6-420.6 s)
36. `pick up the tupperware from the layer_4 fridge` (420.6-446.6 s)
37. `close the door of the left_door fridge` (446.6-465.2 s)
38. `move to the bowl` (465.2-475.1 s)
39. `pour the pepperoni and pepperoni and pepperoni and pepperoni into the tupperware` (475.1-484.8 s)
40. `move to the tupperware` (484.8-487.7 s)
41. `place the tupperware on the tupperware` (487.7-497.6 s)
42. `pick up the carving knife from the bar` (497.6-504.3 s)
43. `chop the carving knife with the mushroom` (504.3-509.3 s)
44. `chop the carving knife with the mushroom` (509.3-512.2 s)
45. `place the carving knife on the bar` (512.2-516.4 s)
46. `pick up the chopping board from the bar` (516.4-524.9 s)
47. `pour the half mushroom 81 and half mushroom 81 and half mushroom 82 and half mushroom 82 into the chopping board` (524.9-532.7 s)
48. `place the chopping board on the bar` (532.7-543.3 s)
49. `pick up the bowl from the bar` (543.3-552.1 s)
50. `move to the pizza dough` (552.1-558.7 s)
51. `pour the half mushroom 81 and half mushroom 81 and half mushroom 82 and half mushroom 82 and pepperoni and pepperoni and pepperoni and pepperoni and diced  vidalia onion into the bowl` (558.7-565.8 s)
52. `move to the tupperware` (565.8-567.8 s)
53. `place the bowl on the tupperware` (567.8-574.5 s)
54. `pick up the tupperware from the drop in sink` (574.5-579.5 s)
55. `pour the grated cheese into the tupperware` (579.5-592.1 s)
56. `place the tupperware on the drop in sink` (592.1-600.9 s)
57. `open the door of the oven` (600.9-624.4 s)
58. `pull tray the high_level oven` (624.4-653.4 s)
59. `pick up the baking sheet from the bar` (653.4-671.1 s)
60. `move to the oven` (671.1-674.9 s)
61. `place the baking sheet in the high_level oven` (674.9-689.9 s)
62. `push tray the high_level oven` (689.9-696.2 s)
63. `close the door of the oven` (696.2-718.9 s)
64. `turn on the oven` (718.9-728.1 s)
65. `open the door of the oven` (728.1-750.9 s)

Mean duration per skill in this task: chop 3.8 s, close door 16.7 s, move to 6.6 s, open door 24.1 s, pick up from 12.0 s, place in 13.0 s, place on 6.7 s, place on next to 7.7 s, pour 8.0 s, pull tray 27.2 s, push to 9.3 s, push tray 7.0 s, turn on switch 6.9 s, turn to 10.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the chopping board from the bar` | 590 |
| `pick up the carving knife from the bar` | 571 |
| `pick up the baking sheet from the bar` | 400 |
| `move to the fridge` | 400 |
| `open the door of the oven` | 400 |
| `chop the carving knife with the mushroom` | 397 |
| `place the chopping board on the bar next to the right bowl` | 390 |
| `move to the baking sheet` | 381 |
| `move to the oven` | 376 |
| `move to the bowl` | 375 |
| `chop the carving knife with the half vidalia onion 80` | 373 |
| `pick up the bowl from the bar` | 358 |
| `place the carving knife on the bar next to the right chopping board` | 312 |
| `move to the tupperware` | 305 |
| `pick up the tupperware from the layer_5 fridge` | 267 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/49_make_pizza.json`. Planner notes: `task_docs/notes/49_make_pizza.md`.
