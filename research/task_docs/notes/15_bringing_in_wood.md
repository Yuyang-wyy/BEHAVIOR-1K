## Planner notes

**Tier:** C — three flat plywood boards (0.07 x 0.47 x 0.02 m each) lie flat on the garden floor. The only dimension under 44 mm is the vertical 0.02 m, which a gripper cannot straddle from above. They must be carried 5-15 m through a closed door.

### Goal in plain words

All three plywood boards must rest on the corridor floor.
The boards are interchangeable, and any spot on the corridor floor works.
Nothing has to be closed afterwards.

### Q traps

- 3 literals, all False at reset. Max partial Q is 1.0; each board is worth 1/3.
- `ontop` needs direct contact (PREDICATES §4). A board stacked on another board does not touch the floor and does not score. Lay them side by side.
- The board must rest on the corridor floor (`floors_xorxro_0`), not the garden floor just outside the door. A board resting across the threshold may touch both floors. It scores only if the ray down from its AABB centre hits the corridor floor; place it fully inside.
- The corridor has two `hall_tree` stands. A board leaning on one of them may not touch the floor.
- A board dropped on the way (on the garden floor) scores 0.

### Minimal plan

The corridor-garden door `door_vudhlc_1` starts closed (template joint_pos ~0). Every demo opens it on the first trip. The boards start anywhere in the garden (per-instance spread up to 16 m), 0.7-14 m from the robot.

1. `move to the plywood` — board centred in view on the ground. ~44 s.
2. `pick up the plywood from the floors` — board lifted off the ground; depth shows a gap below it. ~22 s.
3. `move to the door`, `open the door of the door` — door swung open, corridor visible. ~44 s + 56 s.
4. `move to the floors`, `place the plywood on the floors` — board lying on the corridor floor, gripper open. ~44 s + 17 s.
5. Repeat for the other two boards. Carry one per hand: `move to the plywood`, `pick up the plywood from the floors` twice, then `move to the floors` and `place the plywood on the floors` twice. ~44 + 22 + 44 + 22 + 44 + 17 + 17 s.

Budget: about 440 s against a 677 s limit. The two-per-trip second leg matters; three single trips probably do not fit.

### What the demos do differently

- The demos are uniform: all 200 open `door_vudhlc_1`, carry one board first, then two boards together. The order of the three boards varies freely.
- 3-4 demos put a board down on the garden floor and regrasp; that is recovery, not a needed step.
- No push or hand-over is used.

### Hard parts and hacks

- The grasp is the hard part. A board lying flat has 0.07 m width (too wide) and 0.02 m thickness (vertical, finger cannot get under it). A likely working approach is to tilt it first or grasp its end from the side with fingers low; unverified.
- Scripted pushing along the floor is a legal fallback: `ontop floor` only needs the board resting on the corridor floor. It is 5-15 m of pushing through a doorway; no push prompt exists in this task's demos (closest trained verb: `push the <obj> to the <target>` from other tasks).
- The door must stay open between trips. If it swings shut, it blocks the second trip.
- The garden is large (17.6 x 5.3 m floor, 55 bushes, 26 trees). Boards on the lawn can be hard to see; scan low.

### Hints for the VLM

- Plywood boards are thin light-brown planks about half a metre long, lying on the garden ground. There are exactly three, and no other plywood in the scene.
- The target door is between the garden and the corridor. The corridor has two garden doors (`door_vudhlc_0`, `door_vudhlc_1`); the demos use `_1`. Either leads to the same corridor floor.
- The corridor is a long narrow hall (2.6 x 9 m) with two hall trees, a standing mirror and pictures on the walls.
- Done for each board: lying flat on the corridor tiles, clear of the doorway and not on another board.
