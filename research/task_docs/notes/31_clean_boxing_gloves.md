## Planner notes

**Tier:** D — two pick-and-place moves into the washer, then a washer cycle (a state transition) clears the dust.

### Goal in plain words

Both boxing gloves must end with zero dust particles on them.
The only practical route is the washer: put both gloves in, close the door, turn the washer on.
The glove itself is a particle remover, but its dust condition is `never` (PREDICATES.md §12), so rubbing gloves together does nothing.
Where the gloves end up does not matter; nothing else is scored.

### Q traps

- Two literals, both false at reset (verified: the template `system_registry` has 40 dust particles, 20 on each glove, in all 20 public instances). Max Q is 1.0.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`WasherDryerRule`, `transition_rules.py:745-757`). Pressing while the door is open does nothing lasting; ToggledOn is forced False while open (§11).
- Cleaning needs two things at that step (`WasherRule.transition`, `transition_rules.py:846-884`):
  - the washer's volume holds at least 1 dust particle (these particles sit on the gloves, so at least one glove must be well inside);
  - each glove has **any** collision point inside the washer volume. A glove only partly in still gets cleaned.
- Washer starts closed and off in all 20 instances (joint_pos ~0, `ToggledOn: False`). The door has to be opened first.
- A glove sticking out of the doorway stops the door closing within 5 % (§6). Then the washer stays off and nothing is cleaned.
- Fallback that keeps Q: washing one glove at a time works. Open the door (this forces the washer off), add glove 2, close, press again: the change condition fires again. One cleaned glove = Q 0.5.
- Success is checked every step, so the episode ends with Q 1.0 on the press step itself.

### Minimal plan

1. `move to the washer` — washer front fills the view; base stopped. ~19 s.
2. `open the door of the washer` — door visibly swung open, drum opening visible. ~46 s (slowest step).
3. `move to the boxing gloves` — gloves on the countertop in view at close range. ~19 s.
4. `pick up the boxing gloves from the countertop` — one gripper closed but stopped short of fully closed; glove gone from the counter. ~21 s.
5. `pick up the boxing gloves from the countertop` — second hand holds the second glove. ~21 s.
6. `move to the washer` — ~19 s.
7. `place the boxing gloves in the washer` — glove no longer in the gripper, not visible outside the drum. ~28 s.
8. `place the boxing gloves in the washer` — same for the second glove. ~28 s.
9. `close the door of the washer` — door flush with the washer front. ~28 s.
10. `turn on the washer` — fingertip on the control; episode ends on success. ~21 s.

Total about 250 s against a 411.8 s limit. The demo is already minimal apart from `turn to the boxing gloves` (164 of 200 demos), which can be dropped if the gloves are already in view.

### What the demos do differently

- Most demos open the washer first, then fetch both gloves in one trip (one per hand), as above. Keep that order: the hands are free for the door.
- `turn to the boxing gloves` appears in 164 demos; it is only re-aiming the head/base.
- Rare demos pick a glove back out of the washer (3) or put one on the countertop (2); these are recoveries.

### Hard parts and hacks

- Opening the washer door is the slowest demo step (46 s mean) and needs the door handle. Handle width vs the 44 mm span is unverified.
- Glove size is unknown (no custom list). Every demo picks the gloves up with the same robot, so some part registers a grasp; which part is unverified.
- The gloves sit on countertop `sjxber` (x≈23.7, y≈-2.06), about 3 m from the washer (x≈22.0, y≈0.33). Carry both at once to save a trip.
- The toggle-button location on washer `ynwamu` is unverified. A press must hold finger contact on the button sphere for 5 steps (§11).
- No scripted shortcut beyond a press routine: the planner has no object poses. A scripted "hold fingertip on button for ~0.5 s then withdraw" is legal once the arm is at the button.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. The washer and a clothes dryer stand side by side on one wall (washer at y≈0.33, dryer at y≈0.95, 0.6 m apart). Do not load the dryer: it has no cleaning rule for dust.
- The gloves are on the countertop over the cabinet at the far end of the room (countertop `sjxber`, above cabinet `gjrero_4`), not on the long counter opposite the washer.
- Dust is drawn as small visual specks on the gloves. After the press the specks vanish; that is the done signal.
- "Door closed" = washer door flush, no gap at the hinge side.
