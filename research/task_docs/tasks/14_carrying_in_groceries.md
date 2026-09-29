# 14 · Carrying in Groceries

Task name `carrying_in_groceries`, task index 14.

> Take the sack of groceries out of the car trunk in the garage, bring it to the kitchen, and put both the tomato and the carton of milk into the refrigerator in the kitchen. When you're done, close the car trunk and make sure the refrigerator in the kitchen is closed.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage, kitchen |
| rooms loaded | corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 475.8 s mean (14274 steps) |
| episode time limit | 713.7 s (21412 steps at 30 Hz) |
| human base travel | 37.0952 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.75 |
| ground goal options | 1 |
| starts open (joint_pos > 0.02) | `car.n.01_1` in 20/20 instances |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.25; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114057919 |

## Planner notes

**Tier:** C — the tomato (0.069 m) and milk carton (0.067 x 0.099 x 0.174 m) are wider than the 44 mm jaw span, they start inside a paper bag inside the car trunk, and the fridge is 9-15 m away.

### Goal in plain words

The beefsteak tomato and the milk carton must both be inside the kitchen fridge (there is only one fridge in the kitchen, so the `exists` has one choice).
The car trunk must be closed and the fridge must be closed at the end.
The paper bag itself has no goal; it can be left anywhere.

### Q traps

- 4 literals. `not open fridge` is already true at reset (fridge joint_pos [0, 0] in all 20 instances), so it never scores. Max partial Q is 0.75; full success still needs the fridge closed.
- `not open car` DOES score: the trunk starts open (joint_pos 2.531 in the template and all 20 instances). Closing the trunk alone gives Q = 0.25. zs_pt50 scored exactly 0.25 on instance 311, most likely this way.
- Close the trunk only after the bag is out, or the groceries are locked in. If the grasp on the bag fails, close the trunk anyway to bank 0.25.
- The fridge is side-by-side (`left_door` and `right_door` links). `not open` fails if either door is past 5 % of its range (PREDICATES §6). Close the door you opened and check the other was not bumped.
- `inside` needs the AABB centre in the fridge's fillable volume. Door bins are not verified to have volume (PREDICATES §16); place on a shelf (`layer_4` / `layer_5` in the demo prompts).
- The two items can be on different shelves; both just need to be inside the same fridge.

### Minimal plan

Robot starts in the garage, 1.3-4.8 m from the bag. The garage-corridor door `door_bexenl_0` starts closed; every demo opens it.

1. `move to the paper bag` — bag centred in view inside the open trunk. ~28 s.
2. `pick up the paper bag from the car` — bag lifted clear of the trunk floor. ~16 s.
3. `close the lid of the car` — trunk lid visibly down and flush. ~34 s. Scores 1/4.
4. `move to the door`, `open the door of the door` — corridor visible through the doorway. ~28 s + 23 s.
5. `move to the breakfast table`, `place the paper bag on the breakfast table` — bag standing on the table, gripper open. ~28 s + 15 s.
6. `pick up the beefsteak tomato from the paper bag` — tomato in the gripper above the bag. ~16 s.
7. `move to the fridge`, `open the door of the right_door fridge` — right door swung wide. ~28 s + 23 s.
8. `place the beefsteak tomato in the layer_5 fridge` — tomato resting on a shelf, gripper out. ~16 s.
9. `move to the paper bag`, `pick up the paper bag from the breakfast table`, `tip over the paper bag`, `pour the carton of milk into the paper bag`, `place the paper bag on the breakfast table` — carton lying on the table. ~28 + 16 + 8 + 18 + 15 s. (The demo annotators called tipping the carton out a "pour"; copy the string as is.)
10. `pick up the carton of milk from the breakfast table`, `move to the fridge`, `place the carton of milk in the layer_4 fridge`. ~16 + 28 + 16 s.
11. `close the door of the right_door fridge` — door flush with the cabinet body. ~41 s.

Budget: about 520 s against a 714 s limit. Leave the right door open between steps 7 and 11.

### What the demos do differently

- 170/200 demos follow the plan above exactly (bag out, trunk shut, door, bag on table, tomato, tip bag, milk).
- About 20 demos hand the tomato from one arm to the other (`hand over the beefsteak tomato with the left`) to free a hand for the fridge door. Keep the right arm free instead.
- Picking the carton straight out of the bag, without tipping, is not in the demos.
- The paper bag is only a carrier. A shorter plan that the goal allows: take the bag straight to the fridge and pick items from it there. No demo does that, so the prompts would be out of distribution.

### Hard parts and hacks

- Tomato: 0.069 m sphere, wider than the 44 mm grasp span. The assisted grasp will not register across it; unverified whether a tip-of-finger pinch works.
- Milk carton: smallest side 0.067 m, also wider than the span.
- Paper bag: 0.12 x 0.18 x 0.29 m, no handle link in the asset. A grasp is possible only across a bag wall.
- Fridge door handle width is unknown.
- Given the grasp limits, the reliable Q is 0.25 from the trunk. Close it early.

### Hints for the VLM

- The car is the only car, in the garage, trunk already open with the brown paper bag inside at about 0.9 m.
- The kitchen has one fridge (tall, two vertical doors), one breakfast table, four straight chairs, a dishwasher, an oven and a microwave. Do not confuse the dishwasher or oven doors with the fridge.
- Done for the trunk: lid down, no gap at the rear. Done for the fridge: both doors flush, no light visible at the seam.
- Done for an item: visible resting on a fridge shelf inside the cabinet, not on a door shelf.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside beefsteak_tomato.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(inside carton__of__milk.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(not open car.n.01_1))` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?electric_refrigerator.n.01 - electric_refrigerator.n.01)
                (and
                    (inside ?beefsteak_tomato.n.01_1 ?electric_refrigerator.n.01)
                    (inside ?carton__of__milk.n.01_1 ?electric_refrigerator.n.01) 
                )
            )
            (not
                (open car.n.01_1)
            )
            (not
                (open electric_refrigerator.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `car.n.01_1` | car_ssxsje_0 | car / ssxsje | garage_0 | table/counter (0.6-1.1 m), z 0.67 | 3.23 m (range 1.88-5.11) | no (fixed) |
| `sack.n.01_1` | paper_bag_81 | paper_bag / bzsxgw | garage_0 | table/counter (0.6-1.1 m), z 0.88 | 2.92 m (range 1.29-4.77) | yes, spread 0.89 m |
| `beefsteak_tomato.n.01_1` | beefsteak_tomato_80 | beefsteak_tomato / altlfz | garage_0 | table/counter (0.6-1.1 m), z 0.97 | 2.91 m (range 1.31-4.76) | yes, spread 0.91 m |
| `carton__of__milk.n.01_1` | carton_of_milk_79 | carton_of_milk / xmugpm | garage_0 | table/counter (0.6-1.1 m), z 0.86 | 2.92 m (range 1.29-4.76) | yes, spread 0.88 m |
| `electric_refrigerator.n.01_1` | fridge_petcxr_0 | fridge / petcxr | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 12.71 m (range 9.32-15.31) | no (fixed) |
| `floor.n.01_1` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 1.9 m (range 0.58-3.47) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom car.n.01_1 garage)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 garage)
(inside beefsteak_tomato.n.01_1 sack.n.01_1)
(inside carton__of__milk.n.01_1 sack.n.01_1)
(inside sack.n.01_1 car.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(open car.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 463.17 s (range 372.0-664.47). Skills per demo 21.0 (range 20-24). 4 distinct skill orders; the most common one covers 87% of demos.

Most common skill counts per demo (87% of demos): move to x7, pick up from x4, open door x2, place in x2, place on x2, close door x1, close lid x1, pour x1, tip over x1.

Representative demo `episode_00142640.json` (454.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the paper bag` (0.8-15.5 s)
2. `pick up the paper bag from the car` (15.5-34.0 s)
3. `close the lid of the car` (34.0-64.1 s)
4. `move to the door` (64.1-84.9 s)
5. `open the door of the door` (84.9-98.2 s)
6. `move to the breakfast table` (98.2-158.3 s)
7. `place the paper bag on the breakfast table` (158.3-178.1 s)
8. `pick up the beefsteak tomato from the paper bag` (178.1-201.0 s)
9. `move to the fridge` (201.0-217.5 s)
10. `open the door of the right_door fridge` (217.5-246.1 s)
11. `place the beefsteak tomato in the layer_5 fridge` (246.1-259.1 s)
12. `move to the paper bag` (259.1-290.1 s)
13. `pick up the paper bag from the breakfast table` (290.1-301.6 s)
14. `tip over the paper bag` (301.6-308.1 s)
15. `pour the carton of milk into the paper bag` (310.7-327.9 s)
16. `place the paper bag on the breakfast table` (327.9-335.2 s)
17. `pick up the carton of milk from the breakfast table` (335.2-350.0 s)
18. `move to the fridge` (350.0-368.2 s)
19. `place the carton of milk in the layer_4 fridge` (368.2-380.9 s)
20. `move to the fridge` (380.9-413.8 s)
21. `close the door of the right_door fridge` (413.8-455.0 s)

Mean duration per skill in this task: close door 41.2 s, close lid 33.5 s, hand over 15.3 s, move to 28.0 s, open door 23.3 s, pick up from 15.9 s, place in 15.7 s, place on 14.7 s, pour 18.0 s, tip over 7.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the fridge` | 600 |
| `place the paper bag on the breakfast table` | 400 |
| `move to the paper bag` | 394 |
| `open the door of the right_door fridge` | 222 |
| `move to the breakfast table` | 204 |
| `pick up the paper bag from the car` | 200 |
| `close the lid of the car` | 200 |
| `move to the door` | 200 |
| `open the door of the door` | 200 |
| `pick up the beefsteak tomato from the paper bag` | 200 |
| `pick up the paper bag from the breakfast table` | 200 |
| `tip over the paper bag` | 200 |
| `pour the carton of milk into the paper bag` | 200 |
| `pick up the carton of milk from the breakfast table` | 200 |
| `place the beefsteak tomato in the layer_5 fridge` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/14_carrying_in_groceries.json`. Planner notes: `task_docs/notes/14_carrying_in_groceries.md`.
