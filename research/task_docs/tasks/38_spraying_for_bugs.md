# 38 · Spraying For Bugs

Task name `spraying_for_bugs`, task index 38.

> Pick up the pesticide atomizer in the garden and spray insectifuge to fully cover both potted plants in the garden.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 216.0 s mean (6479 steps) |
| episode time limit | 324.0 s (9719 steps at 30 Hz) |
| human base travel | 21.9792 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.50; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060681 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(covered pot_plant.n.01_1 insectifuge.n.01_1)` | no | yes |
| `(covered pot_plant.n.01_2 insectifuge.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (forall
            (?pot_plant.n.01 - pot_plant.n.01)
            (and
                (covered ?pot_plant.n.01 ?insectifuge.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `insectifuge__atomizer.n.01_1` | insectifuge_atomizer_174 | insectifuge_atomizer / qnroki | garden_0 | floor, z 0.08 | 4.12 m (range 1.01-8.32) | yes, spread 10.05 m |
| `insectifuge.n.01_1` | particle system | insectifuge | - | - | - | - |
| `floor.n.01_1` | floors_ghetev_0 | floors / ghetev | garden_0 | floor, z -0.08 | 1.84 m (range 0.29-4.29) | no (fixed) |
| `pot_plant.n.01_1` | pot_plant_173 | pot_plant / arwvvc | garden_0 | floor, z 0.18 | 3.98 m (range 1.01-8.66) | yes, spread 12.54 m |
| `pot_plant.n.01_2` | pot_plant_172 | pot_plant / arwvvc | garden_0 | floor, z 0.18 | 3.88 m (range 1.07-6.4) | yes, spread 9.7 m |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 garden)
(insource insectifuge__atomizer.n.01_1 insectifuge.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop insectifuge__atomizer.n.01_1 floor.n.01_1)
(ontop pot_plant.n.01_1 floor.n.01_1)
(ontop pot_plant.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 insectifuge__atomizer.n.01_1)
(touching floor.n.01_1 pot_plant.n.01_1)
(touching floor.n.01_1 pot_plant.n.01_2)
(touching insectifuge__atomizer.n.01_1 floor.n.01_1)
(touching pot_plant.n.01_1 floor.n.01_1)
(touching pot_plant.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 206.6 s (range 136.8-385.5). Skills per demo 10.0 (range 9-18). 7 distinct skill orders; the most common one covers 97% of demos.

Most common skill counts per demo (98% of demos): move to x3, spray x2, turn off switch x2, turn on switch x2, pick up from x1.

Representative demo `episode_00382700.json` (206.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the insectifuge atomizer` (2.0-6.0 s)
2. `pick up the insectifuge atomizer from the floors` (6.0-22.0 s)
3. `move to the pot plant` (22.0-28.1 s)
4. `turn on the insectifuge atomizer` (28.1-36.1 s)
5. `spray the insectifuge atomizer with the pot plant` (36.2-93.0 s)
6. `turn off the insectifuge atomizer` (93.1-100.9 s)
7. `move to the pot plant` (100.9-125.8 s)
8. `turn on the insectifuge atomizer` (125.8-131.3 s)
9. `spray the insectifuge atomizer with the pot plant` (131.3-202.3 s)
10. `turn off the insectifuge atomizer` (202.3-208.6 s)

Mean duration per skill in this task: move to 23.9 s, pick up from 18.2 s, push to 7.2 s, spray 45.3 s, turn off switch 7.3 s, turn on switch 7.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `spray the insectifuge atomizer with the pot plant` | 401 |
| `turn off the insectifuge atomizer` | 400 |
| `move to the pot plant` | 397 |
| `turn on the insectifuge atomizer` | 397 |
| `move to the insectifuge atomizer` | 200 |
| `pick up the insectifuge atomizer from the floors` | 200 |
| `push the garden chair to the away robot` | 8 |
| `move to the garden chair` | 7 |
| `turn on the pot plant` | 3 |
| `move to the floors` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/38_spraying_for_bugs.json`. Planner notes: `task_docs/notes/38_spraying_for_bugs.md`.
