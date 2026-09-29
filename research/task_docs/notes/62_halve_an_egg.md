## Planner notes

**Tier:** D — one slice transition (knife touches egg) plus four small pick-and-places, one of them from a closed fridge.

### Goal in plain words

The egg must be cut once, so that both `half__hard-boiled_egg` slots are real. Both halves must rest on the one plate (`plate_232`). The carving knife must end inside the drop-in sink. Nothing is said about the fridge, the cutting board, or where the cut happens, so the fridge may stay open and the egg may be cut anywhere.

### Q traps

- All 5 literals start false, so max partial Q is 1.0 (page is right).
- The two `real` literals are free once the egg is cut (2/5 = 0.4). Cutting is the highest-value single action.
- Halves are diceable (PREDICATES §7). If the knife stays in contact with a half for 2 s after the cut, it re-arms and dices that half: its slot goes `None`, losing `real` and `ontop` for it. Lift the knife straight away.
- Any knife contact with the whole egg slices it, including handle contact and contact while the egg is still held (§7). Do not brush the knife against the egg before it is where you want the halves.
- `ontop half plate` needs the half's centre over the plate and touching it. A half resting on the other half, or half off the rim, does not count.
- `inside knife sink` only checks the knife's AABB centre in the sink volume. Whether `drop_in_sink/awvzkn` has a fillable volume at runtime is unverified; demos place it there 200/200, so assume yes.
- The fridge (`fridge_dszchb_0`, one joint) starts closed (joint_pos 0.0 in all 20 instances). It is not in the goal; leaving it open costs nothing.

### Minimal plan

1. `move to the fridge` — fridge door fills the view. ~13 s.
2. `open the door of the fridge` — door visibly swung open, shelves visible. ~27 s.
3. `pick up the hard boiled egg from the fridge` — gripper closed but not fully; egg gone from shelf. ~15 s.
4. Skip `close the door of the fridge` (goal does not need it; saves ~18 s). Close it only if the open door blocks the base path.
5. `move to the carving knife` (or `move to the cutting board`) — board and knife in view. ~13 s.
6. `pick up the carving knife from the cutting board` with the free hand — knife lifted off the board. ~15 s.
7. `place the hard boiled egg on the cutting board` — egg resting on the board, hand open. ~9 s.
   - Shortcut (untested): place the egg on the plate instead, then cut it there; the halves spawn on the plate and steps 10-13 disappear. No trained prompt; closest: `place the half hard boiled egg on the plate`. Only worth it when plate and board are within one arm's reach.
8. `chop the carving knife with the hard boiled egg` — whole egg replaced by two halves in the image. Lift the knife within 2 s. ~7 s.
9. `move to the drop in sink`, then `place the carving knife in the drop in sink` — knife no longer in hand, visible in the basin. ~5 s + ~8 s.
10. `move to the cutting board` — halves in view. ~13 s.
11. `pick up the half hard boiled egg from the cutting board` twice (one per hand) — both grippers closed, board empty. ~15 s each.
12. `move to the plate` — plate in view. ~13 s.
13. `place the half hard boiled egg on the plate` twice — both halves on the plate surface, hands open. ~9 s each.

Total about 190 s against a 319 s limit.

### What the demos do differently

- 197/200 demos close the fridge right after taking the egg. The goal does not need it.
- The egg is held in one hand while the other hand picks the knife; the cut happens with both hands busy, then the egg hand is free again.
- 11 demos push the cutting board along the counter first (`push the cutting board to the countertop`); not needed.
- Halves are picked one per hand, then placed together, so only one trip to the plate.

### Hard parts and hacks

- Egg size: 58 x 44 x 44 mm (asset bbox, scale 1.0). That is at the ~44 mm jaw limit on every axis, so the grasp may not register. Approach along its long axis so the jaws close across the 44 mm width.
- Halves are 58 x 44 x 22 mm. Lying flat, a top-down grasp must straddle the 44 mm width; the 22 mm edge is easier if the half lands on its side.
- Egg shelf height varies: z 0.49 (6 instances), 0.90 (8), 1.30 (6). The top shelf at 1.3 m needs the trunk raised; the bottom one needs a low reach into the fridge.
- The knife (fqqbop) is 323 x 39 x 24 mm, so its handle fits the jaws.
- Knife re-arm dicing is the silent killer: a VLA that keeps "chopping" will destroy the halves. Stop sending the chop prompt as soon as two halves are visible.
- The halves spawn ~11 mm either side of the egg centre (asset `object_parts`). Cutting on the plate would leave them on the plate directly, but the knife may push them off the plate edge.

### Hints for the VLM

- Kitchen of `house_single_floor`. One counter run along the wall at y ≈ -1.9: fridge at the right end (x 7.8), drop-in sink near x 5.8, board and plate between x 4.6 and 7.3 (they move per instance).
- The egg is a small white oval on a fridge shelf. It is the only egg in the scene.
- The cutting board is a light rectangle 36 x 24 cm with the knife lying on it at start.
- The plate is a 25 cm round flat plate; it is the only plate in the kitchen.
- There is only one sink in the kitchen (the drop-in sink). Other sinks exist in other rooms; ignore them.
- Done: two egg halves on the plate, knife in the sink basin, no whole egg anywhere.
