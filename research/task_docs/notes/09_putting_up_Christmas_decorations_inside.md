## Planner notes

**Tier:** C — nine pick-and-place literals across two rooms, 0.20 m gift boxes wider than the jaw span, and a basket dump; no state change needed.

### Goal in plain words

All three gift boxes end next to, under, or touching the Christmas tree (any mix of the three per box). Both pillar candles end on the dining-room breakfast table. Exactly one candy cane ends on that table. The wreath ends on any living-room sofa, and exactly two candy canes end on one sofa (not necessarily the wreath's sofa, despite the instruction wording). The wicker basket's final place does not matter.

### Q traps

- 9 literals, none true at start per `:init`. But gift boxes spawn randomly on the living-room floor: by an AABB estimate from the instance poses (tree asset 1.30 x 1.32 x 1.90 m, nextto gap limit ~0.28 m), at least one box already starts within the gap or inside the tree footprint in instances 306, 307, 308, 312 (two boxes), 315, 316. Those literals may be true at reset and then never score (ray part of `nextto` unverified). Instance 311: no box close.
- `forn` is exact (PREDICATES §0). Success needs exactly 1 cane on the table and exactly 2 canes on one sofa. Three canes on a sofa, or two on the table, blocks success; partial Q still picks the best 2-of-3 option.
- Only one table is in scope: `breakfast_table_rhjoby_0` in dining_room_0 (the template has no other table in the dining room). The living-room coffee table does NOT count for candles or the cane.
- Four sofas qualify (sofa_lugrhk_0/1, sofa_hiphpn_0, sofa_wnzdke_0, all living_room_0).
- `ontop` on a sofa needs the item's centre over sofa geometry and in contact; an item that slides into the seat-back gap or onto the floor scores 0.
- Everything scored reads only the final state: a cane knocked off the sofa while fetching the others loses its literal.
- Pillar candles inside a basket that sits on the table are not `ontop` the table (they touch the basket, not the table).

### Minimal plan

1. `move to the wicker basket` — basket centred in view, base stopped. ~14 s.
2. `pick up the wicker basket from the floors` — basket off the floor, gripper closed short of full. ~18 s.
3. `move to the sofa` — sofa seat fills lower image. ~14 s.
4. `pour the candy cane and candy cane and candy cane and pillar candle and pillar candle and wreath into the wicker basket` (the demo string; it means tipping the basket out over the sofa) — basket empty, items visible on the seat. ~23 s. This scores wreath + 2 canes at once (3/9).
5. `place the wicker basket on the coffee table` — frees the hand; any drop spot is fine. ~13 s.
6. Gift boxes x3 (living room, do before the long dining trips): `move to the gift box`, `pick up the gift box from the floors`, `move to the christmas tree`, `place the gift box on the floors next to the in_front_of christmas tree`, then `push the gift box to the center christmas tree` — box on the floor touching or under the tree skirt. ~55 s per box. If the grasp fails, push only.
7. `move to the candy cane`, `pick up the candy cane from the sofa`, `move to the breakfast table`, `place the candy cane on the breakfast table` — one cane on the table, two left on the sofa. ~60 s.
8. Pillar candles x2: `move to the pillar candle`, `pick up the pillar candle from the sofa`, `move to the breakfast table`, `place the pillar candle on the breakfast table`. ~60 s each.
- Total ~390 s against a 686 s limit; the demo mean is 457 s.

### What the demos do differently

- Nearly all demos use the same order: dump basket on sofa, park basket on coffee table, cane then both candles to the table, gift boxes last (52% exact order, 29 variants).
- Gift boxes are placed then pushed toward the tree centre (404 push segments over 571 placements).
- Seven demos push the wreath (`push the wreath to the away robot`); not needed.
- Parking the basket on the coffee table is not needed for the goal.
- Moving boxes earlier than the demos do banks 3 literals before the 7 m dining-room trips.

### Hard parts and hacks

- Gift box asset is 0.20 x 0.19 x 0.19 m, far over the 44 mm assisted-grasp span; humans lift it, the robot likely cannot. Pushing along the floor to the tree is legal and is a trained skill.
- Pillar candle is 0.05 x 0.05 x 0.07 m after scale 0.5: 50 mm across, just over 44 mm. Grasp may not register; unverified in sim.
- Candy cane is ~0.12 x 0.05 x 0.015 m after scaling; graspable but tiny and flat on a patterned cushion.
- Wreath is 0.20 x 0.20 x 0.04 m; it arrives on the sofa by the dump, so it never needs a grasp.
- Basket 0.26 x 0.41 x 0.19 m; handle width unverified. If it cannot be lifted, pushing it over is `tip over` (no demo prompt; closest: the pour string above).
- Hack: after picking the wreath and two canes out onto a sofa, carry the basket with 2 candles + 1 cane to the breakfast table and tip it there; all three land on the table. Rolling candles are the risk. Table asset is 1.16 x 2.90 m, so there is room.
- The tree moves between instances (spread 7.4 m) and so do the basket and boxes (spread ~9 m); nothing can be hard-coded.
- Breakfast table is 7.2 m (median) from the start pose through a doorway; base odometry drift is the navigation risk.

### Hints for the VLM

- Tree: 1.9 m tall conifer in living_room_0, the only one. "Next to" = within ~0.28 m of the tree's bounding box; pushing the box against the trunk/skirt (touching) is safest.
- Gift boxes: three identical wrapped boxes on the floor; any box to the tree counts.
- Sofas: four in living_room_0; pick the nearest one to the basket.
- Breakfast table: the long table (2.9 m) with six straight chairs in dining_room_0. The coffee table in the living room is a distractor.
- Done: one cane on the table and two on a sofa (count them), both candles upright on the table, wreath on a sofa, three boxes at the tree.
