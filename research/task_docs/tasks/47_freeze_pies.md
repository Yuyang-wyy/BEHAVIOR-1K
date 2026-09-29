# 47 · Freeze Pies

Task name `freeze_pies`, task index 47.

> In the kitchen, take the two apple pies from the plates on the countertop, put each pie into a separate tupperware container taken from the cabinet, place both tupperwares inside the refrigerator, close the refrigerator, and leave them until the pies are frozen.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 415.2 s mean (12455 steps) |
| episode time limit | 622.8 s (18682 steps at 30 Hz) |
| human base travel | 35.4388 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.857 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114061625 |

## Planner notes

**Tier:** D — freeze two pies in the fridge, after four container moves: pie into tupperware, tupperware into fridge. The pies are too wide for the jaws.

### Goal in plain words

- Each apple pie must be inside its own tupperware, and it does not matter which pie goes in which (`forpairs`, 2 ground options).
- Both tupperwares must be inside the fridge `fridge_dszchb_0`.
- Both pies must be `frozen` at the final step, meaning their **current** temperature is at most 0 °C. This is not latched (§16).
- The fridge must be closed.

**Cold source:** the fridge only (-18 °C, rate 0.1, needs closed + Inside; T_ss ≈ -11.2 °C). **Containers:** the two tupperwares from the bottom cabinet. The plates and the cabinet doors are not in the goal.

### Q traps

- 7 literals. `not open fridge` is true at start, so it never scores. Max partial Q is 6/7 = 0.857 (page is right).
- **Frozen needs the door shut.** The fridge cools only while it is closed within 5 % (§2, §6). An open door means no cooling. A pie taken out, or a door left ajar, warms back above 0 °C within about 20 s (§16).
- Pies start at 1.3 °C in all 20 instances, so they are not frozen at reset. By the time they are loaded they will have warmed toward 23 °C. From there, freezing takes about 9 s with the door closed (§16). Success fires on the first step when everything holds, so after closing the fridge just wait about 10-15 s.
- `inside pie tupperware` checks only the pie's AABB centre in the tupperware volume (§3). A pie resting tilted on the rim does not count.
- Cold reaches a pie in a tupperware as long as the pie's own centre is inside the fridge volume (§2). Door bins are not verified to have volume, so use the shelves.

### Minimal plan

This order loads the empty tupperwares into the fridge first, then the pies straight into them. It avoids carrying a loaded tupperware. The order is derived, not demo order.

1. `move to the bottom cabinet no top`, then `open the door of the second_right_door bottom cabinet no top` (the door name varies: `first_left_door`, `second_left_door`, `second_right_door` or `first_right_door`) — the tupperware is visible on a shelf. ~11 s + ~32 s.
2. `pick up the tupperware from the high_level bottom cabinet no top` — ~18 s. Leave the cabinet door open, since it is not in the goal (saves ~17 s per door).
3. Repeat steps 1-2 for the second tupperware, with the other hand. It may be behind another door.
4. `move to the fridge`, `open the door of the fridge` — ~11 s + ~32 s.
5. `place the tupperware in the middle_level fridge`, then `place the tupperware in the high_level fridge` — both on shelves, open side up. ~9 s each.
6. `move to the plate`, `pick up the apple pie from the plate` — ~11 s + ~18 s. Pick the second pie with the other hand.
7. `move to the fridge`, `place the apple pie in the tupperware` twice — each pie flat inside a tupperware. ~9 s each. Closest trained prompt: the demo places pies into tupperwares on the countertop.
8. `close the door of the fridge` — door flush. ~17 s. Wait about 15 s for the pies to freeze.

The plan takes about 280 s against a 623 s limit. Demo order also works: pies into tupperwares on the countertop, then `pick up the tupperware from the countertop` and `place the tupperware in the high_level fridge`.

### What the demos do differently

- They open and **close** the cabinet door for each tupperware (~30 s each round). Closing is not needed.
- They set the tupperwares on the countertop, load the pies there, then carry the loaded tupperwares to the fridge.
- Which cabinet door hides a tupperware varies by instance. The demos name all four doors about equally often.

### Hard parts and hacks

- **Pie grasp.** Each pie is 173 x 171 x 37 mm and lies flat on a plate. The 37 mm thickness can only be straddled from the side, which a top-down grasp cannot do. The pie is realistically not graspable. Without it, the best reachable Q is the two `tupperware in fridge` literals, 2/7 ≈ 0.29.
- **Tupperware** (`mkstwr`, scaled here to 250 x 250 x 100 mm) is an open box. A grasp must close on its thin wall at the rim (wall thickness not verified). Tupperwares sit on cabinet shelves at z 0.19-0.63, so this is a low reach.
- The fridge is single-door (`dszchb`, one joint) and starts closed in every instance. The cabinet `gjeoer` has 4 doors, all closed at start.
- Keep the tupperwares level. A pie in a tilted tupperware slides out.

### Hints for the VLM

- Kitchen of `house_single_floor`. The pies are on two plates on `countertop_kelzer_0` along the sink wall. The fridge is at the right end of that wall (7.8, -2.0). The tupperwares are in the long low cabinet `bottom_cabinet_no_top_gjeoer_0` under the counter along the x ≈ 4.1 wall. That is the one with the burner and microwave on top, not the sink wall.
- A tupperware is a clear or white square box without a lid. Two are in the scene.
- Done: two pies in two tupperwares on fridge shelves, door flush, about 15 s elapsed. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside apple_pie.n.01_2 tupperware.n.01_2)` | no | yes |
| `(inside apple_pie.n.01_1 tupperware.n.01_1)` | no | yes |
| `(inside tupperware.n.01_2 electric_refrigerator.n.01_1)` | no | yes |
| `(inside tupperware.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(frozen apple_pie.n.01_2)` | no | yes |
| `(frozen apple_pie.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

The goal has 2 ground options (7 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forpairs 
                (?apple_pie.n.01 - apple_pie.n.01) 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?apple_pie.n.01 ?tupperware.n.01)
            ) 
            (forall 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?tupperware.n.01 ?electric_refrigerator.n.01_1)
            ) 
            (forall 
                (?apple_pie.n.01 - apple_pie.n.01) 
                (frozen ?apple_pie.n.01)
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
| `apple_pie.n.01_1` | apple_pie_235 | apple_pie / rpdhbr | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.26 m (range 1.13-3.76) | yes, spread 2.72 m |
| `apple_pie.n.01_2` | apple_pie_234 | apple_pie / rpdhbr | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.33 m (range 0.76-3.49) | yes, spread 2.73 m |
| `plate.n.04_1` | plate_233 | plate / bgxzec | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 2.26 m (range 1.13-3.77) | yes, spread 2.73 m |
| `plate.n.04_2` | plate_232 | plate / bgxzec | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 2.33 m (range 0.76-3.49) | yes, spread 2.73 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.91 m (range 1.11-3.22) | no (fixed) |
| `tupperware.n.01_1` | tupperware_231 | tupperware / mkstwr | kitchen_0 | low (0.25-0.6 m), z 0.55 | 1.45 m (range 0.77-4.0) | yes, spread 2.4 m |
| `tupperware.n.01_2` | tupperware_230 | tupperware / mkstwr | kitchen_0 | low (0.25-0.6 m), z 0.37 | 1.49 m (range 0.87-4.08) | yes, spread 2.39 m |
| `cabinet.n.01_1` | bottom_cabinet_no_top_gjeoer_0 | bottom_cabinet_no_top / gjeoer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 1.53 m (range 0.98-3.8) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.51 m (range 0.72-2.02) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.97 m (range 0.96-4.08) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside tupperware.n.01_1 cabinet.n.01_1)
(inside tupperware.n.01_2 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop apple_pie.n.01_1 plate.n.04_1)
(ontop apple_pie.n.01_2 plate.n.04_2)
(ontop plate.n.04_1 countertop.n.01_1)
(ontop plate.n.04_2 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching apple_pie.n.01_1 plate.n.04_1)
(touching apple_pie.n.01_2 plate.n.04_2)
(touching countertop.n.01_1 plate.n.04_1)
(touching countertop.n.01_1 plate.n.04_2)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 apple_pie.n.01_1)
(touching plate.n.04_1 countertop.n.01_1)
(touching plate.n.04_2 apple_pie.n.01_2)
(touching plate.n.04_2 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 390.52 s (range 314.5-982.17). Skills per demo 27.0 (range 21-28). 14 distinct skill orders; the most common one covers 53% of demos.

Most common skill counts per demo (55% of demos): move to x9, pick up from x6, place in x4, close door x3, open door x3, place on x2.

Representative demo `episode_00470960.json` (391.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bottom cabinet no top` (0.0-14.1 s)
2. `open the door of the second_right_door bottom cabinet no top` (14.1-40.0 s)
3. `pick up the tupperware from the high_level bottom cabinet no top` (40.0-56.3 s)
4. `close the door of the second_right_door bottom cabinet no top` (56.3-71.2 s)
5. `move to the countertop` (71.2-83.9 s)
6. `place the tupperware on the countertop` (83.9-89.8 s)
7. `pick up the apple pie from the plate` (89.8-118.8 s)
8. `place the apple pie in the tupperware` (118.8-128.4 s)
9. `move to the bottom cabinet no top` (128.4-134.8 s)
10. `open the door of the second_left_door bottom cabinet no top` (134.8-166.7 s)
11. `pick up the tupperware from the high_level bottom cabinet no top` (166.7-179.3 s)
12. `close the door of the second_left_door bottom cabinet no top` (179.3-191.4 s)
13. `move to the countertop` (191.4-204.9 s)
14. `place the tupperware on the countertop` (205.0-211.1 s)
15. `move to the plate` (211.1-215.6 s)
16. `pick up the apple pie from the plate` (215.9-228.6 s)
17. `place the apple pie in the tupperware` (228.6-239.9 s)
18. `move to the fridge` (240.1-252.4 s)
19. `open the door of the fridge` (252.4-286.0 s)
20. `move to the tupperware` (286.0-303.2 s)
21. `pick up the tupperware from the countertop` (303.2-311.7 s)
22. `move to the tupperware` (311.7-314.9 s)
23. `pick up the tupperware from the countertop` (314.9-321.8 s)
24. `move to the fridge` (321.8-339.1 s)
25. `place the tupperware in the middle_level fridge` (339.1-349.6 s)
26. `place the tupperware in the high_level fridge` (349.7-361.8 s)
27. `close the door of the fridge` (361.8-391.3 s)

Mean duration per skill in this task: close door 17.1 s, move to 11.3 s, open door 32.1 s, pick up from 18.3 s, place in 9.1 s, place on 8.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the tupperware on the countertop` | 400 |
| `move to the fridge` | 400 |
| `place the apple pie in the tupperware` | 399 |
| `pick up the tupperware from the high_level bottom cabinet no top` | 397 |
| `pick up the apple pie from the plate` | 395 |
| `pick up the tupperware from the countertop` | 395 |
| `move to the bottom cabinet no top` | 393 |
| `move to the countertop` | 393 |
| `move to the tupperware` | 341 |
| `open the door of the fridge` | 200 |
| `close the door of the fridge` | 199 |
| `place the tupperware in the high_level fridge` | 197 |
| `place the tupperware in the middle_level fridge` | 196 |
| `move to the apple pie` | 158 |
| `close the door of the second_right_door bottom cabinet no top` | 113 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/47_freeze_pies.json`. Planner notes: `task_docs/notes/47_freeze_pies.md`.
