# 64 · Setting The Table

Task name `setting_the_table`, task index 64.

> Set the breakfast table with both plates, put one cupcake on each plate, and place a fork and a knife next to each plate.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | dining_room, kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 593.6 s mean (17808 steps) |
| episode time limit | 890.4 s (26712 steps at 30 Hz) |
| human base travel | 55.4631 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 8 |
| starts open (joint_pos > 0.02) | `cabinet.n.01_1` in 1/20 instances |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/Tkf34ap-z8U |

## Planner notes

**Tier:** C — eight pick-and-places across two rooms, with plates on a 1.53 m cabinet shelf behind two doors, cupcakes in a closed fridge, and cupcakes wider than the jaw span.

### Goal in plain words

Both plates must rest on the breakfast table in `dining_room_0`. Each plate needs its own cupcake on it, and its own fork and its own table knife `nextto` it (a perfect matching, so which fork goes with which plate is free). Nothing is said about closing the top cabinet or the fridge, so leaving them open costs nothing. Cutlery only needs to be beside a plate on the table, not on it.

### Q traps

- All 8 literals start false; max partial Q is 1.0 (page is right).
- Cupcake literals need their plate but not the table: a cupcake on a plate counts even if that plate is not yet on the table. Still, carrying a loaded plate is risky; place plates first.
- `nextto` for fork/knife vs plate: L/6 is about 3.4 cm (fork 0.20 x 0.03 x 0.02 m, knife 0.24 x 0.02 x 0.01 m, plate 0.17 x 0.17 x 0.02 m). The cutlery must lie almost touching the plate rim. A fork 10 cm away scores nothing.
- Cutlery must sit on the table at plate height. On a chair or the floor beside the table, the height gap kills `nextto` (PREDICATES §5).
- `forpairs` needs one distinct fork and one distinct knife per plate. Two forks beside plate A and none beside plate B scores only one fork literal.
- Knocking a plate while laying cutlery can shift the cupcake off it or push the plate away from placed cutlery; lay cutlery on the far side from the approach.
- Both top-cabinet doors start closed (joint_pos 0.0; 0.02 on one door in instance 312, still inside the 5 % band) and the fridge is closed in all 20 instances. They are not in the goal.

### Minimal plan

1. `move to the top cabinet` — the middle of three identical wall cabinets is in view. ~26 s.
2. `open the door of the top cabinet` (twice, one per door) — both doors swung open, plates visible on the shelf. ~22 s each.
3. `push the plate to the top cabinet`, then `pick up the plate from the top cabinet`; repeat for the second plate with the other hand — each plate lifted clear of the shelf. ~11 s + ~18 s each.
4. Skip `close the door of the top cabinet` (not in the goal; saves ~31 s).
5. `move to the breakfast table` — table top fills the lower image. ~26 s.
6. `place the plate on the breakfast table` twice — both plates flat on the table, at least ~0.4 m apart, hands empty. ~9 s each.
7. `move to the electric refrigerator`, `open the door of the electric refrigerator` — door open. ~26 s + ~22 s.
8. `pick up the cupcake from the electric refrigerator` twice, one per hand — both grippers holding. ~18 s each.
9. Skip `place the cupcake on the bar` and `close the door of the electric refrigerator` (they exist only to free a hand for closing; saves ~40 s).
10. `move to the breakfast table`, then `place the cupcake on the plate` twice — one cupcake centred on each plate. ~26 s + ~9 s each.
11. `move to the sink`, `pick up the tablefork from the sink`, `pick up the table knife from the sink` — one item per hand. ~26 s + ~18 s each.
12. `move to the breakfast table`, `place the tablefork on the breakfast table`, `place the table knife on the breakfast table` — both lying against the rim of the same plate, one each side. ~26 s + ~9 s each.
13. Repeat steps 11-12 for the second fork and knife at the other plate.

About 520 s against an 890 s limit, versus 594 s for the demo.

### What the demos do differently

- 197/200 close both cabinet doors and the fridge; the goal does not need it.
- 196/200 park one cupcake on the kitchen bar (`place the cupcake on the bar`) to free a hand for the fridge door, then pick it up again.
- Cutlery prompts say `place the tablefork on the breakfast table`, not "next to the plate". The planner must steer placement to the rim; there is no trained `place ... next to the plate` sentence for this task. Closest: `place the tablefork on the breakfast table`.
- 22 demos pick the first plate without the `push the plate to the top cabinet` step.

### Hard parts and hacks

- Plates: 170 x 170 x 19 mm, flat on a shelf at z 1.53 m. The only graspable part is the 19 mm rim, and a finger must get under it. That is why demos push each plate to the shelf edge first so the rim overhangs. High reach plus a loaded extended arm risks tipping.
- Cupcakes: asset bbox 96 x 97 x 56 mm, wider than the 44 mm jaw span on every axis. Demos pick them 400 times, so some narrower sub-part (likely the frosting top) must register; which one is unverified. Expect cupcake grasps to be the most failure-prone step.
- Cupcake shelf varies: z 0.50, 0.91 or 1.31 across instances, sometimes the two on different shelves.
- Cutlery: fork 28 mm and knife 22 mm wide, easy for the jaws. In 6 of 20 instances (303, 310, 313, 314, 315, 318) one or two forks or knives lie in the sink basin (z 0.74) rather than on the deck (z 0.90), which needs a deeper reach.
- Nextto precision is the main Q risk: ~3 cm tolerance. After release, check in depth that the cutlery touches or nearly touches the plate edge; re-push it with `push the tablefork to the plate` (no trained prompt; closest `push the plate to the top cabinet`) if not.
- Base travel is ~5 m each way between kitchen (y ≈ -2 to 0) and table (7.3, 3.5). Four round trips dominate the time; carry two items per trip always.

### Hints for the VLM

- Plates are in the middle one of three identical top cabinets (`top_cabinet_lkxmne_1`) on the kitchen wall at x ≈ 4.0; the others are at y -1.6 and +0.65 and are empty distractors.
- Cupcakes are in the single fridge at the end of the counter (x 7.8). Forks and knives lie on or in the only kitchen sink (drop-in sink, x 5.8).
- The breakfast table (1.16 x 2.9 m, top 0.78 m) is the only table in `dining_room_0`, surrounded by 6 chairs. The low coffee tables are in other rooms; do not use them.
- The kitchen bar (x 7.3, y 0.2) is a handy staging surface but is not part of the goal.
- Done: two plates on the table, each with a cupcake on top and a fork and knife lying right against its rim.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop plate.n.04_1 breakfast_table.n.01_1)` | no | yes |
| `(ontop plate.n.04_2 breakfast_table.n.01_1)` | no | yes |
| `(ontop cupcake.n.01_2 plate.n.04_1)` | no | yes |
| `(ontop cupcake.n.01_1 plate.n.04_2)` | no | yes |
| `(nextto tablefork.n.01_1 plate.n.04_1)` | no | yes |
| `(nextto tablefork.n.01_2 plate.n.04_2)` | no | yes |
| `(nextto table_knife.n.01_1 plate.n.04_1)` | no | yes |
| `(nextto table_knife.n.01_2 plate.n.04_2)` | no | yes |

The goal has 8 ground options (8 literals x8); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?plate.n.04 - plate.n.04) 
                (ontop ?plate.n.04 ?breakfast_table.n.01_1)
            )
            (forpairs 
                (?plate.n.04 - plate.n.04) 
                (?cupcake.n.01 - cupcake.n.01) 
                (ontop ?cupcake.n.01 ?plate.n.04)
            ) 
            (forpairs
                (?tablefork.n.01 - tablefork.n.01)
                (?plate.n.04 - plate.n.04)
                (nextto ?tablefork.n.01 ?plate.n.04)
            ) 
            (forpairs
                (?table_knife.n.01 - table_knife.n.01)
                (?plate.n.04 - plate.n.04)
                (nextto ?table_knife.n.01 ?plate.n.04)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `cupcake.n.01_1` | cupcake_250 | cupcake / mbhweg | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.17 m (range 0.85-3.32) | yes, spread 0.45 m |
| `cupcake.n.01_2` | cupcake_249 | cupcake / mbhweg | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.36 m (range 0.84-3.41) | yes, spread 0.43 m |
| `breakfast_table.n.01_1` | breakfast_table_rhjoby_0 | breakfast_table / rhjoby | dining_room_0 | table/counter (0.6-1.1 m), z 0.76 | 4.58 m (range 3.99-4.84) | no |
| `tablefork.n.01_1` | tablefork_248 | tablefork / flexrc | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.55 m (range 1.0-2.83) | yes, spread 0.63 m |
| `tablefork.n.01_2` | tablefork_247 | tablefork / flexrc | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.4 m (range 0.87-2.89) | yes, spread 0.59 m |
| `table_knife.n.01_1` | table_knife_246 | table_knife / jxdfyy | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.44 m (range 0.87-2.77) | yes, spread 0.45 m |
| `table_knife.n.01_2` | table_knife_245 | table_knife / jxdfyy | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.38 m (range 1.03-2.61) | yes, spread 0.61 m |
| `plate.n.04_1` | plate_244 | plate / aewthq | kitchen_0 | high (1.1-1.6 m), z 1.53 | 1.8 m (range 0.99-4.59) | yes, spread 0.76 m |
| `plate.n.04_2` | plate_243 | plate / aewthq | kitchen_0 | high (1.1-1.6 m), z 1.53 | 1.72 m (range 1.07-4.7) | yes, spread 0.79 m |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.36 m (range 0.94-3.44) | no (fixed) |
| `cabinet.n.01_1` | top_cabinet_lkxmne_1 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 1.76 m (range 1.05-4.65) | no (fixed) |
| `sink.n.01_1` | drop_in_sink_awvzkn_0 | drop_in_sink / awvzkn | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.48 m (range 1.04-3.02) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.43 m (range 0.7-2.15) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "dining_room",
  "kitchen"
 ],
 "house_single_floor": {
  "whitelist": {
   "cupcake.n.01": {
    "cupcake": {
     "mbhweg": null
    }
   },
   "plate.n.04": {
    "plate": {
     "aewthq": null
    }
   },
   "table_knife.n.01": {
    "table_knife": {
     "jxdfyy": null
    }
   },
   "tablefork.n.01": {
    "tablefork": {
     "flexrc": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom breakfast_table.n.01_1 dining_room)
(inroom cabinet.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom sink.n.01_1 kitchen)
(inside cupcake.n.01_1 electric_refrigerator.n.01_1)
(inside cupcake.n.01_2 electric_refrigerator.n.01_1)
(inside plate.n.04_1 cabinet.n.01_1)
(inside plate.n.04_2 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop table_knife.n.01_1 sink.n.01_1)
(ontop table_knife.n.01_2 sink.n.01_1)
(ontop tablefork.n.01_1 sink.n.01_1)
(ontop tablefork.n.01_2 sink.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching sink.n.01_1 table_knife.n.01_1)
(touching sink.n.01_1 table_knife.n.01_2)
(touching sink.n.01_1 tablefork.n.01_1)
(touching sink.n.01_1 tablefork.n.01_2)
(touching table_knife.n.01_1 sink.n.01_1)
(touching table_knife.n.01_2 sink.n.01_1)
(touching tablefork.n.01_1 sink.n.01_1)
(touching tablefork.n.01_2 sink.n.01_1)
```

## What the human demos did

200 annotated demos. Length 614.97 s (range 394.17-773.43). Skills per demo 34.0 (range 31-34). 11 distinct skill orders; the most common one covers 83% of demos.

Most common skill counts per demo (83% of demos): pick up from x9, place on x9, move to x8, close door x3, open door x3, push to x2.

Representative demo `episode_00642660.json` (611.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the top cabinet` (0.0-13.6 s)
2. `open the door of the top cabinet` (13.6-37.7 s)
3. `open the door of the top cabinet` (37.7-53.7 s)
4. `push the plate to the top cabinet` (53.7-66.1 s)
5. `pick up the plate from the top cabinet` (66.1-75.5 s)
6. `push the plate to the top cabinet` (75.5-92.9 s)
7. `pick up the plate from the top cabinet` (92.9-103.0 s)
8. `close the door of the top cabinet` (103.0-116.1 s)
9. `close the door of the top cabinet` (116.1-131.8 s)
10. `move to the breakfast table` (131.8-159.0 s)
11. `place the plate on the breakfast table` (159.0-166.0 s)
12. `place the plate on the breakfast table` (166.0-180.0 s)
13. `move to the electric refrigerator` (180.0-217.0 s)
14. `open the door of the electric refrigerator` (217.0-247.0 s)
15. `pick up the cupcake from the electric refrigerator` (247.0-267.0 s)
16. `pick up the cupcake from the electric refrigerator` (267.0-292.3 s)
17. `place the cupcake on the bar` (292.3-304.9 s)
18. `close the door of the electric refrigerator` (304.9-321.0 s)
19. `pick up the cupcake from the bar` (321.0-331.3 s)
20. `move to the breakfast table` (331.3-366.3 s)
21. `place the cupcake on the plate` (366.3-375.9 s)
22. `place the cupcake on the plate` (375.9-387.9 s)
23. `move to the sink` (387.9-412.0 s)
24. `pick up the tablefork from the sink` (412.0-442.1 s)
25. `pick up the table knife from the sink` (442.1-460.4 s)
26. `move to the breakfast table` (460.4-487.9 s)
27. `place the tablefork on the breakfast table` (487.9-497.4 s)
28. `place the table knife on the breakfast table` (497.4-509.6 s)
29. `move to the sink` (509.6-538.8 s)
30. `pick up the tablefork from the sink` (538.8-547.7 s)
31. `pick up the table knife from the sink` (547.7-564.1 s)
32. `move to the breakfast table` (564.1-591.0 s)
33. `place the tablefork on the breakfast table` (591.0-599.1 s)
34. `place the table knife on the breakfast table` (599.1-611.4 s)

Mean duration per skill in this task: close door 15.5 s, close drawer 16.9 s, move to 26.3 s, open door 21.6 s, pick up from 18.4 s, place on 9.3 s, push to 11.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the breakfast table` | 800 |
| `pick up the plate from the top cabinet` | 400 |
| `place the plate on the breakfast table` | 400 |
| `pick up the cupcake from the electric refrigerator` | 400 |
| `place the cupcake on the plate` | 400 |
| `move to the sink` | 400 |
| `pick up the tablefork from the sink` | 400 |
| `pick up the table knife from the sink` | 400 |
| `place the tablefork on the breakfast table` | 400 |
| `place the table knife on the breakfast table` | 400 |
| `open the door of the top cabinet` | 395 |
| `close the door of the top cabinet` | 391 |
| `push the plate to the top cabinet` | 375 |
| `move to the electric refrigerator` | 201 |
| `move to the top cabinet` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/64_setting_the_table.json`. Planner notes: `task_docs/notes/64_setting_the_table.md`.
