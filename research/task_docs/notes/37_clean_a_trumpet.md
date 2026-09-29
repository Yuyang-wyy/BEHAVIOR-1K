## Planner notes

**Tier:** D — one tool grasp (scrub brush), then removing every dust particle from a curved object on a low desk. The literal is all-or-nothing.

### Goal in plain words

The trumpet (`cornet.n.01_1`, scene object `trumpet_87`) on the bedroom_0 desk must carry zero dust particles at the end. The scrub brush removes dust with no condition (`scrub_brush.n.01`: dust = always, PREDICATES §12). No water, soap or sink is needed. Where the brush and trumpet end up does not matter.

### Q traps

- One literal, so Q is 0 or 1. Cleaning most of the trumpet earns nothing.
- Dust count per instance, from the tro_state files: 20 particles, 19 in instances 302 and 311. All are in one group on `trumpet_87`.
- Removal needs each particle inside the brush's remover-link visual AABB grown by 2 cm (§12). The brush has to pass over every part of the trumpet: bell, valves and tubing.
- The removal box is axis-aligned in world frame. A tilted brush has a bigger box than it looks, but a brush held above the trumpet misses the lower sides.
- Success ends the episode the step the last particle goes, so do not stop wiping to place the brush.
- All three closed-loop runs on 311 scored Q 0.00.

### Minimal plan

1. `move to the scrub brush` — brush on the desk in view. ~12 s.
2. `pick up the scrub brush from the desk` — brush lifted, gripper closed short of full. ~33 s.
3. `hand over the scrub brush with the left` — brush now in the left gripper (all 200 demos do this). ~17 s. Skip it if the brush is already in the hand facing the trumpet.
4. `move to the trumpet` — trumpet centred in front, within arm reach. ~12 s.
5. `wipe the scrub brush` — brush in contact with the trumpet, moving over all of it. ~71 s. Repeat while any dust is visible; send it again rather than a new prompt.
6. Skip `place the scrub brush on the desk`; the goal does not need it.

Budget: ~160 s demo mean vs a 265 s limit. The single `wipe` segment averages 71 s; allow up to ~150 s of wiping.

### What the demos do differently

- 95 % of demos use the same 6-step order above. Every demo has exactly one `wipe the scrub brush` segment and one hand-over to the left.
- 9-10 demos pick up and re-place the trumpet (`pick up the trumpet from the desk`, `place the trumpet on the desk`), probably to reach its far side. Not required, but a fallback if one side stays dusty.
- All end with `place the scrub brush on the desk`. Not needed.

### Hard parts and hacks

- Coverage on a curved, open object. The VLA tends to scrub one spot. The planner should check the trumpet from more than one view and re-issue `wipe` aimed at the dusty region.
- Particles near the desk surface may be hard to reach with the brush above the trumpet (unverified). Rolling or lifting the trumpet (as a few demos did) exposes them.
- Pushing too hard shoves the trumpet across or off the desk; it is not fixed.
- Removal does not need a grasp (ADJACENCY method, §12): only the brush box must pass over the particles. Grasp is still the only practical way to move the brush.
- Brush and trumpet widths are unknown (no custom list). The humans grasped the brush in every demo.

### Hints for the VLM

- bedroom_0 has one desk (low, root z ~0.44 m), one trumpet (z ~0.84) and one scrub brush (z ~0.79), both on the desk. No same-category distractors in the room.
- Dust is drawn as small visual specks on the trumpet (colour unverified). Done is: no specks visible from either side.
