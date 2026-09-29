## Planner notes

**Tier:** C — carry two plated pizzas into a closed two-door fridge and two bowls into a sink; plate and bowl widths vs the 44 mm span are unverified, and each plate must be carried level so the pizza stays on it.

### Goal in plain words

- Both pizzas must end inside the fridge, each still resting on a plate. Either pizza may sit on either plate (`forpairs`).
- Both bowls must end inside the one sink (`drop_in_sink_lkklqs_0`).
- The fridge must end with both doors shut (within 5 % of closed, PREDICATES §6).
- The kitchen has one fridge and one sink, so there are no container choices to make.

### Q traps

- 7 literals. `not open fridge` is true at reset: it never scores but blocks success. Verified in the template and all 20 instances: both fridge joints are at ~0.
- The page's "best option" (0.857) pairs pizza_2 with plate_1 and pizza_1 with plate_2. That option only pays if the pizzas are swapped between plates. Nobody should do that.
- Keep each pizza on its own plate. Then both `ontop` literals are true at reset and never score. The realistic partial Q is 4/7 = 0.571: 2 pizzas inside the fridge plus 2 bowls inside the sink.
- Full success (1.0) needs both pizzas still `ontop` their plates at the end. A pizza that slides off in transit, or rests half on the fridge shelf, blocks success.
- `inside` tests the pizza's AABB centre, not the plate's. The pizza must be fully on a fridge shelf, not on a door bin (door bins have unverified volume, §16).
- Close the fridge only after both plates are in. Closing can push a plate out or leave a door ajar (§3, §6).
- If the fridge ends open, you lose success but no partial Q. Bowls in the sink still score on their own.
- In instances 306 and 309 the pizza starts ~5 cm higher than on the others (z 0.74-0.75 vs 0.70). It may rest tilted on the plate rim. Unverified.

### Minimal plan

1. `move to the fridge` — base stopped facing the fridge doors. ~26 s.
2. `open the door of the right_door fridge` — right door visibly swung wide, shelves visible. ~40 s.
3. `move to the plate` — plate with pizza centred in the head camera. ~26 s.
4. `pick up the plate from the breakfast table` — plate lifted clear of the table, pizza still on it, gripper stopped short of fully closed. ~24 s.
5. `move to the fridge` — ~26 s.
6. `place the plate in the layer_5 fridge` — plate on a shelf, gripper open and withdrawn, pizza on the plate. ~19 s.
7. Repeat 3-6 with `place the plate in the layer_4 fridge` — second plate on another shelf. ~95 s.
8. `close the door of the right_door fridge` — door flush with the body, no gap visible in depth. ~22 s.
9. `move to the bowl`, then `pick up the bowl from the breakfast table` — bowl lifted. ~50 s.
10. `move to the bowl`, then `pick up the bowl from the breakfast table` — second bowl in the other hand. ~50 s.
11. `move to the drop in sink` — ~26 s.
12. `place the bowl in the drop in sink` twice — both bowls below the sink rim, grippers open. ~38 s.

- Total is about 420 s against a 684.8 s limit. There is ~260 s of slack for retries.
- If time runs low, do the bowls (steps 9-12) first. They are 2/7 of Q and need no door.

### What the demos do differently

- 64 % of demos use exactly the order above: fridge first, then bowls.
- The humans open only the right fridge door. The template has 2 fridge joints; the left door is never touched and stays closed.
- The humans carry one plate per trip, but both bowls in one trip (one per hand).
- 2 of 200 demos use `push the plate to the center fridge` to nudge the plate deeper onto the shelf. That is a useful recovery when the plate sits near the shelf edge.

### Hard parts and hacks

- Grasping the plate: a flat plate has no handle. The rim thickness is not verified against the 44 mm span. The pizza (scale 0.63 x 0.64 x 2.34) rides loose on top.
- Carrying the plate level while the base moves ~36 m in total (human mean). A tilt dumps the pizza, and then `ontop` fails.
- Placing inside the fridge at shelf height: the arm must reach in past the open door without hitting it closed.
- The fridge door handle width is not verified. Closing can be done by pushing with no grasp (§6).
- Sink `inside`: the sink needs a fillable volume in its runtime USD (§3). This is not verified for `drop_in_sink/lkklqs`. Dropping from just above the basin is enough.
- The sink has a ToggledOn state (the faucet). It is not in the goal; leave it alone.
- No scripted shortcut beats the VLA here. Every scoring literal needs a carried object.

### Hints for the VLM

- Everything is in `kitchen_0`. The breakfast table is at z ~0.63 m and holds 2 plates with pizzas and 2 bowls. The plates sit close together near x ~4.0-4.3, y ~1.3-1.9.
- The fridge is the only fridge in the kitchen (`fridge_petcxr_0`), a tall two-door unit.
- The sink is the single drop-in sink set in the counter.
- Distractors in the kitchen: a microwave, oven, dishwasher, 2 top cabinets, and 4 straight chairs around the table. None of these is a valid target.
- Done for the pizzas: both plates visible on fridge shelves with pizzas on top, then the fridge door flush and closed.
- Done for the bowls: both bowls visible inside the sink basin, below the rim, not on the counter beside it.
