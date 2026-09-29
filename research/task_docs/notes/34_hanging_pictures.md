## Planner notes

**Tier:** C — one pick plus an `attached` alignment: the poster's top mount must reach the wall nail at ~1.7 m within 5 cm and 15° while touching it. Single literal, so the score is 0 or 1.

### Goal in plain words

The poster must end up attached to a wall nail. The kitchen has exactly one wall nail (`wall_nail_wlnail_1`), so the `exists` is not a real choice. Nothing else is checked; the poster only needs to latch once and stay attached.

### Q traps

- One literal: Q is 0 or 1. No partial credit for carrying the poster to the wall.
- Attachment is automatic (PREDICATES §10). Every step, if the poster is in contact with the nail and the poster's `displaywallM` link is within 5 cm and 15° of the nail's `displaywallF` link, a fixed joint forms. No release is needed, and success ends the episode on that step.
- Meta links verified in asset metadata: poster `dsrcyt` has one `displaywallM` near its top edge (local z +0.40 before scaling); nail `wlnail` has one `displaywallF` rotated ~90° about y in the nail frame. So the poster must hang flat against the wall, upright, top edge at the nail. A poster held face-up or sideways never latches.
- No other `displaywallF` object in the kitchen, so there is no wrong-parent risk here.
- The joint breaks above 5000 N; slamming the poster into the wall after latching could detach it (§10). Back off gently.
- All three closed-loop runs on 311 scored 0.

### Minimal plan

1. `move to the poster` — poster lying on the bar in view. ~13 s.
2. `pick up the poster from the bar` — poster lifted clear of the bar. ~17 s. If it lies flat and ungraspable, `push the poster to the to_the_edge_of bar` first (4 demos).
3. `hand over the poster with the left` — optional; 102 of 200 demos do it, 94 skip it. Use it only if the grasping hand cannot face the wall. ~16 s.
4. `move to the wall nail` — base stopped facing the wall with the nail centred and high in the head camera. ~13 s.
5. `hang the poster on the wall nail` — poster flat on the wall, top edge at the nail; done when the poster stays on the wall after the gripper opens. ~25 s.

Budget: 119 s limit vs 80 s demo mean. There is time for roughly one retry of step 5, not a second full attempt.

### What the demos do differently

- Only four orders exist; the demos are already minimal.
- About half hand the poster to the left arm before walking to the nail.
- A few push the poster to the bar edge before grasping.

### Hard parts and hacks

- The time limit is very tight (1.5x a short demo). Any failed grasp likely ends the episode at Q 0.
- The nail is very high (z ~1.71 m). The trunk must extend up and the arm reach forward; the poster must be rotated to vertical while doing so.
- The 15° orientation window around the nail's mount frame. A VLA can easily press the poster to the wall slightly tilted and never latch. The planner should watch for the poster staying on the wall after release, and if it drops, re-grasp and retry.
- Poster thickness vs the 44 mm span is unknown (no custom list); the demos grasped it every time with this robot.
- Scripted shortcut (unverified): once the poster touches the wall near the nail, small wrist roll/pitch sweeps can bring it inside 15° without further VLA calls.

### Hints for the VLM

- Everything is in kitchen_0. The poster lies on a bar (`bar_egwapq_0`, one of two bars in the kitchen) at about 1.1 m. The robot starts 0.9-7.3 m from it.
- The wall nail is fixed on a kitchen wall at ~1.7 m (appearance unverified); expect it to be small in the head camera. Look for bare wall above head height.
- Done: the poster hangs on the wall by itself with the gripper open and away.
