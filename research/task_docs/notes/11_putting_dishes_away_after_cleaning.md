## Planner notes

**Tier:** B — eight plates, grasped by the rim, carried into a wall cabinet whose two doors must be opened and re-closed; no state change.

### Goal in plain words

- All 8 plates must end up `inside` one cabinet, the same one for all 8.
- Any of the 6 kitchen cabinets in scope may be chosen (6 ground options). The three wall cabinets `top_cabinet_lkxmne_0/1/2` and three base cabinets (`bottom_cabinet_no_top_gjeoer_0`, `bottom_cabinet_no_top_rkgjer_0`, `bottom_cabinet_fancyy_0`) are the candidates.
- All 6 cabinets must be closed at the end (`not open`, 5 % rule, PREDICATES §6).
- Plates start 4 on the bar (`bar_udatjt_0` = countertop.n.01_1, plates z ~1.06) and 4 on the sink countertop (`countertop_kelzer_0` = countertop.n.01_2, plates z ~0.90).

### Q traps

- The 6 `not open` literals are true at reset (all cabinet `joint_pos` ~0 in the template and in all 20 instances 301-320). They never score. Max partial Q = 8/14 = 0.571.
- Leaving any cabinet door ajar costs no partial Q but blocks full success (1.0). The only route above 0.571 is success.
- Splitting plates across two cabinets scores only the larger group. Pick one cabinet and put all 8 there.
- Closing a door onto a plate can push its centre out of the volume (PREDICATES §3). Close only after the last plate, then check no plate sticks out.
- A plate resting on the cabinet top or on the counter under it is not inside.
- Closed-loop ft40k on 311 scored Q=0.50, i.e. 7 of 8 plates inside. Door state at the end is not recorded; partial Q ignores it.

### Minimal plan

1. `move to the top cabinet` — base stopped, facing the counter under the wall cabinet above `countertop_kelker_0`. ~12 s.
2. `open the door of the right_door top cabinet` — right door visibly swung open. ~26 s.
3. `open the door of the left_door top cabinet` — left door open, shelf visible. ~26 s.
4. `move to the plate` — base stopped near the sink counter plates. ~12 s.
5. `pick up the plate from the countertop` — gripper closed, stopped short of full close, plate lifted off the counter. ~8 s.
6. Repeat 4-5 for a second plate with the other arm (demos always carry two plates per trip).
7. `move to the top cabinet` — ~12 s.
8. `place the plate in the low_level top cabinet` (first two plates) or `place the plate on the plate` (later ones, stacking) — gripper open, plate on the shelf behind the door line. ~10 s each.
9. Repeat 4-8 for the other sink-counter pair, then twice with `pick up the plate from the bar`.
10. `close the door of the left_door top cabinet`, then `close the door of the right_door top cabinet` — both doors flush with the frame. ~14 s each.

Budget: demo mean 365 s vs limit 548 s. Four two-plate trips fit; eight one-plate trips probably do not (8 x ~40 s travel/pick/place plus ~80 s of doors is tight, estimate only).

### What the demos do differently

- All 200 demos use `top_cabinet_lkxmne_1` (cabinet.n.01_3); 2 of them also have a stray `place the plate in the low_level countertop` segment. No demo uses a base cabinet, so the base cabinets have no trained prompts (closest: `place the plate in the low_level top cabinet`).
- All demos pick exactly 8 times and carry two plates per trip (one per hand), then place both.
- Plates after the first two are stacked: `place the plate on the plate` (1200 segments). That still scores as long as each plate's centre is inside the cabinet volume.
- Demos open both doors first and close both at the very end. That order is correct; keep it.
- The order of counter vs bar pairs varies (29 distinct orders); it does not matter.

### Hard parts and hacks

- Reach: the wall cabinet centre is at z 1.79. Placing into it needs the trunk raised and arms extended high; tipping risk is low with plates but the shelf height is not verified.
- Stacking 8 plates on one shelf: whether 8 stacked plates fit under the upper shelf/cabinet top is not verified. A stack that slides out past the door line loses literals and can block the door.
- Grasp: plates are wider than 44 mm, so only the rim is graspable. Plate models xfjmld, luhkiz, ntedfx, pkkgzc; rim thickness unknown. Demos show rim grasps work.
- Door handles on `lkxmne` doors: width not verified; the demos open them.
- Door closing must be within ~4.5° of shut per door; a rebound fails success silently.
- Unverified alternative: `bottom_cabinet_no_top_gjeoer_0` sits right under the same wall cabinet (z 0.42). It avoids high reach but needs low bending and has 4 joints (all must be closed), and no demo prompt covers it.

### Hints for the VLM

- Kitchen only. Plates are on the long bar (farther from the wall cabinets, higher) and on the countertop around the sink.
- Target: the middle one of three identical wall cabinets over the countertop without a sink (`top_cabinet_lkxmne_1`, around x 4.0, y -0.5). The other two are distractors of the same model; any works for the goal but only the middle one has demo coverage.
- A water glass is also in the kitchen; ignore it.
- Done for `inside`: no plate visible on either counter; stacked plates visible on the cabinet shelf behind the door plane.
- Done for `not open`: both wall-cabinet doors flush, no gap; also check no base cabinet door was bumped open.
