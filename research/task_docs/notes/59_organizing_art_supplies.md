## Planner notes

**Tier:** B — four small desk items into a tote, then the tote onto the desk; marker, glue stick and eraser fit the 44 mm jaw, the paintbrush and the tote handle are unverified.

### Goal in plain words

- The marker, paintbrush, glue stick and rubber eraser must all end with their centres inside the tote.
- The tote must end resting on the bedroom desk (`desk_aduafr_0`, the only desk in bedroom_0).
- One ground option, 5 literals, none true at reset, so partial Q counts each item and the tote placement at 0.2 each.
- Nothing forbids extra objects in the tote or anything else on the desk.

### Q traps

- Partial Q reads only the final state (PREDICATES §1). An item that falls out while the tote is lifted, carried or set down loses its 0.2.
- `inside` tests only the item's AABB centre against the tote's fillable volume (PREDICATES §3). A paintbrush (0.18 m long) poking out still counts if its centre is in; an item resting on the rim does not.
- The tote asset `tote/bnkjle` has an encrypted USD; its fillable volume could not be checked offline (unverified, but the task is designed around it).
- `ontop tote desk` needs the tote touching the desk with the desk under the tote's centre (PREDICATES §4). The desk top is plain (asset bbox 0.63 x 1.51 x 0.785 m, no hutch; three drawers), so any spot on the top works.
- A tote left half over the desk edge fails `ontop` and can tip items out.
- Whole-task Q was 0.00 in both closed-loop runs on 311 (page); nothing scored at all.

### Minimal plan

Demo order (80% of demos use it). Pick two items per trip, one per hand.

1. `move to the marker` — marker centred in the head camera at arm's reach; ~10 s.
2. `pick up the marker from the desk` — gripper closed but not fully shut, marker gone from the desk; ~17 s.
3. `move to the rubber eraser` — ~10 s.
4. `pick up the rubber eraser from the desk` — second gripper closed short of fully shut; ~17 s.
5. `move to the tote` — tote on the floor at close range; ~10 s.
6. `place the marker in the tote` — gripper open, marker not visible on the floor or rim; ~11 s.
7. `place the rubber eraser in the tote` — same check; ~11 s.
8. `move to the glue stick`, `pick up the glue stick from the desk` — ~27 s.
9. `move to the paintbrush`, `pick up the paintbrush from the desk` — ~27 s.
10. `move to the tote`, `place the paintbrush in the tote`, `place the glue stick in the tote` — ~32 s.
11. `pick up the tote from the floors` — tote off the floor, contents still visible inside; ~17 s.
12. `move to the desk` — desk top in view; ~10 s.
13. `place the tote on the desk` — gripper open, tote upright and fully on the desk top; ~10 s.

Demo pace is ~205 s against a 309.7 s limit, so there is ~100 s for retries.

### What the demos do differently

- All 200 demos leave the tote on the floor while filling it and carry it to the desk last. None bring the tote to the desk first.
- Item order varies (109 distinct object orders), but always two items per trip, both placed before the next trip.
- No hand-overs, no drawer use, no extra steps. The demo is already minimal.

### Hard parts and hacks

- **Grasp widths (custom_lists forced sizes).** Marker 0.14 x 0.022 x 0.022, glue stick 0.12 x 0.03 x 0.03, eraser 0.075 x 0.035 x 0.02: all straddle the 44 mm jaw top-down across the short axis.
- **Paintbrush** is forced to 0.18 x 0.05 x 0.015 m. Its widest cross-axis extent (0.05 m) exceeds 44 mm; the handle is presumably narrower, so grasp the handle, not the bristle end (handle width unverified).
- **Tote grasp.** Tote bbox is 0.34 x 0.24 x 0.47 m (asset metadata), taller than wide, so the top part is presumably the handles. A handle ≤ 44 mm is needed; unverified.
- **Items spread along the desk.** Across the 20 instances the four items span ~1.4 m along the desk's long axis (x -5.94 to -4.52). Expect one base move between items.
- **Tote 1-2.5 m from the desk**, on the floor at z 0.19; reaching into it from standing needs the trunk bent down.
- **Hack (untested, out of demo order):** carry the empty tote to the desk first, then place items into it on the desk. Nothing loaded is ever carried, so no spill risk, and every item place is at desk height. The prompts stay the trained strings (`pick up the tote from the floors`, `place the tote on the desk`, `place the X in the tote`), but Comet never saw the tote on the desk during `place in`.
- Earlier scripted attempts on instance 301 got zero confirmed grasps (radio_generalization_20260920/PICK_PLACE_STATUS.md); perception, not the jaw span, was the blocker there.

### Hints for the VLM

- Everything is in bedroom_0. The desk is the only desk in that room; other desks exist in living_room_0 and bedroom_2 and are wrong.
- Other surfaces in bedroom_0: bed, nightstand, taboret, two bookcases. Items start only on the desk.
- The tote (bbox 0.34 x 0.24 x 0.47 m) starts on the floor of bedroom_0, 1-2.5 m from the desk.
- Done for each item: it is visible inside the tote opening and absent from the desk.
- Done for the tote: it sits upright on the desk top, not overhanging, with the four items still inside.
