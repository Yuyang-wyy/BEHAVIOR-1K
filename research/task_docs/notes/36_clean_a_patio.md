## Planner notes

**Tier:** D — one grasp (the broom), then a particle-removal state change over a large area. The literal is all-or-nothing: every mud particle on the patio floor must go.

### Goal in plain words

The garden patio floor (`floors_ghetev_0`) must carry zero mud particles at the end. Mud is a visual particle system, so a single leftover particle keeps `covered` true (PREDICATES §12). The broom is the only tool in scope; it removes mud with no condition (`broom.n.01`: mud = always). Where the broom ends up does not matter.

### Q traps

- One literal, so Q is 0 or 1. Partial sweeping earns nothing.
- Mud count per instance, from the tro_state files: 9 to 17 particles (instance 311: 13; 301-310: 9-17).
- The particles are spread widely. Their stored positions (relative to the floor object's origin; frame assumed, unverified) span about 7 m in x and 10 m in y. The robot must walk to each patch.
- Removal needs each particle inside the broom's remover-link visual AABB grown by 2 cm (§12). The broom head must pass directly over each speck, not just near it.
- The broom saturates after 200 removed particles per system (§12). With at most 17 mud particles this is never reached.
- Success ends the episode on the step the last particle vanishes, so there is no need to put the broom down.
- All three closed-loop runs on 311 scored Q 0.00.

### Minimal plan

1. `move to the broom` — broom lying on the garden floor in view. ~11 s.
2. `pick up the broom from the floors` — broom lifted, gripper closed short of full. ~29 s.
3. `hold the broom` — demo-only stabilising segment (447 uses); send it if the grip looks loose. ~8 s.
4. Loop until no brown mud patch is visible on the patio:
   - `move to the mud` — nearest remaining patch centred in front of the base. ~11 s.
   - `sweep the broom` — broom head dragged across the patch on the ground. ~3 s.
   - Done-check: the patch is gone in RGB. If not, repeat `sweep the broom` at the same spot before moving on.
5. Skip `release the broom` and `place the broom on the floors`; the goal does not need them.

Budget: ~390 s demo mean vs a 604 s limit. Demos use 15-20 sweeps (101 of 200 use exactly 20). Plan for ~20 move-sweep cycles at ~15 s each, plus ~50 s for the pick.

### What the demos do differently

- Many demos first `push the garden chair to the away robot` (474 uses, ~2 per demo) to clear the sweeping path. Do it only if a chair blocks a mud patch.
- Humans end with `release the broom` and `place the broom on the floors` (200). Not needed.
- 167 distinct orders: the order of patches is free.
- `hand over the broom with the left/right` appears 9 times; not needed.

### Hard parts and hacks

- Coverage bookkeeping is the whole task. The VLA sweeps where it is told; the planner must track which patches remain. One missed speck gives Q 0.
- Mud specks are small visual particles on a large outdoor floor. They are hard to see from far away; revisit the area after each sweep from a closer, lower view.
- The broom is long. Carrying it while driving can hit garden furniture or tip the robot (see the robot facts in the brief).
- Removal volume is the broom's axis-aligned world AABB (+2 cm). A broom held at an angle has a box larger than its head, which helps; a broom held high misses floor particles entirely. Keep the head on the ground during `sweep the broom`.
- Scripted shortcut: a coverage sweep in straight lanes over the patio while dragging the broom head on the ground. Legal (RGB-D and proprioception only), but the patio is ~7 × 10 m, so lanes must be well planned to fit the time limit.

### Hints for the VLM

- Garden only (garden_0). Distractors: 4 garden chairs, a charcoal grill, 55 bushes, 26 trees, garden lights, a car and a playground. There is exactly one broom.
- The broom starts on the floor; its distance from the robot varies from 0.8 to 8.5 m across instances.
- Mud is drawn as small visual specks on the patio floor (colour unverified). Done is: no specks left anywhere on the patio.
