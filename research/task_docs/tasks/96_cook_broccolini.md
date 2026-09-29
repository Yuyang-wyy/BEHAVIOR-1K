# 96 · Cook Broccolini

Task name `cook_broccolini`, task index 96.

> Cook the broccolini in the frying pan on the stove.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | kitchen |
| rooms loaded | kitchen_0 |
| human demo length | 153.9 s mean (4617 steps) |
| episode time limit | 230.9 s (6926 steps at 30 Hz) |
| human base travel | 10.8674 m |
| goal literals (best ground option) | 11 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.18; ft40k@local Q=0.18 |
| demo video | https://www.youtube.com/embed/NXoYiAs_KCs |

## Planner notes

**Tier:** D. It needs cooking on top of pick-and-place. The demo shortcut makes it short: pour the whole plate into the pan, move the pan to the stove, turn the stove on. That is 9 skills and about 150 s.

### Goal in plain words

- All 3 broccolini and both garlic cloves must be resting on the frying pan and be cooked.
- The frying pan must be on the stove (`stove_ykretu_0`).
- The goal does not require the stove to stay on or be switched off.
- The plate is only the starting support.

### Q traps

- There are 11 literals and all score (0/11 true at reset). ft40k got 2/11 = 0.18 on instance 311. Which two is not recorded here.
- **Heat reaches the food, not the pan** (PREDICATES §2). Each food item's collision shape must be within 0.2 m of the stove's heat-source point.
- **Only one burner heats and only one knob toggles (derived from source).** The stove asset has 6 `heatsource` and 6 `togglebutton` meta links. `LinkBasedStateMixin.link` returns only the **first** link found (`link_based_state_mixin.py`, `next(iter(self.links.values()))`), and both `ToggledOn` and `HeatSourceOrSink` use that one. Which burner and knob come first is unverified.
  - The demos all end with `turn on the stove` after `place the frying pan on the stove`, so copying the demo placement is the safest bet.
- **Height (rough, derived).** From the asset metadata, the heat point sits about 0.16 m below the cooktop surface. Food in a pan is then only just inside the 0.2 m sphere, and only near the burner centre. Keep the pan centred on the active burner and the food spread flat in the pan, not piled at the rim.
- **`ontop X pan`** needs the item touching the pan, with the pan under its centre (§4). An item on top of another item (a clove on a broccolini) does not count. It needs direct contact with the pan.
- `cooked` latches (§15). Once 58 °C is reached, an item stays cooked even if the pan is later moved. It still has to be on the pan at the end.

### Minimal plan

1. `move to the plate`. Done when the plate with 5 items is centred on the commercial kitchen table. About 24 s.
2. `pick up the plate from the commercial kitchen table`. Done when the plate is lifted level with the items still on it. About 15 s.
3. `move to the frying pan`. About 24 s.
4. `pour the broccolini`. This is the demos' exact wording. Done when all 3 broccolini and 2 cloves are visible inside the pan. About 7 s.
5. `place the plate on the commercial kitchen table`. About 9 s.
6. `pick up the frying pan from the commercial kitchen table`. Grasp the pan's handle. About 15 s.
7. `move to the stove`. Keep the pan level and low. About 24 s.
8. `place the frying pan on the stove`. Done when the pan is resting flat on a burner. About 9 s.
9. `turn on the stove`. Done when a knob's toggle marker turns green. The episode should end within a second if all items are within range. About 17 s.

- Totals: about 145 s against a 230.9 s limit.

### What the demos do differently

- The demos match this plan (the modal order covers 57%).
- Every demo pours once (`pour the broccolini` appears 200 times in 200 demos). The other 5 orders differ only in extra `move to` steps.
- Nothing in the demos is superfluous except possibly putting the plate back, which frees the hand for the pan.

### Hard parts and hacks

- **Pouring 5 small items** (broccolini 0.088 x 0.044 x 0.041 m; clove 0.016 x 0.027 x 0.006 m) from a 0.30 m plate into a 0.28 m-wide pan. Cloves are light and scatter. Check all 5 are in the pan before lifting it. A stray clove costs 2 literals.
- **Carrying the loaded pan** (0.49 m including the handle) 1.5-4.6 m to the stove. Tilting or jerking spills items. Drive slowly with the pan low.
- If the stove is on and the episode does not end, some item is out of range or off the pan. Items are hard to re-grasp inside a hot pan. Try nudging the pan so it is centred on the burner whose marker is lit (unverified that the marker shows which burner heats).
- The plate is 0.297 x 0.297 x 0.018 m, so only a rim grasp works.

### Hints for the VLM

- The scene is a restaurant kitchen. The only stove is the 6-burner range (0.71 x 0.90 x 1.03 m). Flat-top grills, a deep fryer and an oven are distractors. Do not put the pan on a grill.
- The plate with its 5 items and the frying pan both start on a commercial kitchen table. The robot starts 1.4-4.7 m away.
- Done: the pan rests on the stove top with 3 broccolini and 2 cloves inside it, and a stove knob marker is green.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop clove.n.03_1 frying_pan.n.01_1)` | no | yes |
| `(cooked clove.n.03_1)` | no | yes |
| `(ontop clove.n.03_2 frying_pan.n.01_1)` | no | yes |
| `(cooked clove.n.03_2)` | no | yes |
| `(ontop broccolini.n.01_2 frying_pan.n.01_1)` | no | yes |
| `(cooked broccolini.n.01_2)` | no | yes |
| `(ontop broccolini.n.01_3 frying_pan.n.01_1)` | no | yes |
| `(cooked broccolini.n.01_3)` | no | yes |
| `(ontop broccolini.n.01_1 frying_pan.n.01_1)` | no | yes |
| `(cooked broccolini.n.01_1)` | no | yes |
| `(ontop frying_pan.n.01_1 stove.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and
            (forall
                (?clove.n.03 - clove.n.03)
                (and
                    (ontop ?clove.n.03 ?frying_pan.n.01_1)
                    (cooked ?clove.n.03)
                )
            )
            (forall
                (?broccolini.n.01 - broccolini.n.01)
                (and
                    (ontop ?broccolini.n.01 ?frying_pan.n.01_1)
                    (cooked ?broccolini.n.01)
                )
            )
            (ontop ?frying_pan.n.01_1 ?stove.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `broccolini.n.01_1` | broccolini_80 | broccolini / rlsytp | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.4 m (range 1.51-4.62) | yes, spread 2.36 m |
| `broccolini.n.01_2` | broccolini_79 | broccolini / rlsytp | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.35 m (range 1.55-4.62) | yes, spread 2.43 m |
| `broccolini.n.01_3` | broccolini_78 | broccolini / rlsytp | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.34 m (range 1.49-4.58) | yes, spread 2.52 m |
| `frying_pan.n.01_1` | frying_pan_77 | frying_pan / hzspwg | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.2 m (range 1.42-4.23) | yes, spread 2.22 m |
| `clove.n.03_1` | garlic_clove_76 | garlic_clove / saombi | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.39 m (range 1.5-4.67) | yes, spread 2.56 m |
| `clove.n.03_2` | garlic_clove_75 | garlic_clove / saombi | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.32 m (range 1.5-4.72) | yes, spread 2.37 m |
| `plate.n.04_1` | plate_74 | plate / fkpaie | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | 3.35 m (range 1.55-4.59) | yes, spread 2.38 m |
| `stove.n.01_1` | stove_ykretu_0 | stove / ykretu | kitchen_0 | low (0.25-0.6 m), z 0.58 | 4.31 m (range 3.05-5.47) | no (fixed) |
| `countertop.n.01_1` | commercial_kitchen_table_vxvtec_0 | commercial_kitchen_table / vxvtec | kitchen_0 | low (0.25-0.6 m), z 0.54 | 2.95 m (range 2.33-3.67) | no |
| `floor.n.01_1` | floors_vikfyd_0 | floors / vikfyd | kitchen_0 | floor, z 0.0 | 2.4 m (range 1.82-3.48) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "restaurant_diner": {
  "whitelist": {
   "broccolini.n.01": {
    "broccolini": {
     "rlsytp": null
    }
   },
   "clove.n.03": {
    "garlic_clove": {
     "saombi": null
    }
   },
   "frying_pan.n.01": {
    "frying_pan": {
     "hzspwg": null
    }
   },
   "plate.n.04": {
    "plate": {
     "fkpaie": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom stove.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop broccolini.n.01_1 plate.n.04_1)
(ontop broccolini.n.01_2 plate.n.04_1)
(ontop broccolini.n.01_3 plate.n.04_1)
(ontop clove.n.03_1 plate.n.04_1)
(ontop clove.n.03_2 plate.n.04_1)
(ontop frying_pan.n.01_1 countertop.n.01_1)
(ontop plate.n.04_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching broccolini.n.01_1 plate.n.04_1)
(touching broccolini.n.01_2 plate.n.04_1)
(touching broccolini.n.01_3 plate.n.04_1)
(touching clove.n.03_1 plate.n.04_1)
(touching clove.n.03_2 plate.n.04_1)
(touching countertop.n.01_1 frying_pan.n.01_1)
(touching countertop.n.01_1 plate.n.04_1)
(touching floor.n.01_1 agent.n.01_1)
(touching frying_pan.n.01_1 countertop.n.01_1)
(touching plate.n.04_1 broccolini.n.01_1)
(touching plate.n.04_1 broccolini.n.01_2)
(touching plate.n.04_1 broccolini.n.01_3)
(touching plate.n.04_1 clove.n.03_1)
(touching plate.n.04_1 clove.n.03_2)
(touching plate.n.04_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 152.28 s (range 81.43-241.83). Skills per demo 9.0 (range 9-11). 6 distinct skill orders; the most common one covers 57% of demos.

Most common skill counts per demo (58% of demos): move to x3, pick up from x2, place on x2, pour x1, turn on switch x1.

Representative demo `episode_00960840.json` (143.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the commercial kitchen table` (0.0-36.0 s)
2. `pick up the plate from the commercial kitchen table` (36.0-51.0 s)
3. `move to the frying pan` (51.0-71.0 s)
4. `pour the broccolini` (71.0-78.0 s)
5. `place the plate on the commercial kitchen table` (78.0-86.0 s)
6. `pick up the frying pan from the commercial kitchen table` (86.0-98.1 s)
7. `move to the stove` (98.1-121.0 s)
8. `place the frying pan on the stove` (121.0-126.4 s)
9. `turn on the stove` (126.4-138.2 s)

Mean duration per skill in this task: move to 23.7 s, pick up from 14.9 s, place on 9.1 s, pour 7.2 s, turn on switch 16.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the frying pan` | 281 |
| `move to the stove` | 203 |
| `pick up the plate from the commercial kitchen table` | 200 |
| `pour the broccolini` | 200 |
| `place the plate on the commercial kitchen table` | 200 |
| `pick up the frying pan from the commercial kitchen table` | 200 |
| `place the frying pan on the stove` | 200 |
| `turn on the stove` | 200 |
| `move to the plate` | 199 |
| `move to the commercial kitchen table` | 5 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/96_cook_broccolini.json`. Planner notes: `task_docs/notes/96_cook_broccolini.md`.
