## Planner notes

**Tier:** D — one particle-application transition (`covered` by spray). The only grasp is the atomizer, which is 41 x 40 x 151 mm and fits the jaws.

### Goal in plain words

Each of the two target trees (`tree_dyymaq_1`, `tree_dyymaq_2`) must carry at least one pesticide particle. Nothing else is checked. The atomizer can stay on at the end, and it can be dropped anywhere. Which part of the tree gets hit (trunk or canopy) does not matter.

### Q traps

- Both literals start false, so max partial Q is 1.0 (page is right). Each tree is worth 0.5.
- `covered` for a visual system needs only **1 particle** on the tree (PREDICATES §12, `covered.py` `VISUAL_PARTICLE_THRESHOLD` = 1). Once one particle lands, the literal is done. Longer spraying earns nothing more.
- The atomizer applies only while `toggled_on` (KB: `particleApplier` condition `pesticide: toggled_on True`). A 5-step fingertip press flips it (§11). A second press flips it back off, so do not press it twice in a row.
- Three trees share model `dyymaq`. `tree_dyymaq_0` at (-10.1, 13.2) is a distractor. Spraying it scores nothing.
- The atomizer starts off (`ToggledOn` false in the template).

### Minimal plan

1. `move to the pesticide atomizer` — atomizer (small bottle with a nozzle) centred at the bottom of the view, base stopped. ~37 s (its distance from the start varies from 0.6 to 10.4 m).
2. `pick up the pesticide atomizer from the floors` — gripper closed but not fully shut, bottle off the ground. ~18 s.
3. `move to the tree` (first target) — trunk fills the centre of the view, 1-2 m away. ~37 s.
4. `turn on the pesticide atomizer` — no reliable image cue. Treat it as done after ~7 s. The next step shows whether it worked.
5. `spray the pesticide atomizer with the tree` — nozzle pointed at the trunk from close range. ~20-60 s. The demos take 59 s, but one landed particle is enough (unverified whether particles are visible in RGB).
6. Skip `turn off the pesticide atomizer`. The goal does not need it, and a stray press between trees would turn it off.
7. `move to the tree` (second target) — as in step 3. ~37 s.
8. `spray the pesticide atomizer with the tree` — as in step 5.

The plan takes about 230 s against a 417 s limit. The episode ends on success as soon as the second tree has a particle.

### What the demos do differently

- All 200 demos use the same 10-skill order: turn on, spray, and turn off for each tree. The two extra turn-off/turn-on pairs cost about 26 s and add a double-press risk.
- A few demos say `turn on the tree` (6) or `turn off the tree` (1). These are annotation slips. Do not copy them.

### Hard parts and hacks

- **Distance.** The trees are 8-13 m from the start and 12.5 m from each other: `tree_dyymaq_1` at (25.9, 8.3) and `tree_dyymaq_2` at (15.9, 0.8) in every instance, since trees are fixed. Base travel is the main time cost (the humans drove 23.5 m).
- **Spray cone.** The cone size is an asset annotation and is not verified (PREDICATES §18). Rays are cast every 5 steps, and each hit object gets up to 2 particles (§12). Get close, within about 1 m, and aim at the trunk, which is the densest part in the view.
- **Toggle while holding.** Pressing the button needs a finger link on the atomizer's `togglebutton` sphere (§11). Whether the holding hand's fingers can reach it, or the free hand must press it, is not verified. If spraying shows no effect, press again, once.
- The trees are scaled to about 4.9 x 5.6 x 6.4 m. The trunk is well inside the reachable height, and any hit on the tree mesh counts.

### Hints for the VLM

- Garden of `house_double_floor_lower`. It is large and holds 26 trees and about 50 bushes.
- Target 1 is the eastern `dyymaq` tree near (25.9, 8.3). Target 2 is the `dyymaq` tree near (15.9, 0.8). Nearby distractors are `rrhqpw` trees at (25.0, -0.2), (27.6, 4.2) and (12.4, 7.4), and `wtyipq` trees at (26.9, 0.2), (22.2, -1.5) and (17.2, -3.3). The two targets look identical to each other.
- The atomizer lies on the ground (z 0.08), on the lawn or paving, at a different place in each instance.
- Done looks like a visible pesticide film on some part of each target tree. Without a reliable cue, spray each tree for about 10 s at close range.
