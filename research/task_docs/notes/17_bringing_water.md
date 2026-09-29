## Planner notes

**Tier:** B — two beer bottles (0.075 m body, 0.26 m tall) go from the fridge to a low coffee table. The body is wider than the 44 mm span; the grasp must go on the neck (neck width not in the asset metadata; unverified that it is under 44 mm).

### Goal in plain words

Both beer bottles must rest on the living-room coffee table (`coffee_table_rlsebe_0`, in living_room_0).
The bottles are interchangeable and any spot on the table top works.
The fridge must be closed at the end.

### Q traps

- 3 literals. `not open fridge` is already true at reset (fridge joint_pos 0.0 in all 20 instances), so it never scores. Max partial Q is 0.667, one bottle = 0.333.
- Full success still needs the fridge closed. Opening it and leaving it open caps Q at 0.667.
- The scene has three coffee tables: living_room_0 (the target), living_room_1 and garden_0. A bottle on the wrong coffee table scores 0.
- `ontop` needs direct contact with the table top (PREDICATES §4). A bottle that tips over and rolls off the 0.27 m-high table scores 0. Stand it upright near the table centre.
- Success is checked every step. If the fridge is closed first and the bottles are placed last, the episode ends with success on the second placement.

### Minimal plan

Robot starts in the kitchen, 1-4.4 m from the fridge. The target table is 3.8-7.6 m away.

1. `move to the fridge` — fridge door centred in view. ~47 s.
2. `open the door of the fridge` — single door swung wide, shelves visible. ~51 s.
3. `pick up the beer bottle from the middle_level fridge` (or `low_level` / `high_level`, whichever shelf the bottle is on) — bottle out of the fridge in the right gripper. ~27 s.
4. `hand over the beer bottle with the right` — bottle now in the left gripper, right gripper empty. ~11 s.
5. `pick up the beer bottle from the low_level fridge` (shelf as seen) — second bottle in the right gripper. ~27 s.
6. `close the door of the fridge` — door flush. ~22 s. Doing it here, with both hands full, saves the ~65 s return trip the demos make; no demo closes it at this point, so it is untested. If the arms cannot push the door with a bottle in hand, fall back to step 9.
7. `move to the coffee table` — low square table in the living room with sofas around it. ~47 s.
8. `place the beer bottle on the coffee table` twice — both bottles upright on the table, grippers open. ~19 s + 19 s.
9. (only if step 6 was skipped) `move to the fridge`, `close the door of the fridge`. ~47 s + 22 s.

Budget: about 250 s with step 6, 320 s without, against a 472 s limit.

### What the demos do differently

- 199/200 demos close the fridge only at the very end, after walking back from the living room.
- 119 demos use a right-to-left hand-over to pick both bottles with one arm reaching into the fridge; the rest pick one per hand directly.
- The shelf word in the pick prompt (`high_level`, `middle_level`, `low_level`) varies by instance; pick the one matching where the bottle is seen.

### Hard parts and hacks

- Grasp: the bottle body is 75 mm, too wide. The neck must be straddled. Reaching a neck inside a fridge shelf with shelves above is tight.
- Placing a tall bottle upright on a low (0.27 m) table requires lowering the arm far; the robot's trunk must bend. Laying the bottle on its side also scores, but it may roll off.
- Both hands are full on the way back, so closing the fridge needs a free arm or a push with the forearm or base.

### Hints for the VLM

- The fridge is the only fridge, in the kitchen: a single tall door (door link 1.37 m tall). The bottles are brown beer bottles inside.
- The target coffee table is the 0.98 m square low table in the living room with four sofas and a gas fireplace. The other living room (three sofas) has a different coffee table; do not use it. A third coffee table is in the garden.
- Done for each bottle: resting on the table top, not on a sofa or the floor. Done for the fridge: door flush with the body, no gap.
