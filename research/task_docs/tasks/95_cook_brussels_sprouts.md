# 95 · Cook Brussels Sprouts

Task name `cook_brussels_sprouts`, task index 95.

> Take the brussels sprouts from the refrigerator, cut them on the cutting board, put the pieces onto the baking sheet, and cook them in the oven.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | kitchen |
| rooms loaded | bar_0, corridor_0, kitchen_0 |
| human demo length | 522.1 s mean (15661 steps) |
| episode time limit | 783.1 s (23492 steps at 30 Hz) |
| human base travel | 34.869 m |
| goal literals (best ground option) | 26 |
| literals already true at start (inferred) | 2 |
| max Q short of full success | 0.923 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/9XPaPQmWAgI |

## Planner notes

**Tier:** D. It needs a fridge door, slicing 4 sprouts into 8 halves, moving all 8 into the oven, closing the oven, turning it on, and re-closing the fridge. It is one of the longest chains in the benchmark (human mean 522 s, about 48 skills).

### Goal in plain words

- All 8 halves must exist (each of the 4 whole sprouts sliced once), be cooked, and be inside the oven (`oven_amblrk_0`).
- The fridge `fridge_jtqazu_0` (the one holding the tupperware) and the oven must both be closed at the end.
- The baking sheet and the cutting board are not in the goal. They are only convenient.
- The second kitchen fridge (`fridge_jtqazu_1`) and the freezer are irrelevant.

### Q traps

- There are 26 literals. The two `not open` literals are true at reset and never score, so the best partial Q is 24/26 = 0.923.
  - Each sliced-and-placed half is worth 3 literals: `real`, `cooked`, `inside`.
  - An unsliced sprout leaves 2 slots empty, which is 6 literals lost.
- **Dicing destroys halves.** `half__brussels_sprouts` is diceable (PREDICATES §7). If the knife still touches a half 2 s after a cut, it re-arms and dices it. That half's `real` becomes False for good. Lift the knife clear immediately after each cut.
- **Heat reaches only food inside the oven** (§2, §15). The halves' own AABB centres must be in the oven's volume, with the door fully shut (within 5%) and the oven on. The oven has two joints (`door_leaf1`, `door_leaf2`), and both must be shut for `not open`.
- Cooking is quick once running: cook temperature 58 °C, oven steady state ~212 °C, so a few seconds (§15). `cooked` latches, so success fires as soon as all 8 are hot **and** both doors are closed. The oven is left on; the goal allows it.
- **Fridge left open blocks success** but costs no partial Q. Close it right after taking the tupperware.
- The oven starts off (`ToggledOn` false). Pressing the button while the door is open does not stick, because the oven's state `requires_closed`. Close the door first, then press.

### Minimal plan

1. `move to the electric refrigerator`. About 15 s.
2. `open the door of the electric refrigerator`. About 25 s.
3. `pick up the tupperware from the electric refrigerator`. About 9 s.
4. `close the door of the electric refrigerator`. Done when the door is flush. About 19 s.
5. `move to the commercial kitchen table`, then `place the tupperware on the commercial kitchen table`. About 21 s.
6. `pick up the tupperware from the commercial kitchen table`, then `pour the brussels sprouts and brussels sprouts and brussels sprouts and brussels sprouts into the tupperware`. The wording is the demos'; it means tip them out. Pour onto the **baking sheet** rather than the cutting board. About 19 s. See the hack below.
7. `move to the carving knife`, then `pick up the carving knife from the cutting board`. About 24 s.
8. `chop the carving knife with the brussels sprouts`, 4 times, once per sprout. Done when two halves are visible where the sprout was. Lift the knife away at once. About 6 s each.
9. `place the carving knife on the cutting board`. About 6 s.
10. `move to the oven`, then `open the door of the oven`. About 40 s.
11. `move to the baking sheet`, then `pick up the baking sheet from the commercial kitchen table`. About 24 s.
12. `move to the oven`, then `place the baking sheet in the oven`. Done when the sheet is inside, past the door plane. About 34 s.
13. `close the door of the oven`, then `turn on the oven`. About 29 s.

- Totals: about 290 s against a 783.1 s limit.

### What the demos do differently

- The demos slice on the cutting board, then move 8 halves one by one to the baking sheet. That is 1538 `place the half brussels sprouts on the baking sheet` segments over 200 demos, 150-200 s per demo.
- Slicing on the sheet avoids this. The halves spawn at the sprout's part poses (§7), so they land on whatever the sprout sat on. This is derived from source, not tested.
- The demos also move the cutting board and the baking sheet next to each other, which is not needed.
- About 162 distinct skill orders were seen, so there is no canonical order.

### Hard parts and hacks

- **Slice where you bake.** Pour or place the whole sprouts on the baking sheet and cut them there. No cutting board is needed, because the slicer ability is on the knife (§7).
- **Grasp sizes (asset bbox):**
  - Sprout 0.064 x 0.050 x 0.056 m: wider than 44 mm on every axis.
  - Half 0.050 x 0.052 x 0.032 m: thin only on its cut face.
  - Knife 0.277 x 0.037 x 0.024 m: graspable.
  - Baking sheet 0.249 x 0.416 x 0.023 m: flat; only a rim or edge grasp.
  - Tupperware 0.219 x 0.219 x 0.136 m.
- **Carrying the loaded sheet** risks spilling halves. A half that falls on the oven door or the floor loses `inside` (and possibly `cooked`).
- **Which oven compartment** has a fillable volume is not verified. The asset has two door leaves. Use the one the demos use (`open the door of the oven`).
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The scene is a restaurant kitchen: two identical fridges, one freezer, one oven, one stove, a deep fryer, flat-top grills and two commercial kitchen tables.
- The tupperware is in `fridge_jtqazu_0`. Check both fridges if unsure, but close whichever you open.
- The knife, the cutting board and the baking sheet start on a commercial kitchen table. The knife rests on the board.
- Done: 8 half sprouts are visible on the sheet inside the oven, both oven leaves and the fridge are shut, and the oven's toggle marker is green.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real half__brussels_sprouts.n.01_4)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_4)` | no | yes |
| `(inside half__brussels_sprouts.n.01_4 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_3)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_3)` | no | yes |
| `(inside half__brussels_sprouts.n.01_3 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_1)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_1)` | no | yes |
| `(inside half__brussels_sprouts.n.01_1 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_7)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_7)` | no | yes |
| `(inside half__brussels_sprouts.n.01_7 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_5)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_5)` | no | yes |
| `(inside half__brussels_sprouts.n.01_5 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_8)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_8)` | no | yes |
| `(inside half__brussels_sprouts.n.01_8 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_6)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_6)` | no | yes |
| `(inside half__brussels_sprouts.n.01_6 oven.n.01_1)` | no | yes |
| `(real half__brussels_sprouts.n.01_2)` | no | yes |
| `(cooked half__brussels_sprouts.n.01_2)` | no | yes |
| `(inside half__brussels_sprouts.n.01_2 oven.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |
| `(not open oven.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?half__brussels_sprouts.n.01 - half__brussels_sprouts.n.01)
                (and
                    (real ?half__brussels_sprouts.n.01)
                    (cooked ?half__brussels_sprouts.n.01)
                    (inside ?half__brussels_sprouts.n.01 oven.n.01_1)
                )
            )
            (not
                (open ?electric_refrigerator.n.01_1)
            )
            (not
                (open ?oven.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `brussels_sprouts.n.01_1` | brussels_sprouts_95 | brussels_sprouts / hkwyzk | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 3.55 m (range 1.58-6.65) | yes, spread 0.79 m |
| `brussels_sprouts.n.01_2` | brussels_sprouts_94 | brussels_sprouts / hkwyzk | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.52 m (range 1.59-6.63) | yes, spread 0.77 m |
| `brussels_sprouts.n.01_3` | brussels_sprouts_93 | brussels_sprouts / hkwyzk | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.53 m (range 1.57-6.63) | yes, spread 0.75 m |
| `brussels_sprouts.n.01_4` | brussels_sprouts_92 | brussels_sprouts / hkwyzk | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.54 m (range 1.59-6.67) | yes, spread 0.73 m |
| `half__brussels_sprouts.n.01_1` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_2` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_3` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_4` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_5` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_6` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_7` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `half__brussels_sprouts.n.01_8` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_brussels_sprouts | - | - | - | - |
| `tupperware.n.01_1` | tupperware_91 | tupperware / mkstwr | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 3.54 m (range 1.59-6.63) | yes, spread 0.71 m |
| `carving_knife.n.01_1` | carving_knife_90 | carving_knife / zaihmr | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.11 m (range 1.23-4.48) | yes, spread 2.3 m |
| `chopping_board.n.01_1` | chopping_board_89 | chopping_board / mqsqhl | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.07 m (range 1.13-4.44) | yes, spread 2.39 m |
| `cookie_sheet.n.01_1` | baking_sheet_88 | baking_sheet / yhurut | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 2.98 m (range 1.36-4.14) | yes, spread 2.05 m |
| `oven.n.01_1` | oven_amblrk_0 | oven / amblrk | kitchen_0 | table/counter (0.6-1.1 m), z 0.97 | 4.19 m (range 1.28-6.3) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_jtqazu_0 | fridge / jtqazu | kitchen_0 | table/counter (0.6-1.1 m), z 1.08 | 3.72 m (range 1.61-6.85) | no (fixed) |
| `countertop.n.01_1` | commercial_kitchen_table_vxvtec_0 | commercial_kitchen_table / vxvtec | kitchen_0 | low (0.25-0.6 m), z 0.54 | 3.01 m (range 2.12-3.81) | no |
| `floor.n.01_1` | floors_vikfyd_0 | floors / vikfyd | kitchen_0 | floor, z 0.0 | 2.52 m (range 1.33-3.51) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bar",
  "corridor",
  "kitchen"
 ],
 "restaurant_diner": {
  "whitelist": {
   "brussels_sprouts.n.01": {
    "brussels_sprouts": {
     "hkwyzk": null,
     "mbkrxe": null,
     "siodbb": null,
     "vdamtq": null
    }
   },
   "carving_knife.n.01": {
    "carving_knife": {
     "zaihmr": null
    }
   },
   "chopping_board.n.01": {
    "chopping_board": {
     "mqsqhl": null
    },
    "cutting_board": {
     "tcdrzs": null
    }
   },
   "cookie_sheet.n.01": {
    "baking_sheet": {
     "yhurut": null
    }
   },
   "half__brussels_sprouts.n.01": {
    "half_brussels_sprouts": {
     "txelwc": null,
     "wbisku": null
    }
   },
   "tupperware.n.01": {
    "tupperware": {
     "mkstwr": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(future half__brussels_sprouts.n.01_1)
(future half__brussels_sprouts.n.01_2)
(future half__brussels_sprouts.n.01_3)
(future half__brussels_sprouts.n.01_4)
(future half__brussels_sprouts.n.01_5)
(future half__brussels_sprouts.n.01_6)
(future half__brussels_sprouts.n.01_7)
(future half__brussels_sprouts.n.01_8)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom oven.n.01_1 kitchen)
(inside brussels_sprouts.n.01_1 tupperware.n.01_1)
(inside brussels_sprouts.n.01_2 tupperware.n.01_1)
(inside brussels_sprouts.n.01_3 tupperware.n.01_1)
(inside brussels_sprouts.n.01_4 tupperware.n.01_1)
(inside tupperware.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop carving_knife.n.01_1 chopping_board.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop cookie_sheet.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching carving_knife.n.01_1 chopping_board.n.01_1)
(touching chopping_board.n.01_1 carving_knife.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching cookie_sheet.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 cookie_sheet.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 505.25 s (range 340.47-813.6). Skills per demo 48.0 (range 42-54). 162 distinct skill orders; the most common one covers 3% of demos.

Most common skill counts per demo (4% of demos): pick up from x15, place on x11, move to x9, chop x4, close door x2, open door x2, place on next to x2, place in x1, pour x1, push to x1, turn on switch x1.

Representative demo `episode_00950990.json` (593.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the electric refrigerator` (0.0-27.0 s)
2. `open the door of the electric refrigerator` (27.0-46.0 s)
3. `pick up the tupperware from the electric refrigerator` (46.0-69.0 s)
4. `close the door of the electric refrigerator` (69.0-92.0 s)
5. `move to the commercial kitchen table` (92.0-107.0 s)
6. `place the tupperware on the commercial kitchen table` (107.0-114.0 s)
7. `move to the carving knife` (114.0-144.0 s)
8. `pick up the carving knife from the cutting board` (144.0-155.0 s)
9. `push the cutting board to the commercial kitchen table` (155.0-167.0 s)
10. `pick up the cutting board from the commercial kitchen table` (167.0-210.9 s)
11. `move to the tupperware` (210.9-224.4 s)
12. `place the cutting board on the commercial kitchen table next to the tupperware` (224.4-228.0 s)
13. `move to the baking sheet` (228.0-233.0 s)
14. `pick up the baking sheet from the commercial kitchen table` (233.0-255.0 s)
15. `place the baking sheet on the commercial kitchen table next to the cutting board` (255.0-274.0 s)
16. `move to the tupperware` (274.0-283.0 s)
17. `pick up the tupperware from the commercial kitchen table` (283.0-288.0 s)
18. `pour the brussels sprouts and brussels sprouts and brussels sprouts and brussels sprouts into the tupperware` (288.0-291.0 s)
19. `place the tupperware on the commercial kitchen table` (291.0-298.0 s)
20. `pick up the brussels sprouts from the cutting board` (298.0-311.2 s)
21. `chop the carving knife with the brussels sprouts` (308.0-315.0 s)
22. `place the half brussels sprouts on the baking sheet` (315.0-321.9 s)
23. `pick up the half brussels sprouts from the cutting board` (321.9-326.6 s)
24. `place the half brussels sprouts on the baking sheet` (326.6-330.1 s)
25. `pick up the brussels sprouts from the cutting board` (330.1-340.3 s)
26. `chop the carving knife with the brussels sprouts` (340.3-346.0 s)
27. `place the half brussels sprouts on the baking sheet` (346.0-353.4 s)
28. `pick up the half brussels sprouts from the cutting board` (353.4-358.2 s)
29. `place the half brussels sprouts on the baking sheet` (358.2-363.5 s)
30. `pick up the brussels sprouts from the cutting board` (363.5-379.5 s)
31. `chop the carving knife with the brussels sprouts` (379.5-382.0 s)
32. `place the half brussels sprouts on the baking sheet` (382.0-389.1 s)
33. `pick up the half brussels sprouts from the cutting board` (389.1-393.7 s)
34. `place the half brussels sprouts on the baking sheet` (393.7-399.9 s)
35. `pick up the brussels sprouts from the cutting board` (399.9-418.8 s)
36. `chop the carving knife with the brussels sprouts` (418.8-421.7 s)
37. `place the half brussels sprouts on the baking sheet` (421.7-428.2 s)
38. `pick up the half brussels sprouts from the cutting board` (428.2-435.3 s)
39. `place the half brussels sprouts on the baking sheet` (435.3-443.5 s)
40. `place the carving knife on the cutting board` (443.5-456.0 s)
41. `move to the oven` (456.0-481.0 s)
42. `open the door of the oven` (481.0-504.0 s)
43. `move to the baking sheet` (504.0-521.0 s)
44. `pick up the baking sheet from the commercial kitchen table` (521.0-537.0 s)
45. `move to the oven` (537.0-551.0 s)
46. `place the baking sheet in the oven` (551.0-568.0 s)
47. `close the door of the oven` (568.0-582.0 s)
48. `turn on the oven` (582.0-593.0 s)

Mean duration per skill in this task: chop 5.7 s, close door 18.9 s, move to 15.2 s, open door 24.6 s, pick up from 9.3 s, place in 19.2 s, place on 5.8 s, place on next to 10.5 s, pour 9.5 s, push to 20.3 s, turn on switch 9.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the half brussels sprouts on the baking sheet` | 1538 |
| `pick up the half brussels sprouts from the cutting board` | 956 |
| `pick up the brussels sprouts from the cutting board` | 800 |
| `chop the carving knife with the brussels sprouts` | 800 |
| `move to the oven` | 402 |
| `place the tupperware on the commercial kitchen table` | 400 |
| `pick up the baking sheet from the commercial kitchen table` | 400 |
| `move to the baking sheet` | 382 |
| `move to the tupperware` | 359 |
| `move to the electric refrigerator` | 222 |
| `move to the commercial kitchen table` | 217 |
| `open the door of the electric refrigerator` | 200 |
| `pick up the tupperware from the electric refrigerator` | 200 |
| `close the door of the electric refrigerator` | 200 |
| `pick up the carving knife from the cutting board` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/95_cook_brussels_sprouts.json`. Planner notes: `task_docs/notes/95_cook_brussels_sprouts.md`.
