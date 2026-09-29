# 13 · Loading The Car

Task name `loading_the_car`, task index 13.

> Put the digital camera from the living room table into the container on the living room floor. Then take the container and the tennis racket to the garage, place both in the car trunk, and close it.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage, living_room |
| rooms loaded | corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 640.9 s mean (19226 steps) |
| episode time limit | 961.3 s (28839 steps at 30 Hz) |
| human base travel | 48.3176 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114057519 |

## Planner notes

**Tier:** C — the toy box (0.30 x 0.45 x 0.15 m) and the camera (0.11 x 0.20 x 0.15 m) have no dimension under the 44 mm jaw span, and the box is container-in-container work.

### Goal in plain words

The toy box must end up inside the car, the digital camera inside the toy box, and the tennis racket inside the car.
There is one of each object, so nothing is interchangeable.
The car trunk does NOT have to be closed at the end (see Q traps).
The racket may lie anywhere in the car's container volume; it does not have to be in the toy box.

### Q traps

- The BDDL writes `(not (open ?car.n.01_1))` as a second clause after the `and` block. `bddl/parsing.py:281` keeps only `group[1]` of `:goal`, so that clause is dropped. The evaluator's goal has 3 literals and success does not need the trunk closed. Skip `close the lid of the car`; closing it could also push the racket or box out of the volume.
- All 3 literals start False (template: nothing starts in the car; car trunk joint_pos 0.0 in all 20 instances).
- `inside camera toy_box` is checked wherever the box is. Putting the camera in the box first and then carrying the box would earn 2 literals at once, but the camera can fall out while the box is carried. Putting the box in the car first, then the camera into it (the demo order), is safer.
- `inside` needs each object's AABB centre in a fillable volume (PREDICATES §3). Whether the car asset `ssxsje` has a fillable volume in the trunk is unverified: its metadata lists only a `trunk` link and an `attachment` meta link. Run `task_feasibility_probe.py` before investing in this task.
- The racket is 0.82 m long. Its centre must be inside the trunk volume; a racket lying half over the bumper may not count.

### Minimal plan

Robot starts in the garage, 1.7-4.1 m from the car. Living-room objects are 5.7-13.3 m away. The garage-corridor door `door_bexenl_0` starts closed (joint_pos 0) and every demo opens it.

1. `move to the car` — base stopped at the car's rear. ~57 s.
2. `open the lid of the car` — trunk lid visibly raised. ~68 s.
3. `move to the door` then `open the door of the door` — door visibly swung open, corridor visible. ~57 s + 19 s.
4. `move to the toy box` — box centred in the head camera on the living-room floor. ~57 s.
5. `pick up the toy box from the floors` — box lifted off the floor in the gripper(s); depth shows it no longer on the floor. ~26 s.
6. `move to the car` — base stopped at the open trunk. ~57 s (longest leg, 7-13 m).
7. `place the toy box in the car` — box visible in the trunk, grippers open. ~16 s.
8. `move to the digital camera` then `pick up the digital camera from the coffee table`. ~57 s + 26 s.
9. `move to the tennis racket` then `pick up the tennis racket from the coffee table` (second arm). ~57 s + 26 s.
10. `move to the car`, `place the tennis racket in the car`, `place the digital camera in the toy box`. ~57 s + 2 x 16 s.
11. Stop. Do not send `close the lid of the car`.

Budget: about 610 s against a 961 s limit. The demo carries camera and racket together (one per hand) to save one round trip; keep that.

### What the demos do differently

- 200/200 demos close the trunk lid at the end; the evaluator does not need it.
- 200/200 open the trunk first and open the corridor door on the way to the living room.
- 199/200 place the camera into the box after the box is already in the car. 83 demos carry camera then racket, 36 carry racket then camera; the order does not matter.
- 34 demos `push the digital camera to the reorient coffee table` and 10 push the racket to reorient before picking. This is in the trained vocabulary; use it if the first grasp fails.

### Hard parts and hacks

- Toy box: 0.30 x 0.45 x 0.15 m. The whole box cannot fit in the jaws. A grasp is only possible across a wall of the open box (wall thickness unknown) or bimanually. The asset has no handle link.
- Digital camera: smallest extent 0.11 m, so no straddling grasp on the body. A lens or strap narrower than 44 mm is not listed as a separate link; unverified.
- Tennis racket: 0.028 m thick overall (bbox 0.82 x 0.34 x 0.03 m); the frame rim or handle should fit the jaws. It lies flat on a 0.36 m coffee table, so the rim needs a top-down pinch at the edge.
- Long carries (48 m of human base travel) through a doorway; odometry drift makes re-finding the trunk the likely failure.
- Cheap partial Q: the racket alone is 1/3. It is the only object clearly within the grasp span.

### Hints for the VLM

- The car is in the garage (the only car); the robot starts next to it. Its trunk is the rear lid.
- The living room has exactly one coffee table, one toy box (on the floor) and one sofa. The camera and racket sit on the coffee table (0.36 m high).
- The corridor door is the one between garage and corridor; it is the only door in the garage besides the large garage door (do not open the garage door).
- Done for the box: box visibly within the trunk opening, below the rim. Done for the camera: camera visible inside the box walls. Done for the racket: racket lying inside the trunk, handle not hanging out.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside container.n.01_1 car.n.01_1)` | no | yes |
| `(inside digital_camera.n.01_1 container.n.01_1)` | no | yes |
| `(inside tennis_racket.n.01_1 car.n.01_1)` | no | yes |

**Warning:** this goal has more than one top-level clause. The BDDL parser keeps only the first (`bddl/parsing.py:281`), so the later clauses are ignored by the evaluator and are not in the literal table.

BDDL goal:

```lisp
(:goal 
        (and 
            (inside ?container.n.01_1 ?car.n.01_1) 
            (inside ?digital_camera.n.01_1 ?container.n.01_1)
            (inside ?tennis_racket.n.01_1 ?car.n.01_1)
        )
        (not 
            (open ?car.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `car.n.01_1` | car_ssxsje_0 | car / ssxsje | garage_0 | table/counter (0.6-1.1 m), z 0.67 | 3.48 m (range 1.67-4.07) | no (fixed) |
| `container.n.01_1` | toy_box_81 | toy_box / uvhflb | living_room_0 | floor, z 0.05 | 9.96 m (range 6.94-13.34) | yes, spread 5.0 m |
| `tennis_racket.n.01_1` | tennis_racket_80 | tennis_racket / rmvafy | living_room_0 | low (0.25-0.6 m), z 0.44 | 10.12 m (range 5.84-11.57) | yes, spread 0.77 m |
| `digital_camera.n.01_1` | digital_camera_79 | digital_camera / wbzzjl | living_room_0 | low (0.25-0.6 m), z 0.49 | 10.17 m (range 5.65-11.67) | yes, spread 1.49 m |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 10.21 m (range 5.75-11.4) | no |
| `floor.n.01_1` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 2.12 m (range 1.19-3.49) | no (fixed) |
| `floor.n.01_2` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 10.58 m (range 6.14-11.77) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom car.n.01_1 garage)
(inroom floor.n.01_1 garage)
(inroom floor.n.01_2 living_room)
(inroom table.n.02_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop container.n.01_1 floor.n.01_2)
(ontop digital_camera.n.01_1 table.n.02_1)
(ontop tennis_racket.n.01_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching container.n.01_1 floor.n.01_2)
(touching digital_camera.n.01_1 table.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_2 container.n.01_1)
(touching table.n.02_1 digital_camera.n.01_1)
(touching table.n.02_1 tennis_racket.n.01_1)
(touching tennis_racket.n.01_1 table.n.02_1)
```

## What the human demos did

200 annotated demos. Length 661.45 s (range 309.87-758.7). Skills per demo 16.0 (range 14-19). 15 distinct skill orders; the most common one covers 60% of demos.

Most common skill counts per demo (60% of demos): move to x7, pick up from x3, place in x3, close lid x1, open door x1, open lid x1.

Representative demo `episode_00131800.json` (672.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the car` (0.0-23.2 s)
2. `open the lid of the car` (23.2-94.7 s)
3. `move to the door` (94.7-123.4 s)
4. `open the door of the door` (123.4-145.8 s)
5. `move to the toy box` (145.8-197.1 s)
6. `pick up the toy box from the floors` (197.1-228.9 s)
7. `move to the car` (228.9-320.0 s)
8. `place the toy box in the car` (320.0-327.5 s)
9. `move to the digital camera` (327.5-405.6 s)
10. `pick up the digital camera from the coffee table` (405.6-419.3 s)
11. `move to the tennis racket` (419.3-453.3 s)
12. `pick up the tennis racket from the coffee table` (453.3-495.9 s)
13. `move to the car` (495.9-598.0 s)
14. `place the tennis racket in the car` (598.0-611.4 s)
15. `place the digital camera in the toy box` (611.4-635.5 s)
16. `close the lid of the car` (635.5-672.0 s)

Mean duration per skill in this task: close lid 32.9 s, move to 57.2 s, open door 18.7 s, open lid 67.6 s, pick up from 25.9 s, place in 15.8 s, push to 29.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the car` | 557 |
| `move to the toy box` | 240 |
| `open the lid of the car` | 200 |
| `move to the door` | 200 |
| `open the door of the door` | 200 |
| `place the toy box in the car` | 200 |
| `pick up the digital camera from the coffee table` | 200 |
| `pick up the tennis racket from the coffee table` | 200 |
| `place the tennis racket in the car` | 200 |
| `close the lid of the car` | 200 |
| `pick up the toy box from the floors` | 199 |
| `place the digital camera in the toy box` | 199 |
| `move to the digital camera` | 188 |
| `move to the tennis racket` | 174 |
| `push the digital camera to the reorient coffee table` | 34 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/13_loading_the_car.json`. Planner notes: `task_docs/notes/13_loading_the_car.md`.
