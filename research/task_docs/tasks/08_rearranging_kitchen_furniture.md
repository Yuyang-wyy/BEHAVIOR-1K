# 08 · Rearranging Kitchen Furniture

Task name `rearranging_kitchen_furniture`, task index 8.

> Move the toaster, food processor, and French press from the kitchen countertop into the same kitchen cabinet, and make sure that cabinet is closed at the end.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 298.1 s mean (8943 steps) |
| episode time limit | 447.2 s (13414 steps at 30 Hz) |
| human base travel | 25.8899 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.75 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114056046 |

## Planner notes

**Tier:** C. Three countertop appliances must go into a wall-mounted top cabinet (root z 1.89 m) behind two hinged doors, then both doors must be shut.

### Goal in plain words

- Toaster, food processor and French press must all end inside the same cabinet.
- Either of the two top cabinets counts (`exists`, 2 ground options). They are the only cabinets in the kitchen (template init_info: 2 `top_cabinet`, no bottom cabinets).
- That cabinet must be closed at the end: both its doors within 5 % of closed (PREDICATES.md §6).
- Splitting items across the two cabinets scores only the items in the better one.

### Q traps

- 4 literals. `not open cabinet` is true at reset (both joints ~0 in the template and all 20 instances), so it never scores. Max partial Q = 0.75.
- Full success needs the doors closed; closing earns no partial Q but is the only route to 1.0.
- Open both doors of one cabinet only. Opening the other cabinet adds nothing.
- Closing a door onto an item can push its centre out of the volume (§3). Push items well back before closing.
- ft40k scored Q=0.5 on 311 (2 of 3 inside), so the top cabinet volume works.
- Each cabinet has 2 joints; any door left ajar breaks success.

### Minimal plan

1. `move to the top cabinet`. Done: base stopped below the cabinet, doors in view. ~10 s.
2. `open the door of the right_door top cabinet`. Done: right door swung clearly open. ~39 s.
3. `open the door of the left_door top cabinet`. ~39 s.
4. `move to the toaster`. ~10 s.
5. `pick up the toaster from the bar`. Done: gripper closed short of full, toaster lifted off the bar. ~15 s.
6. `move to the top cabinet`. ~10 s.
7. `place the toaster in the low_level top cabinet`. Done: gripper open, toaster on the lower shelf, arm withdrawn. ~18 s.
8. `move to the food processor`; `pick up the food processor from the bar`; `move to the top cabinet`; `place the food processor in the low_level top cabinet next to the right toaster`. ~50 s.
9. `move to the french press`; `pick up the french press from the bar`; `move to the top cabinet`; `place the french press in the low_level top cabinet next to the right food processor`. ~50 s.
10. `close the door of the right_door top cabinet`. Done: door flush with the frame in RGB/depth. ~18 s.
11. `close the door of the left_door top cabinet`. ~18 s.

Budget: human mean 298 s, limit 447 s. Door opening (~39 s each) is the costliest step.

### What the demos do differently

- 199/200 demos use `top_cabinet_tynnnw_1` (cabinet.n.01_2, y ~0.83); one used both. The goal accepts either one.
- 132 `turn to` segments across the 200 demos (`turn to the food processor` 72, `turn to the french press` 58) to reorient the item in hand. Only needed if the item will not fit through the doors.
- The "next to" placements are wording only; `nextto` is not in the goal.
- Some demos open the left door first. Order does not matter.

### Hard parts and hacks

- Height: the cabinet shelf is above shoulder level. Carrying an appliance extended high risks tipping the robot (robot fact).
- Grasp: object widths are unknown (no custom list). Humans pick all three directly from the bar with no push-to-edge. The French press likely has a handle (unverified). ft40k got two items in, so at least two are graspable in practice.
- Door opening needs the handle; handle width is unverified against the 44 mm limit.
- Placement depth: releasing on the shelf lip leaves the centre outside the volume or blocks the door.
- The French press position varies most (spread 1.95 m; x from ~5.8 to ~7.7 along the bar in instances). The toaster and food processor stay within ~0.35 m.
- Closing is push-only (§6), so a scripted close (push each door flat) is legal and cheap.

### Hints for the VLM

- Everything is in `kitchen_0`. The "countertop" is a bar (`bar_byvbuc_0`); a second bar exists in the kitchen as a distractor.
- The two top cabinets are identical models (tynnnw) side by side on the wall, ~1.2 m apart. Pick one and use it for all three items.
- Toaster, food processor and French press are the only instances of their categories in the scene.
- Other appliances nearby (microwave, oven, fridge, dishwasher) are not targets.
- Done looks like: bar empty of the three items, all three visible on the chosen cabinet's shelf, then both doors of that cabinet flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside toaster.n.02_1 cabinet.n.01_2)` | no | yes |
| `(inside food_processor.n.01_1 cabinet.n.01_2)` | no | yes |
| `(inside french_press.n.01_1 cabinet.n.01_2)` | no | yes |
| `(not open cabinet.n.01_2))` | yes | never (already true) |

The goal has 2 ground options (4 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?cabinet.n.01 - cabinet.n.01)
                (and
                    (inside toaster.n.02_1 ?cabinet.n.01)
                    (inside food_processor.n.01_1 ?cabinet.n.01)
                    (inside french_press.n.01_1 ?cabinet.n.01)
                    (not
                        (open ?cabinet.n.01)
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
| `toaster.n.02_1` | toaster_91 | toaster / kjwqav | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.97 m (range 1.57-6.51) | yes, spread 0.35 m |
| `food_processor.n.01_1` | food_processor_90 | food_processor / gamkbo | kitchen_0 | table/counter (0.6-1.1 m), z 0.99 | 4.16 m (range 1.81-6.65) | yes, spread 0.28 m |
| `french_press.n.01_1` | french_press_89 | french_press / zidmyo | kitchen_0 | table/counter (0.6-1.1 m), z 1.03 | 3.74 m (range 1.67-6.42) | yes, spread 1.95 m |
| `countertop.n.01_1` | bar_byvbuc_0 | bar / byvbuc | kitchen_0 | low (0.25-0.6 m), z 0.4 | 3.83 m (range 1.27-5.95) | no (fixed) |
| `cabinet.n.01_1` | top_cabinet_tynnnw_0 | top_cabinet / tynnnw | kitchen_0 | very high (>1.6 m), z 1.89 | 4.46 m (range 2.13-7.04) | no (fixed) |
| `cabinet.n.01_2` | top_cabinet_tynnnw_1 | top_cabinet / tynnnw | kitchen_0 | very high (>1.6 m), z 1.89 | 3.98 m (range 1.59-6.52) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.02 m (range 1.11-3.3) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 kitchen)
(inroom cabinet.n.01_2 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop food_processor.n.01_1 countertop.n.01_1)
(ontop french_press.n.01_1 countertop.n.01_1)
(ontop toaster.n.02_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 food_processor.n.01_1)
(touching countertop.n.01_1 french_press.n.01_1)
(touching countertop.n.01_1 toaster.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching food_processor.n.01_1 countertop.n.01_1)
(touching french_press.n.01_1 countertop.n.01_1)
(touching toaster.n.02_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 275.98 s (range 178.93-668.7). Skills per demo 17.0 (range 16-20). 14 distinct skill orders; the most common one covers 54% of demos.

Most common skill counts per demo (54% of demos): move to x7, pick up from x3, close door x2, open door x2, place in next to x2, place in x1.

Representative demo `episode_00080160.json` (271.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the top cabinet` (0.0-16.1 s)
2. `open the door of the right_door top cabinet` (16.1-55.3 s)
3. `open the door of the left_door top cabinet` (55.3-92.0 s)
4. `move to the bar` (92.0-101.4 s)
5. `pick up the toaster from the bar` (101.4-116.6 s)
6. `move to the top cabinet` (116.6-124.4 s)
7. `place the toaster in the low_level top cabinet` (124.4-137.4 s)
8. `move to the bar` (137.4-149.9 s)
9. `pick up the food processor from the bar` (149.9-166.8 s)
10. `move to the top cabinet` (166.8-173.8 s)
11. `place the food processor in the low_level top cabinet next to the right toaster` (173.8-190.1 s)
12. `move to the bar` (190.1-196.4 s)
13. `pick up the french press from the bar` (196.4-206.5 s)
14. `move to the top cabinet` (206.5-213.1 s)
15. `place the french press in the low_level top cabinet next to the right food processor` (213.1-228.8 s)
16. `close the door of the right_door top cabinet` (228.8-255.4 s)
17. `close the door of the left_door top cabinet` (255.4-271.0 s)

Mean duration per skill in this task: close door 18.2 s, move to 10.4 s, open door 38.6 s, pick up from 15.2 s, place in 17.6 s, place in next to 16.0 s, push to 11.3 s, turn to 21.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the top cabinet` | 799 |
| `open the door of the right_door top cabinet` | 200 |
| `pick up the food processor from the bar` | 200 |
| `move to the french press` | 200 |
| `pick up the french press from the bar` | 200 |
| `open the door of the left_door top cabinet` | 199 |
| `move to the toaster` | 199 |
| `pick up the toaster from the bar` | 199 |
| `close the door of the left_door top cabinet` | 198 |
| `close the door of the right_door top cabinet` | 198 |
| `move to the food processor` | 191 |
| `place the toaster in the low_level top cabinet` | 184 |
| `place the food processor in the low_level top cabinet next to the right toaster` | 150 |
| `place the french press in the low_level top cabinet next to the right food processor` | 145 |
| `turn to the food processor` | 72 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/08_rearranging_kitchen_furniture.json`. Planner notes: `task_docs/notes/08_rearranging_kitchen_furniture.md`.
