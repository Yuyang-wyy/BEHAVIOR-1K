# 37 · Clean a Trumpet

Task name `clean_a_trumpet`, task index 37.

> In the bedroom, pick up the scrub brush from the desk and scrub the cornet (trumpet) on the desk until it's no longer covered in dust.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, bedroom_1, bedroom_2 |
| human demo length | 176.9 s mean (5307 steps) |
| episode time limit | 265.4 s (7960 steps at 30 Hz) |
| human base travel | 12.3853 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060606 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered cornet.n.01_1 dust.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (not 
                (covered ?cornet.n.01_1 ?dust.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `cornet.n.01_1` | trumpet_87 | trumpet / bafgow | bedroom_0 | table/counter (0.6-1.1 m), z 0.84 | 1.72 m (range 1.08-2.47) | yes, spread 0.85 m |
| `scrub_brush.n.01_1` | scrub_brush_86 | scrub_brush / hsejyi | bedroom_0 | table/counter (0.6-1.1 m), z 0.79 | 1.8 m (range 1.2-2.62) | yes, spread 1.4 m |
| `desk.n.01_1` | desk_aduafr_0 | desk / aduafr | bedroom_0 | low (0.25-0.6 m), z 0.44 | 1.81 m (range 1.13-2.36) | no (fixed) |
| `floor.n.01_1` | floors_nlswvt_0 | floors / nlswvt | bedroom_0 | floor, z -0.15 | 0.82 m (range 0.39-1.56) | no (fixed) |

Initial conditions from `:init`:

```lisp
(covered cornet.n.01_1 dust.n.01_1)
(inroom desk.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop cornet.n.01_1 desk.n.01_1)
(ontop scrub_brush.n.01_1 desk.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching cornet.n.01_1 desk.n.01_1)
(touching desk.n.01_1 cornet.n.01_1)
(touching desk.n.01_1 scrub_brush.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching scrub_brush.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 161.47 s (range 93.0-241.57). Skills per demo 6.0 (range 5-9). 4 distinct skill orders; the most common one covers 95% of demos.

Most common skill counts per demo (95% of demos): move to x2, hand over x1, pick up from x1, place on x1, wipe hard x1.

Representative demo `episode_00370500.json` (160.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the scrub brush` (0.0-32.0 s)
2. `pick up the scrub brush from the desk` (32.0-59.0 s)
3. `hand over the scrub brush with the left` (61.5-79.0 s)
4. `move to the trumpet` (80.8-85.7 s)
5. `wipe the scrub brush` (85.7-148.6 s)
6. `place the scrub brush on the desk` (149.8-160.2 s)

Mean duration per skill in this task: hand over 17.2 s, move to 11.8 s, pick up from 32.9 s, place on 10.1 s, wipe hard 70.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the trumpet` | 207 |
| `hand over the scrub brush with the left` | 200 |
| `wipe the scrub brush` | 200 |
| `pick up the scrub brush from the desk` | 197 |
| `move to the scrub brush` | 195 |
| `place the scrub brush on the desk` | 195 |
| `place the trumpet on the desk` | 10 |
| `pick up the trumpet from the desk` | 9 |
| `pick up the scrub brush from the floors` | 2 |
| `place the scrub brush on the to_the_edge_of desk` | 2 |
| `place the floors on the desk` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/37_clean_a_trumpet.json`. Planner notes: `task_docs/notes/37_clean_a_trumpet.md`.
