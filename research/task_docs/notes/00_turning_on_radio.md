## Planner notes

**Tier:** A. The goal is a single `toggled_on`; a fingertip press on the radio's control is enough, no grasp needed.

### Goal in plain words

The one radio (`radio_89`, asset `radio/wxnicr`) on the living-room coffee table must end toggled on.
Nothing else is checked: the radio may stay on the table, be moved, or end anywhere.
There is only one radio and one coffee table in the living room, so there is no object choice.
The episode ends with Q = 1.0 on the first step the radio is on.

### Q traps

- One literal, false at reset in all 20 public instances (`ToggledOn.value = False` in every `-tro_state.json`). Q is 0 or 1; there is no partial credit.
- The toggle fires only when a robot finger link touches the radio **and** overlaps an ~11 mm sphere at the `togglebutton` meta link for exactly 5 consecutive steps (PREDICATES.md §11). Touching the body elsewhere does nothing.
- A second separate 5-step touch would flip it back, but success ends the episode on the first flip, so this cannot bite in practice.
- Knocking the radio over is the real trap. The body is only ~0.138 m deep; a push aimed past the cap surface toppled it on instance 315 (`radio_generalization_20260920/RESULTS.md`). On its side the control face points somewhere unexpected.

### Minimal plan

Option A (recommended, press in place; shorter than the demo):
1. `move to the radio` — done when the radio fills a large part of the head image and the base has stopped. ~18 s.
2. `press the radio` — done when the episode terminates (success ends it). ~10 s per attempt; retry once or twice, then reposition.

Option B (the demo order, in distribution for Comet):
1. `move to the radio` — as above. ~18 s.
2. `pick up the radio from the coffee table` — done when the radio is off the table and a gripper is stopped short of fully closed. ~25 s.
3. `press the radio` — done when the episode terminates. ~10 s.
4. `place the radio on the coffee table` is never needed: the episode already ended at step 3.

- Scripted alternative: `code: press_marker_policy.py` (`BEHAVIOR-1K/scripts/aspire_radio/`). It presses the control in place from RGB-D + proprioception only and scored 7/20 on public 301-320 (4/10 on the leaderboard ids 301-310). Its successes took 323-3000 steps, all under the 3224-step limit.
- Time limit: 107.5 s (3224 steps). Option B at demo pace (~53 s) fits; Option A leaves room for 3-4 press retries.

### What the demos do differently

- All 200 demos do move to, pick up, press, place on, in that order (the one skill order, 100%).
- Picking the radio up is unnecessary. So is putting it back: the evaluator ends the episode at the press.
- The demo press is annotated `coordinated`: one hand holds the radio while the other presses. Comet has therefore mostly seen `press the radio` with the radio held in the air, not resting on the table. Pressing on the table is out of distribution (unverified how much that hurts).
- Comet closed-loop on instance 311: Q = 0.00 for every checkpoint tried (zs_pt50, ft10k, ft24k, ft40k).

### Hard parts and hacks

- Hardest step: hitting an ~11 mm sphere with a fingertip while in contact with the radio. Centimetre-scale aim error decides success.
- Grasping is the dominant failure of grasp-first pipelines ("No visually verified radio grasp"). Whether any part of the radio fits the 44 mm jaw span is unverified; prefer Option A.
- The radio yaw is random across instances (full circle, -166° to +166°), so the control face often points away from the robot. Orbit the coffee table to the face that shows the control before pressing.
- In 7/20 public instances the radio starts more than 90° off the robot's initial heading (305, 306, 311, 313, 316, 318, 319). A rotate-in-place scan is needed before the first `move to`.
- In the scripted runs, the largest failure was never sighting the control face (9 of 20 in the v10 arm), not the press itself. Search and viewpoint matter more than press accuracy.
- Push along the face normal and stop at the cap surface. Driving 12-42 mm past it tipped the radio over.
- Rotation odometry drifts; re-ground the radio visually after every drive instead of trusting a pose from an earlier scan.

### Hints for the VLM

- Scene `house_double_floor_lower`, living room. The robot starts 0.75-2.25 m from the radio.
- The radio is a small red box on the low coffee table (radio root z 0.53 m, table root z 0.36 m; table top height not measured). It is the only radio and the only coffee table in the living room. Other living-room objects: sofa, shelf, wall-mounted TV, fireplace, bottom cabinet, pictures.
- The control is a small raised red cap in the centre of the dark speaker face, ~10 cm above the table. It looks 8-14 mm across in RGB at 0.36-1.4 m.
- If no dark speaker face with a red cap is visible, you are looking at the back or a side: move around the table.
- The cap turns from red to green when the radio is on. You will rarely see it, because the episode ends on success.
- "Done" for step 2 is episode termination, not anything seen in the image.
