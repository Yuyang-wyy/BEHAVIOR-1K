## Planner notes

**Tier:** C — five wide floor objects into a low drawer, a 29 cm cauldron to carry, plus drawer open/close. None of the objects fits the 44 mm span.

### Goal in plain words

Both pumpkins and all three pillar candles must end inside a living-room cabinet. Only one cabinet is in scope: `bottom_cabinet_rhdbzv_0`, a low 2.34 m console with two drawers. Any mix of drawers is fine. The cauldron must be `nextto` the coffee table, the only table in the living room. At the end every drawer of that cabinet must be closed.

### Q traps

- 7 literals. `not open cabinet` is true at start: both drawer joints are ~1e-10 in the template and all 20 instances (checked). It never scores but blocks success. Max partial Q = 6/7 = 0.857.
- Opening a drawer costs no Q; leaving it open only loses success. If time runs short, stop putting items in rather than skipping the close.
- The cauldron starts 0.97-2.53 m from the coffee-table centre, so `nextto` is false at start in all instances.
- `nextto` threshold: cauldron 0.29 x 0.29 x 0.25 m, coffee table 0.80 x 1.66 x 0.41 m, so L/6 ~ 0.20 m. The AABB gap must be under ~0.2 m (PREDICATES §5). Aim for near touching.
- The not-open literal counts both drawers. A drawer bumped ajar (> 5 % of its travel) during placing blocks success.
- Closing the drawer can snag an item on the front edge and pull its centre out of the volume. Re-check after closing.
- Whether drawers carry fillable volume is not verified in PREDICATES §18. Indirect evidence: zs_pt50 scored 4/7 on 311, which needs at least 3 `inside` literals.

### Minimal plan

1. `move to the cauldron` — base stopped at cauldron. ~15 s.
2. `pick up the cauldron from the floors` — cauldron clear of floor. ~19 s.
3. `move to the coffee table` — ~15 s.
4. `place the cauldron on the floors next to the in_front_of coffee table` — cauldron on floor, under ~0.2 m from the table side in depth. ~13 s.
5. `move to the bottom cabinet` then `open the drawer of the right bottom cabinet` — drawer visibly pulled out. ~15 + 28 s.
6. `move to the pillar candle`, `pick up the pillar candle from the floors`, then again for a second candle with the other gripper. ~2 x 34 s.
7. `move to the bottom cabinet`, `place the pillar candle in the right bottom cabinet` x2 — both grippers empty, candles below the drawer rim. ~15 + 2 x 17 s.
8. Same for the third candle and one pumpkin (`move to the pumpkin`, `pick up the pumpkin from the floors`, `place the pumpkin in the right bottom cabinet`), then the last pumpkin. ~2 trips x ~115 s.
9. `close the drawer of the right bottom cabinet` — drawer front flush with the cabinet. ~18 s.

Budget ~500 s against a 689 s limit (20682 steps). Using one drawer skips one open (28 s) and one close (18 s) versus the demos. Space check: right drawer link is 1.25 m wide, 0.36 m deep; 3 candles (0.10 m) plus 2 pumpkins (0.15 m) need ~0.6 m.

### What the demos do differently

- All demos open both drawers: candles mostly go to the "left" drawer, pumpkins to the "right". One drawer is enough.
- Humans carry two items at once (one per hand) and place both before walking back. Keep this: it halves the trips.
- 92 distinct orders; the cauldron is often done first. Order is free, but close the drawer last.
- "left bottom cabinet" and "right bottom cabinet" are the two drawers of the same console, not two cabinets.

### Hard parts and hacks

- Object sizes (asset bbox_size, scale 1.0): pumpkin 150 x 149 x 124 mm, pillar candle 100 x 100 x 139 mm, cauldron 291 x 291 x 250 mm. None has a dimension under 44 mm. A pumpkin stem or cauldron handle width is unverified. Policies did move items on 311 (zs_pt50, ft24k, pt0 all 0.57).
- The drawer sits at floor level (cabinet top 0.41 m). Placing needs a low trunk pose and reaching down over the drawer front.
- Drawer handle width is unverified against 44 mm. Closing can be a push (no grasp).
- Pushing the cauldron across the floor to the table would satisfy `nextto` without a grasp. No trained prompt; closest: `push the <obj> to the <target>` template, e.g. `push the cauldron to the coffee table` (untested wording).
- Round shapes: a dropped pumpkin or tipped candle rolls. Release low, inside the drawer.
- Closed-loop on 311: zs_pt50 0.57, ft24k 0.57, pt0 0.57, ft40k 0.29, ft10k 0.14.

### Hints for the VLM

- All task objects are on the living-room floor: 2 pumpkins, 3 pillar candles (short fat cylinders), 1 cauldron (pot shape, ~29 cm).
- Cabinet: long low console (2.34 m x 0.41 m x 0.41 m) against a wall, with two wide drawers. It is the only cabinet in the living room. Kitchen cabinets are out of scope and do not count.
- Coffee table: the low table (top ~0.41 m) in the living room (0.80 x 1.66 m). The kitchen breakfast table does not count.
- Distractors: sofa, shelf, fireplace, a living-room countertop.
- Done: no pumpkins or candles visible on the floor, both drawer fronts flush, cauldron on the floor touching or almost touching the coffee table.
