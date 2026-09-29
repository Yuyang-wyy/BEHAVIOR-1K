## Planner notes

**Tier:** B — three batteries (34 x 35 x 61 mm) fit the jaws, but one sits on a high counter behind bar chairs and the target is a cabinet drawer.

### Goal in plain words

All three batteries must be inside one bottom cabinet in the living room; either of the two living-room bottom cabinets counts (`exists`). The goal has **no** `not open` literal, so the drawer may be left open. Nothing else is checked.

### Q traps

- Three literals, each 1/3. None is true at reset. All must be in the same cabinet.
- The task sentence says "then close the drawer", but closing is not a goal literal.
- `inside` tests the battery's AABB centre against the cabinet's fillable volume (PREDICATES §3). Whether an open drawer carries its own volume is not verified. If only the carcass has one, a battery in a pulled-out drawer counts only after the drawer is shut. Closing is cheap (~7 s), so close it anyway.
- Closing the drawer can push a battery that sits near its front edge out of the volume; drop batteries toward the back.
- Every door and drawer of both cabinets starts closed (joint_pos 0 in all 20 instances).

### Minimal plan

1. `move to the battery` — two batteries on the coffee table in view. ~14 s.
2. `pick up the battery from the coffee table` twice, one per hand — both grippers stopped short of closed. ~16 s each.
3. `move to the bottom cabinet` — cabinet front in view. ~14 s.
4. `open the drawer of the bottom cabinet` — drawer visibly pulled out. ~11 s.
5. `place the battery in the bottom cabinet` twice — both batteries in the drawer. ~9 s each.
6. `move to the chair` / `pick up the chair from the floors` / `move to the floors` / `place the chair on the floors` — only if a bar chair blocks the counter. ~50 s.
7. `move to the battery` then `pick up the battery from the countertop` — third battery in hand. ~14 s + 16 s.
8. `move to the bottom cabinet`, `place the battery in the bottom cabinet` — third battery in the drawer. ~23 s.
9. `close the drawer of the bottom cabinet` — drawer flush. ~7 s.

Budget: 385 s limit vs 257 s demo mean.

### What the demos do differently

- 62% of demos fetch the countertop battery first, then the two coffee-table batteries together.
- 392 chair segments in 200 demos: humans move a bar chair away from the counter and later put a chair back. Putting it back is not needed.
- `move to the floors` / `place the chair on the floors` are the demo words for parking the chair.

### Hard parts and hacks

- The countertop battery sits at z 1.11 m on the kitchen-living counter `countertop_tpuwys_0`. Two straight chairs stand at (-0.4, 1.1) and (-1.26, 1.1), in front of the counter (y 1.53) where the battery lies. Reaching over them is the hard step.
- Target choice: `bottom_cabinet_jhymlr_0` (1.65 m wide, 6 openable links, 1.0-2.6 m from start) or `bottom_cabinet_bamfsz_1` (0.42 m wide, 4 links, 1.7-3.7 m). Which link is a drawer is not verified. The demos call both "the bottom cabinet".
- Opening a drawer needs its handle; handle width vs 44 mm is not verified.
- Hack: the coffee table is 1.5 m from `bamfsz_1` and 2.2 m from `jhymlr_0`. Carrying both coffee-table batteries at once saves a round trip.

### Hints for the VLM

- Scene Rs_int. Two batteries lie on the low coffee table in front of the sofa. The third is on the high kitchen counter that divides the kitchen from the living room.
- Two more bottom cabinets stand in the kitchen, one in the entryway and one in the bedroom. They are not in the task scope and do not count.
- Done: all three batteries in the same living-room cabinet, drawer closed.
