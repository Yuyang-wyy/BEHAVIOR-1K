## Planner notes

**Tier:** C — four large, bushy branches (0.63 m long) must go into a lidded bin 0.91 m tall, and they are scattered along a ~16 m garden strip.

### Goal in plain words

All four branches must end inside the recycling bin, and the bin must still stand on the garden floor. The lid is not in the goal; it can be left open.

### Q traps

- 5 literals. `ontop recycling_bin floor` is true at reset, so it never scores, but tipping or lifting the bin breaks success. Max partial Q = 4/5 = 0.8.
  - In every instance the bin root sits at z 0.47, the same height, which is consistent with the bin on the floor. This is inferred; there is no sim check.
- Result on 311 (ft40k): Q = 0.00.
- `inside` tests the branch's AABB centre against the bin's volume (PREDICATES §3). A branch lying across the rim, or across the open lid, does not count.
- **Capacity (derived):** the forced sizes are bin 0.684 × 0.588 × 0.912 m and branch 0.625 × 0.30 × 0.255 m. Four branches stacked flat are ~1.0 m high, taller than the bin.
  - The last branch's centre may end up above the volume. Drop branches in steeply or on end so they pack.
- Do not push the bin to the branches with the base: that risks tipping it (the ontop literal). Seven demos push it anyway.

### Minimal plan

1. `move to the recycling bin` ~29 s.
2. `open the lid of the recycling bin` — the lid is visibly up and the opening clear. ~37 s. The lid starts closed (joint_pos 0) in all 20 instances. The demos log 310 open-lid segments over 200 episodes, so a retry is common.
3. `move to the branch`, `pick up the branch from the floors` — the branch is lifted clear of the ground. ~29 + 23 s.
4. `move to the branch`, `pick up the branch from the floors` with the other hand, as in the demos. ~29 + 23 s.
5. `move to the recycling bin`, `place the branch in the recycling bin` ×2 — each branch drops below the rim. ~29 + 2 × 9 s.
6. Repeat steps 3-5 for the last two branches.
7. Skip `close the lid of the recycling bin`; it is not in the goal, and closing could lift a branch that pokes out.

Demo mean 418 s against a 626 s limit. The walking dominates: the demos cover 41 m of base travel.

### What the demos do differently

- They carry two branches per trip, one per hand. 62-72/200 follow exactly two-and-two.
- All 200 close the lid at the end. This is not needed.
- 7/200 push the bin toward the driveway.

### Hard parts and hacks

- **Branch grasp:** the whole branch is 0.63 × 0.30 × 0.26 m, so only a single twig or the stem can be gripped. Twig thickness is not in the metadata (unverified vs the 44 mm span). Grab near the stem so the branch does not swing into the bin rim.
- **Scatter:** branches and bin are placed along a strip at x -16 to +0.5, y -3 to +1.4. Their spread per object across instances is 14-16 m. Expect branches out of view at the start.
- **Lid:** the bin has three movable links but one joint. Opening it needs a grip on the lid edge. A lid that falls back shut blocks every insert.
- Tipping risk: carrying two 0.63 m branches spread wide at shoulder height. Keep them low while driving.
- A dropped branch that lands against the bin but outside it is common. Re-check after each place.

### Hints for the VLM

- The garden of house_double_floor_lower, along the strip y ≈ -3 to +1.5, x ≈ -16 to +0.5. There are many bushes (55) and trees (26); the task branches are loose, lying flat on the paved/grass ground at z ~0.05 m.
- The recycling bin is the only bin in the garden: 0.9 m tall, with a hinged lid (one joint).
- Done: four branches visible inside the bin opening, none on the ground or across the rim, and the bin upright.
