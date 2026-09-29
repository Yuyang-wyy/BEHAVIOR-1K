## Planner notes

**Tier:** C — one floor pick plus an `attached` alignment on the tripod head within 5 cm and 15°, including yaw. Single literal, so the score is 0 or 1.

### Goal in plain words

The digital camera must be attached to the camera tripod in bedroom_0. There is one camera and one tripod. Nothing else is checked, and the tripod may stand anywhere.

### Q traps

- One literal: Q is 0 or 1.
- Attachment is automatic while the camera touches the tripod and the camera's `cameratripodM` link is within 5 cm and 15° of the tripod's `cameratripodF` link (PREDICATES §10). No release needed; success ends the episode.
- Meta links verified in asset metadata: tripod `hnpofr` has `cameratripodF` at its top (local z +0.48 above the root, identity orientation). Camera `zcnxuz` has `cameratripodM` near its base, rotated ~90° about z in the camera frame. So the camera must sit upright on the head **and** at one specific yaw relative to the tripod; a camera rotated 90° or 180° on the head does not latch (derived from the link orientations).
- The tripod root is at z 0.8 m and upright (roll and pitch ~0) in all 20 instances, with random yaw. The mount point is therefore at about 1.28 m (derived).
- Knocking the tripod over moves its mount; re-standing it costs a pick and place.
- The camera also has a `togglebutton`; pressing it is harmless for this goal.
- All three closed-loop runs on 311 scored 0.

### Minimal plan

1. `move to the digital camera` — camera on the floor in view. ~19 s.
2. `pick up the digital camera from the floors` — camera lifted off the floor. ~35 s (the slowest step: floor-level grasp).
3. `move to the camera tripod` — tripod head at chest height, centred. ~19 s.
4. `hold the camera tripod` — second gripper closed on a tripod leg or shaft. ~14 s.
5. `attach the digital camera to the camera tripod` — camera sitting on the tripod head; done when it stays there after the camera gripper opens. ~14 s.
6. `release the camera tripod` — only if the episode has not already ended. ~9 s.

Budget: 196 s limit vs 130 s demo mean. Room for one retry of step 5.

### What the demos do differently

- 167 of 200 demos follow exactly the plan above.
- 30 demos also pick up and re-place the tripod (`pick up the camera tripod from the floors`, `place the camera tripod on the floors`), apparently to bring it closer. Not needed unless the tripod stands against furniture.
- Humans always brace the tripod with the second arm before attaching.

### Hard parts and hacks

- Floor pick of a small camera: the trunk must bend low (35 s mean even for humans).
- The yaw constraint: the camera must face the tripod's own "forward". The tripod's yaw varies across instances and is hard to read from RGB. The VLA must learn it from the demo appearance of a mounted camera.
- Pushing the camera down on the head can tip the tripod; holding it is the demo remedy.
- Camera and tripod widths vs the 44 mm span are unknown (no custom list). The demos grasped both.
- Scripted shortcut (unverified): once the camera rests on the head, a slow wrist yaw sweep over ±180° while keeping contact passes through the 15° window and latches the moment it aligns.

### Hints for the VLM

- Everything is in bedroom_0: one camera on the floor, one tripod standing on the floor, 0.6-2.7 m from the start. No distractors of either category.
- The tripod head (mount) is at about 1.3 m, the top of the tripod.
- Done: the camera sits on top of the tripod and stays there with both grippers open.
