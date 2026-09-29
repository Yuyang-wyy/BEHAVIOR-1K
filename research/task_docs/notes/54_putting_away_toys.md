## Planner notes

**Tier:** B. Eight small rigid toy figures (bbox 0.08-0.16 m long, 0.04-0.09 m tall) into two open boxes; closed loop already reached Q = 0.75 on 311, so the grasps work in practice even though no bbox axis is clearly under 44 mm.

### Goal in plain words

- All 8 toy figures must end inside a toy box. Each figure may go in either box (256 ground options), so mixing boxes is fine.
- Figures 1-4 start on the living-room floor, 5-8 on the dining-room floor (`:init`; instance x-coordinates agree: living figures at x 9.4-17.3, dining figures at x 5.1-9.3).
- Toy box 1 (`qgfbdj`, 0.46 x 0.80 x 0.40 m) sits on the living-room floor. Toy box 2 (`kvithq` scaled 5x, 0.59 x 0.63 x 0.31 m) sits on the dining breakfast table, rim at roughly 1.1 m.
- No doors, lids or switches are involved. Neither box has joints in the template.

### Q traps

- No literal is true at reset. Max Q = 1.0; each figure is worth 1/8.
- `inside` tests only the figure's AABB centre against the box's fillable volume (PREDICATES §3). A figure caught on the rim or lying across the edge does not count. Drop it well inside.
- Box 1 is on the floor and is not fixed. Driving into it moves it; box 2 can be knocked off the table, spilling its figures and losing their literals.
- Scoring reads only the final state. Check that earlier figures are still in the box after each drop.

### Minimal plan

Two figures per trip, one per hand, as in the demos. Times are demo means.

1. `move to the toy figure` — base stopped with a figure on the floor within reach. ~17 s.
2. `pick up the toy figure from the floors` — gripper closed short of fully closed, figure gone from the floor. ~12 s.
3. `move to the toy figure` / `pick up the toy figure from the floors` with the other hand. ~30 s.
4. `move to the toy box` — nearest box in view (floor box in the living room, table box in the dining room). ~20 s.
5. `place the toy figure in the toy box` twice — figures visible inside the box, grippers open. ~7 s each.
6. Repeat 1-5 for the other living-room pair, then for the two dining-room pairs using the box on the breakfast table.

Budget: 4 trips x ~90 s = ~360 s against a 565 s limit. Leaves ~200 s for re-grasps.

### What the demos do differently

- 48% of demos use exactly this pattern (move to x12, pick up x8, place in x8); 40 distinct orders.
- About 46 of 1600 picks add `hand over the toy figure`. Not needed.
- One demo picked up a toy box. Not needed and not advised.
- Humans often chain figures regardless of room; the nearest box is always the right box.

### Hard parts and hacks

- Grasp on figures lying on the floor: bboxes are 76-113 mm across the short horizontal axis, so the 44 mm jaw span must close on a narrower part (limb, neck, base). Which part works per model is unverified. Expect several retries per figure.
- Picking from the floor needs the trunk folded down; carrying two figures while driving 5-10 m between rooms risks dropping one. Check both grippers after every move.
- Box 2 is high (table top ~0.78 m plus a 0.31 m box). Raise the arm above the rim before releasing to avoid knocking the box off the table.
- Travel dominates: the humans drive 35 m. Figures in the dining room are 3-12 m from the start.
- Cheap check: after each place, the figure should be seen inside the box outline in the head camera; if it sits on the rim, push it in with the open gripper.

### Hints for the VLM

- Scene `house_single_floor`. The robot starts in the living room (sofas, wall-mounted TV, gas fireplace, coffee table). The dining room has one long breakfast table with 6 chairs; the box there sits on the table top.
- Toy figures are small figurines (under 0.16 m) lying on the floor. No figure starts under the dining table in any of the 20 instances.
- There are exactly 2 toy boxes and 8 figures; no same-category distractors.
- Done looks like: no figures visible on either floor; all eight inside the two boxes.
