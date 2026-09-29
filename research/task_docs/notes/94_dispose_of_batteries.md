## Planner notes

**Tier:** B. Batteries are 0.034 x 0.035 x 0.061 m (asset bbox, scale 1), so they fit the 44 mm jaws. The difficulty is distance: two batteries are ~14.5 m away behind a closed door.

### Goal in plain words

- All three batteries must end inside the copy-room trash can (`trash_can_159`, model wklill).
- That trash can must also be resting on the **copy-room** floor (`floors_tkyckr_0`) at the end.
- Battery 3 starts on the copy-room bottom cabinet, near the start. Batteries 1 and 2 start on the desk in private_office_0 (`desk_mdhelw_2`).

### Q traps

- There are 4 literals. `ontop ashcan floor.n.01_1` is true at reset and never scores, so the best partial Q is 0.75.
- **The trash-can trap.** If the bin is carried to the office and left there, `ontop ashcan floor.n.01_1` becomes False and success is impossible. That floor literal names the copy-room floor. Either leave the bin in the copy room or bring it back and set it on the copy-room floor.
- A bin tipped over while dropping batteries in loses the ones already inside (§3). It also stops being `ontop` the floor if it rests on its side on something else.
- The private_office_0 door starts closed (`joint_pos` 0). The goal does not care about the door, but the robot must get through it.

### Minimal plan

Keep the bin in the copy room and carry batteries to it.

1. `move to the battery`. Go to the one on the copy-room bottom cabinet. About 44 s (demo mean; this one is ~1.5 m away).
2. `pick up the battery from the cabinet`. Done when the fingers stop short of fully closed around it. About 19 s.
3. `move to the trash can`. About 20 s.
4. `place the battery in the trash can`. Done when the gripper is open and the battery is not on the rim or the floor. About 14 s.
5. `move to the wooden door`. About 44 s.
6. `open the door of the wooden door`. Done when the doorway is visibly clear. About 17 s.
7. `move to the battery`. Go to the office desk. About 44 s.
8. `pick up the battery from the desk`, once per hand for both batteries. About 19 s each. If a chair blocks the desk, first `push the swivel chair to the desk` (about 22 s).
9. `move to the trash can`. Travel back to the copy room. The demos' mean `move to` is 44 s, and this trip is longer.
10. `place the battery in the trash can`, twice. About 14 s each.

- Totals: about 330 s against a 721.4 s limit.

### What the demos do differently

- All 200 demos pick up the trash can (`pick up the trash can from the floors`, 200 of 200) and carry it through the task. They place the batteries into the held bin, then walk back and `place the trash can on the floors`.
- That return trip averages about 136 s in the representative demo. It is required only because they moved the bin.
- If Comet insists on the bin-carry pattern, the final `move to the floors` and `place the trash can on the floors` must happen **in the copy room**.
- 110 of 200 demos push a swivel chair aside at the office desk.

### Hard parts and hacks

- **Two-handed carry.** One battery per hand saves a 29 m round trip. Check both grippers stopped short of closed before leaving the office.
- **Long navigation** (~14.5 m each way) through a corridor with many identical doors. Rotation odometry drifts, so re-identify the copy room by its trash can and cabinet rather than by dead reckoning.
- Batteries are small and can roll off the desk when a chair or arm bumps it. Re-check both on the desk before grasping.
- The trash can is 0.41 x 0.30 x 0.44 m. Drop from just above the opening.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- Copy room: one bottom cabinet (battery on top, z ~1.05 m), one top cabinet and the trash can on the floor. The robot starts here.
- private_office_0: one desk with two batteries (z ~0.81 m), three swivel chairs, and the wooden door to the corridor.
- There are no other trash cans or batteries in these rooms.
- Done: no battery visible on the cabinet or desk, three batteries seen inside the bin, and the bin upright on the copy-room floor.
