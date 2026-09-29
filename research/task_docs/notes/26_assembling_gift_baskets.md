## Planner notes

**Tier:** B — 16 plain pick-and-place moves into open baskets; no doors, no state changes. Item widths vs the 44 mm span are unknown (no custom list), so graspability of the pillar candle and cheese is unverified.

### Goal in plain words

Each of the four wicker baskets must contain exactly one pillar candle, one butter cookie, one swiss cheese and one bow. Items of a kind are interchangeable and so are the baskets. `forpairs` needs a perfect matching, so two candles in one basket and none in another loses one literal. Where the baskets stand at the end does not matter. Nothing else is checked: no `not open`, no `ontop`.

### Q traps

- 16 literals, none true at reset. Every item placed in a distinct basket earns 1/16.
- Doubling up breaks the matching. Two of the same kind in one basket count once. Keep a per-basket tally of the four kinds.
- `inside` tests only the item's AABB centre (PREDICATES §3). An item on the rim or poking out still counts if the centre is in the basket volume.
- Knocking a basket over spills its items and loses those literals. Do not bump filled baskets with the base or arm.
- Past results on 311: Q 0.44-0.50 (7-8 items in). That confirms the wicker basket has a working fillable volume.

### Minimal plan

All 200 demos first lift all four baskets from the floor onto the living-room bottom cabinet, two per trip, then fill them. That relocation is not in the goal, but every trained `place ... in the wicker basket` frame shows baskets on the cabinet. Keep it unless the VLA fails to lift baskets; then fill them on the floor (out of distribution).

1. `move to the wicker basket` — basket centred and close in the head camera. ~15 s.
2. `pick up the wicker basket from the floors` — gripper closed but not fully, basket lifted off the floor in view. ~16 s. Repeat 1-2 for a second basket with the other hand.
3. `move to the bottom cabinet` — base stopped facing the cabinet. ~15 s.
4. `place the wicker basket on the bottom cabinet` (x2) — both baskets resting on the cabinet top, grippers open and empty. ~6 s each.
5. Repeat 1-4 for the other two baskets. Leave the four baskets side by side, not stacked.
6. For each kind (swiss cheese, pillar candle, butter cookie, bow), twice:
   - `move to the swiss cheese` — item on the coffee table in view. ~15 s.
   - `pick up the swiss cheese from the coffee table` — gripper closed on the item, table spot now empty. ~16 s. Repeat for a second item with the other hand.
   - `move to the bottom cabinet`. ~15 s.
   - `place the swiss cheese in the wicker basket` (x2, different baskets) — item visible inside the basket rim in depth. ~8 s each.
7. Swap in `pillar candle`, `butter cookie`, `bow` with the same sentences.

Budget: ~870 s demo mean vs a 1303 s limit. Two-handed carrying roughly halves the trips; a one-hand plan needs ~32 trips and may run out of time.

### What the demos do differently

- All 200 demos move all four baskets onto the bottom cabinet (4 × `place ... on the bottom cabinet`). The goal does not need it.
- Humans carry two items of the same kind per trip, one in each hand, and drop them into two different baskets.
- 119 distinct orders; the modal one (26 %) goes cheese, candle, cookie, bow, then repeats.
- `move to the bottom cabinet` is the top sentence (2000 uses): it is the hub of every trip.

### Hard parts and hacks

- Grasping four different small shapes from a low coffee table (z ~0.36 m). Bow and cheese widths are unknown vs the 44 mm span.
- Lifting a basket from the floor: basket and handle dimensions are unknown; humans managed it in every demo (teleop, not assisted-grasp evidence).
- Assignment bookkeeping is the planner's job: track which basket already holds which kind. Comet has no memory of this.
- Clutter: 16 items on one coffee table. Picking one can knock others off; items on the floor still need picking (`pick up the swiss cheese from the floors` occurs once in demos).
- Robot start varies across instances, baskets spread up to ~5 m between instances. The coffee table is fixed.
- Cheap fallback: if basket lifting fails, fill baskets where they lie on the floor with the same `place ... in the wicker basket` sentence.

### Hints for the VLM

- Everything is in `living_room_0`. One coffee table (items), one bottom cabinet (basket staging), one sofa, a fireplace, a shelf.
- Distractors: none of the target categories exist outside the 16 targets and 4 baskets in this room.
- Item appearance (unverified from assets): pillar candle, butter cookie, swiss cheese and gift bow are all small objects sitting together on the one coffee table.
- Done per literal: the item lies inside a basket rim in RGB and its depth sits below the rim. Done overall: each basket shows four distinct items, coffee table empty.
