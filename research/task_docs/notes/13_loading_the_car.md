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
