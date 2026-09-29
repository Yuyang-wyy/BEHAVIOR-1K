# 17 · Bringing Water

Task name `bringing_water`, task index 17.

> Retrieve the two bottles from the refrigerator in the kitchen, bring them to the living room, and place both on the coffee table. Make sure the refrigerator is closed when you finish.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen, living_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 314.6 s mean (9438 steps) |
| episode time limit | 471.9 s (14157 steps at 30 Hz) |
| human base travel | 26.2495 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.667 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114058418 |

## Planner notes

**Tier:** B — two beer bottles (0.075 m body, 0.26 m tall) go from the fridge to a low coffee table. The body is wider than the 44 mm span; the grasp must go on the neck (neck width not in the asset metadata; unverified that it is under 44 mm).

### Goal in plain words

Both beer bottles must rest on the living-room coffee table (`coffee_table_rlsebe_0`, in living_room_0).
The bottles are interchangeable and any spot on the table top works.
The fridge must be closed at the end.

### Q traps

- 3 literals. `not open fridge` is already true at reset (fridge joint_pos 0.0 in all 20 instances), so it never scores. Max partial Q is 0.667, one bottle = 0.333.
- Full success still needs the fridge closed. Opening it and leaving it open caps Q at 0.667.
- The scene has three coffee tables: living_room_0 (the target), living_room_1 and garden_0. A bottle on the wrong coffee table scores 0.
- `ontop` needs direct contact with the table top (PREDICATES §4). A bottle that tips over and rolls off the 0.27 m-high table scores 0. Stand it upright near the table centre.
- Success is checked every step. If the fridge is closed first and the bottles are placed last, the episode ends with success on the second placement.

### Minimal plan

Robot starts in the kitchen, 1-4.4 m from the fridge. The target table is 3.8-7.6 m away.

1. `move to the fridge` — fridge door centred in view. ~47 s.
2. `open the door of the fridge` — single door swung wide, shelves visible. ~51 s.
3. `pick up the beer bottle from the middle_level fridge` (or `low_level` / `high_level`, whichever shelf the bottle is on) — bottle out of the fridge in the right gripper. ~27 s.
4. `hand over the beer bottle with the right` — bottle now in the left gripper, right gripper empty. ~11 s.
5. `pick up the beer bottle from the low_level fridge` (shelf as seen) — second bottle in the right gripper. ~27 s.
6. `close the door of the fridge` — door flush. ~22 s. Doing it here, with both hands full, saves the ~65 s return trip the demos make; no demo closes it at this point, so it is untested. If the arms cannot push the door with a bottle in hand, fall back to step 9.
7. `move to the coffee table` — low square table in the living room with sofas around it. ~47 s.
8. `place the beer bottle on the coffee table` twice — both bottles upright on the table, grippers open. ~19 s + 19 s.
9. (only if step 6 was skipped) `move to the fridge`, `close the door of the fridge`. ~47 s + 22 s.

Budget: about 250 s with step 6, 320 s without, against a 472 s limit.

### What the demos do differently

- 199/200 demos close the fridge only at the very end, after walking back from the living room.
- 119 demos use a right-to-left hand-over to pick both bottles with one arm reaching into the fridge; the rest pick one per hand directly.
- The shelf word in the pick prompt (`high_level`, `middle_level`, `low_level`) varies by instance; pick the one matching where the bottle is seen.

### Hard parts and hacks

- Grasp: the bottle body is 75 mm, too wide. The neck must be straddled. Reaching a neck inside a fridge shelf with shelves above is tight.
- Placing a tall bottle upright on a low (0.27 m) table requires lowering the arm far; the robot's trunk must bend. Laying the bottle on its side also scores, but it may roll off.
- Both hands are full on the way back, so closing the fridge needs a free arm or a push with the forearm or base.

### Hints for the VLM

- The fridge is the only fridge, in the kitchen: a single tall door (door link 1.37 m tall). The bottles are brown beer bottles inside.
- The target coffee table is the 0.98 m square low table in the living room with four sofas and a gas fireplace. The other living room (three sofas) has a different coffee table; do not use it. A third coffee table is in the garden.
- Done for each bottle: resting on the table top, not on a sofa or the floor. Done for the fridge: door flush with the body, no gap.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop bottle.n.01_1 coffee_table.n.01_1)` | no | yes |
| `(ontop bottle.n.01_2 coffee_table.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall
                (?bottle.n.01 - bottle.n.01)
                (ontop ?bottle.n.01 ?coffee_table.n.01_1)
            )
            (not
                (open ?electric_refrigerator.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `bottle.n.01_1` | beer_bottle_268 | beer_bottle / nigfha | kitchen_0 | low (0.25-0.6 m), z 0.58 | 2.84 m (range 1.04-4.61) | yes, spread 0.54 m |
| `bottle.n.01_2` | beer_bottle_267 | beer_bottle / nigfha | kitchen_0 | low (0.25-0.6 m), z 0.58 | 2.85 m (range 0.97-4.43) | yes, spread 0.56 m |
| `coffee_table.n.01_1` | coffee_table_rlsebe_0 | coffee_table / rlsebe | living_room_0 | floor, z 0.15 | 7.24 m (range 3.82-7.58) | no |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.78 m (range 1.06-4.39) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.63 m (range 0.65-2.83) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom coffee_table.n.01_1 living_room)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside bottle.n.01_1 electric_refrigerator.n.01_1)
(inside bottle.n.01_2 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 303.4 s (range 192.0-489.7). Skills per demo 10.0 (range 8-10). 4 distinct skill orders; the most common one covers 59% of demos.

Most common skill counts per demo (60% of demos): move to x3, pick up from x2, place on x2, close door x1, hand over x1, open door x1.

Representative demo `episode_00172620.json` (291.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (1.9-26.1 s)
2. `open the door of the fridge` (26.1-67.9 s)
3. `pick up the beer bottle from the high_level fridge` (68.0-84.8 s)
4. `hand over the beer bottle with the right` (84.9-93.5 s)
5. `pick up the beer bottle from the middle_level fridge` (93.6-111.4 s)
6. `move to the coffee table` (111.5-182.5 s)
7. `place the beer bottle on the coffee table` (182.5-202.8 s)
8. `place the beer bottle on the coffee table` (202.8-209.2 s)
9. `move to the fridge` (210.0-274.0 s)
10. `close the door of the fridge` (274.5-293.0 s)

Mean duration per skill in this task: close door 21.6 s, hand over 10.7 s, move to 47.0 s, open door 50.5 s, pick up from 26.6 s, place on 18.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the fridge` | 397 |
| `place the beer bottle on the coffee table` | 396 |
| `move to the coffee table` | 201 |
| `open the door of the fridge` | 200 |
| `close the door of the fridge` | 199 |
| `pick up the beer bottle from the low_level fridge` | 146 |
| `pick up the beer bottle from the middle_level fridge` | 144 |
| `hand over the beer bottle with the right` | 119 |
| `pick up the beer bottle from the high_level fridge` | 104 |
| `place the beer bottle on the fridge` | 4 |
| `pick up the beer bottle from the middle_level coffee table` | 2 |
| `pick up the beer bottle from the high_level beer bottle` | 1 |
| `pick up the low_level beer bottle from the low_level fridge` | 1 |
| `pick up the beer bottle from the high_level coffee table` | 1 |
| `close the door of the coffee table` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/17_bringing_water.json`. Planner notes: `task_docs/notes/17_bringing_water.md`.
