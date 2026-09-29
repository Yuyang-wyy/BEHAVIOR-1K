# 50 · Freeze Fruit

Task name `freeze_fruit`, task index 50.

> In the kitchen, take the two tupperware containers from the cabinet, put one apple and one strawberry into each container, place both containers in the refrigerator, and leave the fruit frozen.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 420.6 s mean (12618 steps) |
| episode time limit | 630.9 s (18928 steps at 30 Hz) |
| human base travel | 25.4002 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.857 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/6nM9_B5OoRY |

## Planner notes

**Tier:** C — pure container-in-container placement: fruit into tupperware, tupperware into fridge. Despite the name, nothing has to freeze, but the fruit is wider than the jaws.

### Goal in plain words

Each tupperware must hold one apple and one strawberry, with a different apple and a different strawberry in each (`forpairs`, 4 ground options). Both tupperwares must be inside the fridge `fridge_dszchb_0`, and the fridge must be closed. **There is no `frozen` literal**, so there is no waiting after closing the door. **Containers:** the two tupperwares from the bottom cabinet `bottom_cabinet_no_top_gjeoer_0`. The bowl, the tray and the cabinet doors are not in the goal.

### Q traps

- 7 literals. `not open fridge` is true at start (joint 0.0 in all 20 instances), so it never scores. Max partial Q is 6/7 = 0.857 (page is right).
- **Split the fruit.** Both apples in the same tupperware satisfy only one `inside apple tupperware` literal of the best option, and the same holds for the strawberries. A full pair needs one of each per box.
- `inside` tests only the AABB centre (§3). A strawberry resting on top of an apple can poke above the rim and still count, as long as its centre is below the rim's volume top. Check it.
- Close the fridge last, and check afterwards that the door did not bounce open on a tupperware edge (§6).
- Leaving the cabinet open costs nothing. The cabinet is not in the goal, and one of its joints reads 0.0035 at start in some instances anyway.

### Minimal plan

1. `move to the bottom cabinet no top`, `open the door of the bottom cabinet no top`, `pick up the tupperware from the bottom cabinet no top` — ~14 + 24 + 10 s.
2. `place the tupperware on the countertop` — box upright near the bowl and tray. ~10 s.
3. Repeat step 1 (another door may be needed), then `place the tupperware on the countertop` again. Skip `close the door of the bottom cabinet no top` (not in the goal, ~15 s each).
4. `move to the apple`, `pick up the apple from the bowl`, then `move to the tupperware`, `place the apple in the tupperware` — ~14 + 10 + 14 + 7 s. Repeat for the second apple, into the **other** tupperware.
5. `move to the strawberry`, `pick up the strawberry from the tray`, `move to the tupperware`, `place the strawberry in the tupperware` — same timings. Repeat into the other tupperware.
6. `move to the electric refrigerator`, `open the door of the electric refrigerator` — ~14 + 24 s.
7. `pick up the tupperware from the countertop`, `place the tupperware in the electric refrigerator` — ~10 + 7 s. Do it once per tupperware. Carrying both at once (one per hand) saves a trip.
8. `close the door of the electric refrigerator` — door flush. ~15 s. Success.

The plan takes about 330 s against a 631 s limit. Picking two fruits (one per hand) per trip, as the demos do, saves about 40 s.

### What the demos do differently

- Two-handed batching: `pick up the apple from the bowl` twice, then `place the apple in the tupperware` twice.
- 199 of 200 demos park one loaded tupperware on the breakfast bar (`place the tupperware on the bar`) to free a hand for the fridge door, and fetch it again afterwards (`pick up the tupperware from the bar`). This is a staging step, not a goal need.
- They close the cabinet after each tupperware. That is not needed.
- In this task the fridge is called `electric refrigerator`, not `fridge`. Keep that wording.

### Hard parts and hacks

- **Grasp span.** Apples are 86-87 x 74 x 74 mm, and strawberries are forced to 60 x 50 x 50 mm (`task_custom_lists.json`). Both exceed the 44 mm span on every axis, so a clean grasp is unlikely. The ft40k checkpoint scored 0 on instance 311. Without fruit, the reachable Q is 2/7 ≈ 0.29, from the two tupperwares in the fridge.
- **Pour hack** (untested): pick the bowl by its rim (306 mm bowl) and tip the apples into a tupperware. Put the two tupperwares side by side first, so an apple landing in each is at least possible. There is no trained prompt; closest: `pour the ... into the ...` from other tasks. The strawberries sit on a flat 200 x 250 x 20 mm tray, which can hardly be picked.
- **Tupperware** (`mkstwr`, 219 x 219 x 136 mm, no lid in the scene) is held by the rim wall. Wall thickness is not verified. The boxes sit on a low cabinet shelf at z ≈ 0.56.

### Hints for the VLM

- Kitchen of `house_single_floor`. The tupperwares are in the long low cabinet under the counter along the x ≈ 4.1 wall, under the burner and microwave. The bowl of apples and the tray of strawberries are on `countertop_kelzer_0` along the sink wall. The fridge is at the right end of that wall (7.8, -2.0). The breakfast bar with stools is at (7.3, 0.2).
- Two red apples in a large bowl, two strawberries on a small tray. Each is the only fruit of its kind.
- Done: two boxes on fridge shelves, each visibly holding one apple and one strawberry, door flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside apple.n.01_1 tupperware.n.01_2)` | no | yes |
| `(inside apple.n.01_2 tupperware.n.01_1)` | no | yes |
| `(inside strawberry.n.01_1 tupperware.n.01_2)` | no | yes |
| `(inside strawberry.n.01_2 tupperware.n.01_1)` | no | yes |
| `(inside tupperware.n.01_2 electric_refrigerator.n.01_1)` | no | yes |
| `(inside tupperware.n.01_1 electric_refrigerator.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

The goal has 4 ground options (7 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forpairs 
                (?apple.n.01 - apple.n.01) 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?apple.n.01 ?tupperware.n.01)
            ) 
            (forpairs 
                (?strawberry.n.01 - strawberry.n.01) 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?strawberry.n.01 ?tupperware.n.01)
            )
            (forall 
                (?tupperware.n.01 - tupperware.n.01) 
                (inside ?tupperware.n.01 ?electric_refrigerator.n.01_1)
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
| `tupperware.n.01_1` | tupperware_238 | tupperware / mkstwr | kitchen_0 | low (0.25-0.6 m), z 0.56 | 1.67 m (range 0.78-3.64) | yes, spread 2.44 m |
| `tupperware.n.01_2` | tupperware_237 | tupperware / mkstwr | kitchen_0 | low (0.25-0.6 m), z 0.56 | 1.46 m (range 1.01-3.7) | yes, spread 2.34 m |
| `cabinet.n.01_1` | bottom_cabinet_no_top_gjeoer_0 | bottom_cabinet_no_top / gjeoer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 1.64 m (range 1.05-3.75) | no (fixed) |
| `bowl.n.01_1` | bowl_236 | bowl / byzaxy | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 2.42 m (range 0.93-3.78) | yes, spread 2.64 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 2.1 m (range 1.07-3.64) | no (fixed) |
| `apple.n.01_1` | apple_235 | apple / omzprq | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.41 m (range 0.94-3.76) | yes, spread 2.62 m |
| `apple.n.01_2` | apple_234 | apple / agveuv | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.45 m (range 0.87-3.76) | yes, spread 2.74 m |
| `tray.n.01_1` | tray_233 | tray / gsxbym | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 2.49 m (range 1.54-4.06) | yes, spread 2.73 m |
| `strawberry.n.01_1` | strawberry_232 | strawberry / xcnzxh | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.53 m (range 1.53-4.04) | yes, spread 2.76 m |
| `strawberry.n.01_2` | strawberry_231 | strawberry / xcnzxh | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.48 m (range 1.49-4.06) | yes, spread 2.69 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.54 m (range 0.94-2.31) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.21 m (range 0.97-4.41) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "house_single_floor": {
  "whitelist": {
   "apple.n.01": {
    "apple": {
     "agveuv": null,
     "omzprq": null
    }
   },
   "bowl.n.01": {
    "bowl": {
     "byzaxy": null
    }
   },
   "strawberry.n.01": {
    "strawberry": {
     "xcnzxh": [
      0.06,
      0.05,
      0.05
     ]
    }
   },
   "tray.n.01": {
    "tray": {
     "gsxbym": [
      0.2,
      0.25,
      0.02
     ]
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
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside apple.n.01_1 bowl.n.01_1)
(inside apple.n.01_2 bowl.n.01_1)
(inside tupperware.n.01_1 cabinet.n.01_1)
(inside tupperware.n.01_2 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bowl.n.01_1 countertop.n.01_1)
(ontop strawberry.n.01_1 tray.n.01_1)
(ontop strawberry.n.01_2 tray.n.01_1)
(ontop tray.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bowl.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 bowl.n.01_1)
(touching countertop.n.01_1 tray.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching strawberry.n.01_1 tray.n.01_1)
(touching strawberry.n.01_2 tray.n.01_1)
(touching tray.n.01_1 countertop.n.01_1)
(touching tray.n.01_1 strawberry.n.01_1)
(touching tray.n.01_1 strawberry.n.01_2)
```

## What the human demos did

200 annotated demos. Length 407.0 s (range 303.03-664.1). Skills per demo 34.0 (range 27-38). 89 distinct skill orders; the most common one covers 18% of demos.

Most common skill counts per demo (18% of demos): move to x11, pick up from x9, place in x6, close door x3, open door x3, place on x3.

Representative demo `episode_00501190.json` (429.5 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the bottom cabinet no top` (0.0-15.0 s)
2. `open the door of the bottom cabinet no top` (15.0-38.0 s)
3. `pick up the tupperware from the bottom cabinet no top` (38.0-59.0 s)
4. `place the tupperware on the countertop` (59.0-65.0 s)
5. `close the door of the bottom cabinet no top` (65.0-76.0 s)
6. `move to the bottom cabinet no top` (76.0-87.0 s)
7. `open the door of the bottom cabinet no top` (87.0-112.0 s)
8. `pick up the tupperware from the bottom cabinet no top` (112.0-133.0 s)
9. `close the door of the tupperware` (133.0-152.7 s)
10. `move to the countertop` (152.7-160.4 s)
11. `place the tupperware on the countertop` (160.4-170.0 s)
12. `move to the apple` (170.0-192.0 s)
13. `pick up the apple from the bowl` (192.0-200.0 s)
14. `pick up the apple from the bowl` (200.0-213.0 s)
15. `move to the tupperware` (213.0-229.5 s)
16. `place the apple in the tupperware` (229.5-233.9 s)
17. `place the apple in the tupperware` (233.9-241.0 s)
18. `move to the strawberry` (241.0-253.0 s)
19. `pick up the strawberry from the tray` (253.0-264.0 s)
20. `pick up the strawberry from the tray` (264.0-271.0 s)
21. `move to the tupperware` (271.0-287.4 s)
22. `place the strawberry in the tupperware` (287.4-293.0 s)
23. `place the strawberry in the tupperware` (293.0-297.5 s)
24. `pick up the tupperware from the countertop` (297.5-301.0 s)
25. `pick up the tupperware from the countertop` (301.0-306.0 s)
26. `move to the bar` (306.0-325.0 s)
27. `place the tupperware on the bar` (325.0-337.0 s)
28. `move to the electric refrigerator` (337.0-346.0 s)
29. `open the door of the electric refrigerator` (346.0-370.5 s)
30. `place the tupperware in the electric refrigerator` (370.5-383.0 s)
31. `move to the tupperware` (383.0-391.0 s)
32. `pick up the tupperware from the bar` (391.0-400.0 s)
33. `move to the electric refrigerator` (402.0-407.0 s)
34. `place the tupperware in the electric refrigerator` (407.0-421.0 s)
35. `close the door of the electric refrigerator` (421.0-429.0 s)

Mean duration per skill in this task: close door 15.0 s, hand over 11.7 s, move to 14.3 s, open door 24.1 s, pick up from 10.3 s, place in 7.2 s, place on 9.6 s, place on next to 7.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tupperware` | 596 |
| `pick up the apple from the bowl` | 402 |
| `move to the electric refrigerator` | 401 |
| `pick up the strawberry from the tray` | 398 |
| `place the tupperware in the electric refrigerator` | 396 |
| `pick up the tupperware from the bottom cabinet no top` | 393 |
| `pick up the tupperware from the countertop` | 391 |
| `open the door of the bottom cabinet no top` | 387 |
| `close the door of the bottom cabinet no top` | 384 |
| `place the apple in the tupperware` | 372 |
| `place the strawberry in the tupperware` | 365 |
| `place the tupperware on the countertop` | 335 |
| `move to the bottom cabinet no top` | 300 |
| `move to the bar` | 215 |
| `pick up the tupperware from the bar` | 207 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/50_freeze_fruit.json`. Planner notes: `task_docs/notes/50_freeze_fruit.md`.
