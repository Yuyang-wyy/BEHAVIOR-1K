## Planner notes

**Tier:** D — grasp one tool (the insectifuge atomizer), toggle it on, and aim it at two pot plants. One landed particle per plant is enough.

### Goal in plain words

Both pot plants in the garden must carry at least one insectifuge particle at the end. The plants are interchangeable only in the sense that both need it. Insectifuge is a visual system: `covered` is true with a single particle (PREDICATES §12). Whether the atomizer ends on or off, held or dropped, does not matter: there is no `toggled_on` literal.

### Q traps

- Two literals, both false at reset (0 insectifuge particles in all 20 instances). Each plant sprayed earns 0.5.
- The atomizer applies only while toggled on (`particleApplier` condition `toggled_on: True`). It starts off in the template.
- Toggling is a 5-step fingertip press on the button sphere (§11). A second press turns it off. Pressing twice by mistake leaves it off with no visible spray.
- Spray does not wear off: pot plants have a `particleRemover` ability, but its insectifuge condition falls back to `default_visual_conditions` = None, i.e. never. Covering is permanent (KB, `output_hierarchy_properties.json`).
- Plant-to-plant distance varies a lot: 0.7 to 10.7 m across instances (7.8 m on 311). Zero-shot on 311 scored 0.50, one plant.
- Spray cone size is unverified (§18). Spray from close range, nozzle pointed at the foliage.

### Minimal plan

1. `move to the insectifuge atomizer` — atomizer on the garden floor in view. ~24 s.
2. `pick up the insectifuge atomizer from the floors` — atomizer lifted, gripper closed short of full. ~18 s.
3. `move to the pot plant` — the nearer plant in front, within ~1 m. ~24 s.
4. `turn on the insectifuge atomizer` — spray visible at the nozzle (whether the spray renders is unverified). ~7 s.
5. `spray the insectifuge atomizer with the pot plant` — nozzle aimed at the plant; a few seconds of visible spray on it is enough. ~10-45 s.
6. `move to the pot plant` — the other plant. ~24 s. The atomizer can stay on while driving; the goal has no toggle literal.
7. `spray the insectifuge atomizer with the pot plant`. ~10-45 s. If no spray is visible, send `turn on the insectifuge atomizer` first.

Budget: ~210 s demo mean vs a 324 s limit. Skipping both `turn off` steps and the second `turn on` saves ~20 s.

### What the demos do differently

- 97 % of demos: pick, then for each plant `turn on`, `spray`, `turn off`. The turn-offs are not in the goal.
- Human spray segments average 45 s per plant. The applier casts rays every 5 steps and deposits up to 2 particles per hit (§12), so a short, well-aimed burst suffices.
- 8 demos push a garden chair out of the way first. Only needed if a chair blocks the approach.

### Hard parts and hacks

- Finding both plants in a large garden full of bushes and trees; the second plant can be ~10 m away.
- Pressing the atomizer's trigger while holding it: the button location is unverified. A grasp that already covers the button can flip it on during the pick (5-step rule), and a later `turn on` would then switch it off. Check for visible spray before sending `turn on`.
- Aim: the cone must hit the plant's own collision geometry, not the pot's surroundings. Stand close and point low at the plant.
- Tipping risk is low: the atomizer is carried near floor level.

### Hints for the VLM

- Garden only (garden_0). Exactly one insectifuge atomizer and two pot plants (same model `arwvvc`, root z ~0.18 m, on the floor). Distractors: 55 bushes and 26 trees, which are not pot plants; 4 garden chairs.
- A pot plant is a plant in a pot standing on the paving; bushes are planted in the ground and trees are tall.
- Done per plant: spray particles visible on its foliage after the burst.
