## Planner notes

**Tier:** C — one pick-and-place, but the alarm is a 100 x 100 x 38 mm disc lying flat, and it must be mounted on a wall nail 1.71 m up within 5 cm and 15°.

### Goal in plain words

One literal: `attached fire_alarm_102 wall_nail_wlnail_1`. The task sentence says "two smoke detectors"; the BDDL has only one fire alarm and one nail, so one attach is full success. The attach happens by itself the moment the alarm's back mount touches the nail in the right pose; no release is needed, and success ends the episode on that step.

### Q traps

- Single literal, so Q is 0 or 1. There is no partial credit for carrying the alarm near the nail.
- Page error: the BDDL puts the nail `inroom living_room`, but the sampled scene object `wall_nail_wlnail_1` is listed `in_rooms ['kitchen_0']` in the template and sits at (8.40, 2.87, 1.71) in all 20 instances. The alarm starts on the living-room coffee table around (3.2-3.9, 4.6-5.9). Expect ~5.5 m of travel.
- Time limit is only 128 s (demo mean 86 s). Every re-grasp costs ~20 s; two failed grasps use up the budget.
- The other two `wall_nail` objects in the scene are in `garage_0`, which is not loaded. There is no distractor nail.
- The alarm's toggle button (`togglebutton` on the front face) is irrelevant; pressing it does not matter.

### Minimal plan

1. `move to the fire alarm` — the white disc on the coffee table is centred in the head camera. ~22 s demo mean; the table is 1.1-2.0 m away, so less.
2. `pick up the fire alarm from the coffee table` — gripper closed but not fully, disc lifted clear of the table. ~21 s.
3. `move to the wall nail` — base stopped facing the wall with the nail at the top of the image. ~22 s (longest leg).
4. `attach the fire alarm to the wall nail` — disc stays on the wall after the gripper opens; episode ends with success if attached. ~11 s.

This is exactly the demo plan (156/200 demos). Nothing can be dropped.

### What the demos do differently

- 44 of 200 demos put the alarm back on the coffee table and re-grasp it (`place the fire alarm on the coffee table`), presumably to fix the grip orientation for wall mounting. A planner should allow one such re-grasp if the disc is held face-down.
- No demo uses a hand-over or second arm.

### Hard parts and hacks

- Grasp: the disc is 100 mm across and 38 mm thick (asset bbox, scale 1.0). Only the 38 mm thickness fits the 44 mm jaw span, and while it lies flat that needs a finger under it (same problem as the books). Pinching it at the table edge, or tipping it up against something first, are the realistic options. Unverified whether assisted grasp registers at all.
- Mount geometry: the male link `displaywallM` is at the disc's back centre (z -15 mm) with a 90° pitched frame; the nail's `displaywallF` is 15 mm behind the nail tip. The disc must be held upright, back face to the wall, centred on the nail, within 5 cm and 15° (PREDICATES §10). A top-down grasp that leaves the disc horizontal will never attach.
- Height: the nail is at z 1.71 m. The trunk must be extended and the arm raised; carrying the load high risks tipping the base. Approach close to the wall before raising the arm.
- The nail is tiny (about 19 x 19 x 29 mm after the 2.44 scale), so it is hard to see at range. Localise it from the wall first, then servo the alarm onto it.
- Contact with the nail is required (any substep since the last step). Pushing the disc flat against the wall slightly beside the nail will not attach.
- No legal scripted shortcut: attach needs real contact and alignment.

### Hints for the VLM

- The coffee table is the large low table (0.8 x 1.66 m, top ~0.4 m) in `living_room_0`; the alarm is a white round disc, the only small object on it.
- The nail is in `kitchen_0`, on a wall at about 1.7 m, alone on bare wall. It is a small dark peg; look for it at head height, not near the floor.
- Done looks like: the white disc flat against the wall at head height, not in the gripper and not falling. If it drops after release, it did not attach.
