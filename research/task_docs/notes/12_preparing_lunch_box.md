## Planner notes

**Tier:** B — five small pick-and-place items into an open box, plus one fridge door open/close; no state change. The flat cookie is the awkward grasp.

### Goal in plain words

- Two apple halves, the club sandwich, the chocolate chip cookie and the bottle of tea must all be `inside` the one packing box.
- The fridge must be closed at the end (`not open`, 5 % rule, PREDICATES §6).
- The box has no joints (no `joint_pos` in the template), so it is always open; nothing to close on it.
- Where the box stands does not matter. Moving it is allowed.
- There is exactly one of each object in the kitchen; no distractors of the same category.

### Q traps

- `not open fridge` is true at reset (fridge `joint_pos` 0.0 in the template and all 20 instances). It never scores. Max partial Q = 5/6 = 0.833.
- Leaving the fridge open after taking the tea costs no partial Q but blocks success. Close it right after the tea pick, as every demo does.
- `inside` tests only the item's AABB centre in the box volume (PREDICATES §3). An item resting on the rim or on another item poking out of the box can fail. Check after each drop.
- Knocking the box (e.g. while carrying the tea bottle into it) can tip it and spill earlier items. Items lost at the end score 0.
- Closed-loop on 311: zs_pt50 Q=0.67 (4 of 5 items), ft40k Q=0.50 (3 of 5).

### Minimal plan

1. `move to the packing box` — box centred in view, base stopped. ~10 s.
2. `pick up the packing box from the countertop` — box lifted. ~13 s. Optional, see below.
3. `move to the chopping board` — ~10 s.
4. `place the packing box on the countertop next to the right chopping board` — box resting beside the board. ~5 s.
5. `push the chocolate chip cookie to the to_the_edge_of chopping board` — cookie overhangs the board edge. ~20 s.
6. `pick up the chocolate chip cookie from the chopping board` — gripper stopped short of full close, cookie lifted. ~13 s.
7. `place the chocolate chip cookie in the packing box` — cookie not visible outside the box. ~10 s.
8. `pick up the half apple from the chopping board` (x2, one per arm), then `place the half apple in the packing box` (x2). ~13 s + ~10 s each.
9. `pick up the club sandwich from the chopping board`, `place the club sandwich in the packing box`. ~23 s.
10. `move to the fridge` — ~10 s. `open the door of the fridge` — door swung wide, shelves visible. ~32 s.
11. `pick up the bottle of tea from the low_level fridge` (or `middle_level` / `high_level` by which shelf it is on) — bottle lifted clear. ~13 s.
12. `close the door of the fridge` — door flush. ~18 s. Do this before walking back.
13. `move to the packing box`, `place the bottle of tea in the packing box`. ~20 s.

Budget: demo mean 275 s vs limit 412 s. Steps 2-4 cost ~30 s but save two or three carries of ~1.8 m.

### What the demos do differently

- 191/200 demos move the box next to the chopping board first (onto the countertop, or onto the burner in 76 demos). The goal does not need it; it only shortens carries.
- 187/200 demos push the cookie to the board edge before picking it. Keep this; the cookie is flat (scaled 1.25 x 1.25 x 2.99 on a thin model).
- All 200 demos do the food first and the tea last, and all close the fridge before placing the tea.
- The tea pick prompt names the shelf level: low 95, middle 60, high 45 demos. Tea z is 1.31 or 1.38 m across instances 301-320.

### Hard parts and hacks

- Fridge door: opening needs the handle; handle width vs 44 mm not verified. Demos take ~32 s for it, the slowest skill.
- Tea bottle high in the fridge (z 1.31-1.38): reach past the open door; clutter on the shelf unknown.
- Cookie: flat, only graspable once it overhangs the board edge. A VLA that skips the push will close on air.
- Apple halves and club sandwich: sizes not in custom_lists (unknown vs 44 mm). The sandwich model is scaled 0.74. Demos grasp both.
- Box position: on the same countertop (`countertop_kelker_0`) as the board, about 1.5-2 m away in most instances (box y 0.0-0.4, board y -1.5 to -1.8). In instance 315 the box already sits near the board (y -1.16); skip steps 2-4 there.
- Placing the bottle upright into the box may catch the rim and tip the box. Lower it well inside before releasing.

### Hints for the VLM

- Kitchen only. The chopping board with the four food items is on the countertop near the wall cabinets, not the sink counter. The fridge is at the far end of the kitchen near the sink counter (around x 7.8, y -2.0); tea x-y stays within ~0.2 m of the fridge centre in all 20 instances, so it sits on a shelf inside the body, not in the door.
- The packing box is a small open cardboard box on the same countertop as the board.
- Done for each food item: board empty of that item and the item visible inside the box from above.
- Done for tea: bottle visible standing or lying inside the box, not leaning on the rim.
- Done for the fridge: door flush with the body, no gap.
