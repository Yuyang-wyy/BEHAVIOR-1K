## Planner notes

**Tier:** C — four dishes carried about 13 m through a bar flip-up and a closed kitchen door. The plates are flat (28 mm thick, lying on a table), and no dish has a bbox axis of 44 mm or less except the plate thickness.

### Goal in plain words

Both bowls and both plates must be inside the commercial kitchen sink. Stacking is fine: only each dish's AABB centre has to be inside the sink volume. The dirt and stain on the dishes are not in the goal; no cleaning is needed. Nothing else is checked, and the doors may stay open.

### Q traps

- Four literals, each 1/4, all false at reset.
- `inside` tests only the dish's AABB centre (PREDICATES §3). A dish perched on the sink rim or on the faucet deck does not count; a bowl stacked on a bowl inside the basin does.
- The sink `commercial_kitchen_sink_xecfyh_0` has fluid and toggle meta links; its fillable volume is not readable from metadata and is not verified here.
- The bar flip-up lid (`bar_xxftww_0`) and the kitchen door (`door_mkcndz_0`) start closed (joint_pos 0). Closing them again, as the demos do, is not a goal literal.

### Minimal plan

1. `move to the booth` — dishes on the booth table in view. ~34 s.
2. `pick up the bowl from the booth` twice, one per hand — both grippers stopped short of closed. ~8 s each.
3. `move to the flipup countertop` then `open the lid of the flipup countertop` — bar flap raised. ~34 s + 7 s.
4. `move to the kitchen door` then `open the door of the kitchen door` — door swung open. ~34 s + 10 s.
5. `move to the commercial kitchen sink` — basin in view. ~34 s.
6. `place the bowl in the commercial kitchen sink`, then `place the bowl on the bowl` — both bowls in the basin. ~15 s + 12 s.
7. `move to the booth`, `pick up the plate from the booth` twice, `move to the commercial kitchen sink`, `place the plate in the commercial kitchen sink`, `place the plate on the plate` — both plates in the basin. ~140 s.

Budget: 607 s limit vs 405 s demo mean. Skipping the demos' close-lid and close-door steps saves about 30 s plus two detours.

### What the demos do differently

- 98% of demos use one order: bowls first (both hands), open lid and door, sink; back for the plates; close lid and door on the second trip; sink.
- The closing steps (`close the lid of the flipup countertop`, `close the door of the kitchen door`) are housekeeping. Skip them.

### Hard parts and hacks

- Grasp widths (asset bboxes): bowl 0.117 x 0.105 x 0.060 m; plate 0.169 x 0.176 x 0.028 m. The bowl can only be held across its rim wall. The plate's 28 mm axis is vertical, so the jaws must get under its edge on the table. Expect plate grasps to fail.
- Distance: the dishes are on `booth_xzrpar_2` at (0.12, -9.11) in the far end of the dining room; the sink is in kitchen_0 at (-10.78, 0.92). Human base travel averaged 57 m per demo.
- Route: every demo passes the bar flip-up and the kitchen door, so treat both as on the path. Opening them needs graspable handles; widths not verified.
- Four booths are in the dining room; only `booth_xzrpar_2` holds dishes.

### Hints for the VLM

- Scene restaurant_diner. Two bowls and two plates sit together on one booth table. The robot starts about 2.2-11 m from them.
- The sink is the large commercial kitchen sink in kitchen_0; the bathroom's five furniture sinks are not the target.
- Done per literal: dish visible down in the basin, not on the rim.
