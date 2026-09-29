## Planner notes

**Tier:** C — a floor pick of a door panel plus an `attached` alignment (5 cm, 15°) on a free-standing cabinet base that the demos first tip over. Single literal, so Q is 0 or 1.

### Goal in plain words

The cabinet door must be attached to the cabinet base. There is exactly one of each, both standing upright on the living-room floor. Nothing else is checked: where the base ends up, and whether it lies on its back, do not matter.

### Q traps

- One literal: Q is 0 or 1. Success ends the episode at once, with no release needed (PREDICATES §10).
- Attachment fires automatically while the door touches the base and the door's `doorcabinetM` link is within 5 cm and 15° of the base's `doorcabinetF` link.
- Meta links verified in asset metadata (both scale 1.0 in the template):
  - base `dcmhhh` (0.253 x 0.264 x 0.457 m): `doorcabinetF` at local (+0.149, +0.128, 0), identity orientation. That is just outside the +x face (half-depth 0.126), at the +y edge, mid-height.
  - door `ertkre` (0.024 x 0.263 x 0.457 m): `doorcabinetM` at local (-0.005, -0.129, 0), rotated 180° about x.
- Derived from those links: the door must lie flush over the base's +x face, covering it edge to edge (the door face 0.263 x 0.457 matches the base face 0.264 x 0.457). Its local "up" must point opposite to the base's "up". With both objects upright, as at reset, that means standing the door on its other end. After tipping the base onto its back, any in-plane rotation is a yaw of the flat door, which is why the demos tip first (derived).
- Tipping the base onto its front or side buries or tilts the +x face. Only "on its back, +x face up" leaves a horizontal mounting face (derived).
- Both objects start upright (tilt 0°) in all 20 instances, 0.3-3.8 m apart.

### Minimal plan

1. `move to the cabinet door` — the door panel fills the view. ~16 s.
2. `pick up the cabinet door from the floors` — gripper closed across the 24 mm edge, door off the floor. ~17 s.
3. `move to the cabinet base` — base in front of the robot. ~16 s.
4. `tip over the cabinet base` — base lying on its back, open face up. ~14 s.
5. `place the cabinet door on the cabinet base` — door lying flat on the base, edges aligned. ~30 s.
6. `attach the cabinet door to the cabinet base` — done when the episode ends (success). If not, nudge the door so its edges line up with the base within a few cm. ~14 s.

Budget: 172 s limit vs 115 s demo mean. Little room for retries. Doing step 4 with the door already in one hand follows the demo order; tipping first with both hands free is an untested alternative.

### What the demos do differently

- 60% of demos follow the plan above exactly.
- 24 demos add `turn to the cabinet door` and 14 add `turn to the cabinet base` (reorientation).
- 49 extra `move to the cabinet base` over 200 demos: some humans re-approach after tipping.

### Hard parts and hacks

- The door is 24 mm thick, so the jaws fit across it (asset bbox). It stands on edge on the floor, so the grasp is low on the top edge.
- The base (0.25 x 0.26 x 0.46 m) is too wide to grasp; tipping is a push.
- The alignment is the hard step: 5 cm on the link position and 15° on the full orientation. A door placed rotated by 180° in plane (hinge edge on the wrong side) never latches (derived from the link orientations).
- Scripted shortcut (unverified): with the door resting flat on the base, a slow in-plane wrist rotation sweep plus small translations while in contact passes through the window. Attachment is checked every step.

### Hints for the VLM

- Both objects are in living_room_0 of Rs_int, on the floor, 0.7-3.3 m from the start. No distractors of either category.
- The base is a small open box about knee height (0.46 m); the door is a flat panel of the same height standing on edge.
- Done: the door lies flush on the tipped base, covering its open face, and the episode ends.
