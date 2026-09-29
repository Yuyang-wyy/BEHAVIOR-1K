## Planner notes

**Tier:** A, borderline B. Both literals can be met without a grasp: press the scanner's button, and push the scanner (or the laptop) along the desk until they touch. The demos lift the scanner, but it is 0.31 x 0.218 x 0.06 m (asset bbox), with no dimension under 44 mm.

### Goal in plain words

- The scanner must be toggled on and must be `nextto` the laptop.
- Both start on the same desk (`desk_mdhelw_0`) in private_office_3, 0.52-2.27 m apart (centre to centre, over the 20 instances).
- The laptop stays closed (joint 0) and does not need to be opened or switched on.

### Q traps

- There are 2 literals and both score (0/2 true at reset). The scanner starts off (`ToggledOn` false in all instances).
- **Toggle parity.** Every separate 5-step finger contact on the button flips the scanner (PREDICATES §11). Brushing the button while pushing or placing afterwards turns it back off. Press it **last**, after the nextto is done. Success ends the episode at once, so nothing can undo it.
- **nextto gap (derived from §5 and the asset sizes).** L = mean(0.513, 0.486, 0.08) = 0.36 m, so the AABB gap must be ≤ ~0.06 m. "Somewhere near the laptop" is not enough. Leave them nearly touching, on the same desk.
- The laptop is only 0.02 m thick, and the scanner's horizontal rays leave from 3 cm above the desk. The literal can still pass through the laptop's own rays hitting the scanner, so keep both flat on the desk.

### Minimal plan

1. `move to the scanner`. Done when the scanner is centred on the desk in the head camera and the base has stopped. About 30 s.
2. `push the scanner to the desk`. This is the closest trained prompt; there is none for "push to the laptop". Done when the scanner's near edge is within ~5 cm of the laptop's edge. About 29 s. If Comet will not slide it the right way, use `code: push` along the desk top toward the laptop. Alternatively, move the laptop instead (light and 0.02 m thick; no trained prompt, the closest is `pick up the laptop from the desk`, seen once).
3. `move to the laptop`. Only if the robot has to re-position. About 30 s.
4. `turn on the scanner`. Done when the button marker turns green (the toggle marker is recoloured red to green, `toggle.py` `_set_value`). Withdraw the finger right after. About 11 s.

- Totals: about 70-100 s against a 212.9 s limit.

### What the demos do differently

- 57% of demos push the scanner, then pick it up, carry it to the laptop, turn it on while holding it, and place it. That is a lift of a 0.22 m-wide box, and the place after the press risks a second button contact.
- 48 of 200 demos skip the push. None open the laptop.

### Hard parts and hacks

- **Button target.** The togglebutton meta link sits at the end face of the scanner's long axis (local x = +0.158 m on a 0.31 m body, z = +0.005 m). The sphere is small (marker size 0.009 m, like the radio's ~11 mm). The fingertip must overlap it **and** touch the scanner for 5 steps.
- **Scripted press.** `code: press` in the style of the radio toggle policy may transfer, with the end-face button as the target (unverified on this asset).
- **Pushing** a 0.31 m box across a 2.78 m desk to within 5 cm needs closed-loop depth feedback. Stop at a small gap rather than shoving the laptop off the desk.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The room is private_office_3, with one desk, one laptop, one scanner and three swivel chairs. There are no same-category distractors in the room.
- The scanner is the flat 0.31 x 0.22 x 0.06 m box on the desk. The laptop is the thinner 0.20 x 0.27 m slab.
- Done: the two objects visibly abut on the desk top (depth gap under ~5 cm), and the scanner's button marker is green.
