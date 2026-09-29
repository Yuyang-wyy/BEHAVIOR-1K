## Planner notes

**Tier:** C — one pick and one drawer place, but the jar (forced size 75 x 85 x 150 mm) is wider than the 44 mm jaw span on both short axes, and it sits on a high counter behind bar chairs.

### Goal in plain words

The jar of honey must be inside the entryway bottom cabinet (`bottom_cabinet_slgzfc_0`). The goal has **no** `not open` literal, so the drawer may stay open. Nothing else is checked.

### Q traps

- One literal: Q is 0 or 1.
- The task sentence says "then close the drawer", but that is not a goal literal.
- `inside` tests the jar's AABB centre against the cabinet's fillable volume (PREDICATES §3). Whether an open drawer carries its own volume is not verified; if only the carcass has one, the jar counts only once the drawer is shut. Close it anyway (~10 s).
- The jar is 0.15 m tall. A drawer too shallow for it will jam on closing and can push the jar's centre out. Pick the drawer by eye; drawer depths are not verified.
- All four openable links of the cabinet start closed (joint_pos 0 in all 20 instances).

### Minimal plan

1. `move to the chair` / `pick up the chair from the floors` / `move to the floors` / `place the chair on the floors` — only if a bar chair blocks the counter in front of the jar. ~55 s.
2. `move to the jar of honey` — jar on the counter in view. ~14 s.
3. `pick up the jar of honey from the countertop` — jar lifted, gripper stopped short of closed. ~14 s.
4. `move to the cabinet` — entryway cabinet front in view. ~14 s.
5. `open the drawer of the cabinet` — drawer visibly out. ~12 s.
6. `place the jar of honey in the cabinet` — jar standing in the drawer. ~7 s.
7. `close the drawer of the cabinet` — drawer flush, jar not visible. ~10 s.

Budget: 338 s limit vs 226 s demo mean. Without the chair detour the plan is about 70 s of skills plus walking.

### What the demos do differently

- All 200 demos follow one order. They move a chair away, carry the jar to the breakfast table, put the chair back, pick the jar up again, and only then go to the cabinet. The breakfast-table stop and the chair return are not needed.
- A few demos (2) say `move to the storage container` for the cabinet. Stick with `move to the cabinet`.

### Hard parts and hacks

- Grasp: the task forces the jar to 0.075 x 0.085 x 0.15 m. Neither short axis fits 44 mm, and the jar has no handle. Grasp may fail outright; the lid rim is not a separate part (single link, not verified to be narrower).
- Height: the jar stands on the counter top at about 1.08 m (jar centre z 1.16), behind two straight chairs at (-0.4, 1.1) and (-1.26, 1.1).
- The cabinet is in entryway_0 at (1.67, 2.2), facing -x; 2.5-3.5 m from the start.
- Opening the drawer needs its handle; handle width is not verified.

### Hints for the VLM

- Scene Rs_int. The jar is the only jar on the high counter between the kitchen and the living room.
- `the cabinet` in the demo prompts is the single bottom cabinet in the entryway. Five other bottom cabinets exist (two in the kitchen, two in the living room, one in the bedroom); they are not in scope.
- Done: jar inside the entryway cabinet, drawer closed.
