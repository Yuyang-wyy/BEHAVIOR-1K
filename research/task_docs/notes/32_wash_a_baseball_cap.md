## Planner notes

**Tier:** D — two pick-and-place moves into the washer, then a washer cycle (a state transition) clears the dirt.

### Goal in plain words

Both baseball caps must end with zero dirt particles on them.
The route is the washer: put both caps in, close the door, turn it on.
Where the caps end up does not matter; nothing else is scored.

### Q traps

- Two literals, both false at reset (verified: 40 dirt particles, 20 per cap, in all 20 public instances). Max Q is 1.0.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`transition_rules.py:745-757`). A press with the door open does nothing lasting (§11).
- At that step (`WasherRule.transition`, `transition_rules.py:846-884`):
  - the washer volume must hold at least 1 dirt particle (the particles are on the caps, so at least one cap must be well inside);
  - each cap with **any** collision point inside the washer volume is cleaned, even if partly out.
- Washer starts closed and off in all 20 instances (joint_pos ~0, `ToggledOn: False`).
- A cap brim caught in the doorway keeps the door more than 5 % open (§6), so the washer never turns on.
- Fallback: wash one cap per cycle. Opening the door forces the washer off; closing and pressing again fires a new cycle. One clean cap = Q 0.5.
- Success ends the episode on the press step.

### Minimal plan

1. `move to the washer` — washer front in view; base stopped. ~18 s.
2. `open the door of the washer` — door swung open, drum visible. ~47 s.
3. `move to the baseball cap` — cap on the long countertop in view. ~18 s.
4. `turn to the baseball cap` — optional; only if the cap is off-centre. ~23 s.
5. `pick up the baseball cap from the countertop` — gripper closed short of fully closed; cap gone from the counter. ~15 s.
6. `move to the baseball cap` — only if the second cap is out of reach (caps can be up to ~2 m apart). ~18 s.
7. `pick up the baseball cap from the countertop` — second hand holds the second cap. ~15 s.
8. `move to the washer` — ~18 s.
9. `place the baseball cap in the washer` — cap released, not visible outside the drum. ~28 s.
10. `place the baseball cap in the washer` — second cap. ~28 s.
11. `close the door of the washer` — door flush. ~24 s.
12. `turn on the washer` — fingertip on the control; episode ends on success. ~25 s.

About 260-280 s against a 417.5 s limit. This matches the representative demo; drop steps 4 and 6 when not needed.

### What the demos do differently

- All demos open the washer before picking up the caps, and carry both caps in one trip (one per hand).
- `turn to the baseball cap` in 211 segments and a second `move to the baseball cap` in many demos: the caps are often far apart.
- Two demos pick a cap back out of the washer (recovery).

### Hard parts and hacks

- Caps start anywhere along countertop `ikwqer`, a ~4 m counter on the wall opposite the washer (cap y from -2.14 to 2.03 across instances; washer at x≈22.0, counter at x≈24.5). The page's "spread 4.1 m" is this, not a different surface.
- Cap size is unknown (no custom list). Demos grasp them, so some part (probably the brim) registers; unverified.
- Opening the washer door is the slowest step (47 s mean). Handle width vs 44 mm is unverified.
- Button location on washer `ynwamu` is unverified. The press needs 5 steps of finger contact on the button sphere (§11).
- A scripted press routine (hold fingertip ~0.5 s, withdraw) is legal once the hand is at the button.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. Washer and clothes dryer stand side by side (washer y≈0.33, dryer y≈0.95). Use the washer; the dryer does not clean.
- The target counter is the long one over the row of four identical cabinets opposite the washer. The two caps may be at opposite ends of it.
- Dirt shows as brown specks on the caps. They vanish on the press step; that is the done signal.
- "Door closed" = washer door flush with the front.
