# 39 · Spraying Fruit Trees

Task name `spraying_fruit_trees`, task index 39.

> In the garden, pick up the pesticide atomizer on the floor and spray pesticide onto both trees until each tree trunk is fully covered.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 278.2 s mean (8345 steps) |
| episode time limit | 417.3 s (12518 steps at 30 Hz) |
| human base travel | 23.4965 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060748 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(covered tree.n.01_1 pesticide.n.01_1)` | no | yes |
| `(covered tree.n.01_2 pesticide.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (covered ?tree.n.01_1 ?pesticide.n.01_1)
            (covered ?tree.n.01_2 ?pesticide.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `pesticide.n.01_1` | particle system | pesticide | - | - | - | - |
| `pesticide__atomizer.n.01_1` | pesticide_atomizer_172 | pesticide_atomizer / eisckl | garden_0 | floor, z 0.08 | 3.47 m (range 0.55-10.39) | yes, spread 10.38 m |
| `tree.n.01_1` | tree_dyymaq_1 | tree / dyymaq | garden_0 | very high (>1.6 m), z 3.72 | 11.13 m (range 8.03-12.3) | no (fixed) |
| `tree.n.01_2` | tree_dyymaq_2 | tree / dyymaq | garden_0 | very high (>1.6 m), z 3.72 | 11.33 m (range 7.96-12.8) | no (fixed) |
| `floor.n.01_1` | floors_ghetev_0 | floors / ghetev | garden_0 | floor, z -0.08 | 3.11 m (range 0.3-4.08) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 garden)
(inroom tree.n.01_1 garden)
(inroom tree.n.01_2 garden)
(insource pesticide__atomizer.n.01_1 pesticide.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop pesticide__atomizer.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 pesticide__atomizer.n.01_1)
(touching pesticide__atomizer.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 272.17 s (range 214.87-428.97). Skills per demo 10.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x3, spray x2, turn off switch x2, turn on switch x2, pick up from x1.

Representative demo `episode_00392680.json` (272.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the pesticide atomizer` (1.3-41.4 s)
2. `pick up the pesticide atomizer from the floors` (41.4-57.4 s)
3. `move to the tree` (57.4-92.6 s)
4. `turn on the pesticide atomizer` (92.6-100.7 s)
5. `spray the pesticide atomizer with the tree` (100.7-154.4 s)
6. `turn off the pesticide atomizer` (154.4-160.6 s)
7. `move to the tree` (160.6-210.2 s)
8. `turn on the pesticide atomizer` (210.2-218.3 s)
9. `spray the pesticide atomizer with the tree` (218.3-267.1 s)
10. `turn off the pesticide atomizer` (267.1-273.6 s)

Mean duration per skill in this task: move to 36.9 s, pick up from 18.2 s, spray 59.2 s, turn off switch 5.9 s, turn on switch 7.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `spray the pesticide atomizer with the tree` | 399 |
| `turn off the pesticide atomizer` | 399 |
| `turn on the pesticide atomizer` | 394 |
| `move to the tree` | 375 |
| `move to the pesticide atomizer` | 223 |
| `pick up the pesticide atomizer from the floors` | 197 |
| `turn on the tree` | 6 |
| `pick up the pesticide atomizer from the lawn` | 2 |
| `move to the floors` | 2 |
| `spray the pesticide atomizer with the pesticide atomizer` | 1 |
| `pick up the pesticide atomizer from the tree` | 1 |
| `turn off the tree` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/39_spraying_fruit_trees.json`. Planner notes: `task_docs/notes/39_spraying_fruit_trees.md`.
