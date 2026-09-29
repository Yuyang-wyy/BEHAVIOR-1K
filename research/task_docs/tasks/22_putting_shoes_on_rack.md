# 22 · Putting Shoes On Rack

Task name `putting_shoes_on_rack`, task index 22.

> Pick up the two gym shoes and the two sandals from the corridor floor and place them onto the hallstand (shoe rack) in the corridor, making sure they are on the rack and not on the floor. Arrange them so the two gym shoes are next to each other and the two sandals are next to each other.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | corridor |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 257.5 s mean (7726 steps) |
| episode time limit | 386.3 s (11589 steps at 30 Hz) |
| human base travel | 27.0157 m |
| goal literals (best ground option) | 10 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.50; ft40k@sulab1 Q=0.30; ft40k@local Q=0.30 |
| demo video | https://player.vimeo.com/video/1114058985 |

## Planner notes

**Tier:** B — four shoes go from the corridor floor onto one hall tree in the same corridor, short moves. No shoe dimension is under the 44 mm span across the body (gym shoes 0.31 x 0.11 x 0.14 m, sandals 0.26 x 0.11 x 0.12 m); the grasp must go on a rim, heel or strap (unverified).

### Goal in plain words

Both sandals and both gym shoes must touch the hall tree `hall_tree_daxzaw_0` and must not touch the corridor floor.
The two gym shoes must be next to each other, and the two sandals must be next to each other.
Shoes of the same kind are interchangeable within the pair; any shelf or hook of that hall tree works.

### Q traps

- The four `not touching <shoe> floor` literals start False: `:init` puts every shoe `ontop` the floor, and `ontop` requires contact (PREDICATES §4); the instances confirm the shoes rest on the floor (z 0.04-0.05). All 10 literals can score, so max partial Q is 1.0.
- Consequence: lifting a shoe off the floor scores 1/10 at once, even while it is still held. zs_pt50's 0.5 on instance 311 fits this.
- `nextto` between shoes of a pair needs an AABB gap under ~6-8 cm (L/6 = 0.058-0.081 m across instances, PREDICATES §5). Two shoes on the same shelf, placed side by side, pass. Shoes on different shelves at different heights fail. Both pairs are far apart at reset in all 20 instances (nearest 0.20 m in 301 and 312).
- A shoe resting partly on the floor, or leaning on the hall tree with the toe on the floor, fails `not touching floor` (PREDICATES §8).
- The corridor has two hall trees. The goal names `hall_tree_daxzaw_0` (at about x -1.19, y -0.21); the other, `hall_tree_upkvgr_0`, is 5.6 m further along the corridor. Shoes on the wrong one score only the `not touching floor` literals.
- `touching` is instantaneous contact. A shoe hovering a few mm over a shelf, or jittering, can flicker off.

### Minimal plan

Everything is in corridor_0; shoes are 0.7-6.7 m from the start, the hall tree 1.5-6.8 m.

1. `move to the sandal`, `pick up the sandal from the floors` — sandal off the floor (scores 1/10). ~19 s + 20 s.
2. `move to the sandal`, `pick up the sandal from the floors` with the other hand. ~19 s + 20 s. (The demos mix one sandal and one gym shoe per trip; carrying a matched pair makes the `nextto` placement easier.)
3. `move to the hall tree`. ~19 s.
4. `place the sandal in the high_level hall tree` twice, the second right beside the first on the same shelf. ~14 s each.
5. Repeat 1-4 for the gym shoes with `move to the gym shoe`, `pick up the gym shoe from the floors`, `place the gym shoe in the high_level hall tree`.

Done-check per shoe: shoe resting on the hall tree shelf, no part on the floor, gripper open. Done for a pair: the two shoes side by side with a gap under ~5 cm.
Budget: about 230 s against a 386 s limit.

### What the demos do differently

- Demos carry one sandal and one gym shoe per trip in about half the orders; many orders appear (top sequence only 6/200).
- Every demo uses the prompt `place the ... in the high_level hall tree`, i.e. the upper shelf.
- A few demos re-pick a shoe from the hall tree to fix its placement.

### Hard parts and hacks

- Grasp: no shoe body fits the 44 mm span. A gym shoe's collar/heel counter or a sandal strap is the likely grasp target; unverified that the assisted grasp registers there.
- Placing on a high shelf: the robot must reach up with a load; keep the base close to avoid tipping.
- The `nextto` pairs are the literals most likely to be lost. Place the second shoe of a pair directly against the first.
- Cheapest partial Q: lift and hold shoes. Each shoe off the floor is 1/10 even if never placed.

### Hints for the VLM

- The corridor is a long narrow hall (2.6 x 9 m) with two hall trees, a standing mirror and four doors. The target `hall_tree_daxzaw_0` stands at about (x -1.19, y -0.21), 1.5-6.8 m from the start; the other hall tree (different model) is 5.6 m along the corridor. Which looks like which is unverified; identify it at reset.
- Gym shoes are sneakers (two different models); sandals are open shoes (two different models).
- Done: four shoes on the target hall tree, sandals together, gym shoes together, corridor floor clear.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(touching sandal.n.01_2 hallstand.n.01_1)` | no | yes |
| `(not touching sandal.n.01_2 floor.n.01_1))` | no | yes |
| `(touching sandal.n.01_1 hallstand.n.01_1)` | no | yes |
| `(not touching sandal.n.01_1 floor.n.01_1))` | no | yes |
| `(touching gym_shoe.n.01_2 hallstand.n.01_1)` | no | yes |
| `(not touching gym_shoe.n.01_2 floor.n.01_1))` | no | yes |
| `(touching gym_shoe.n.01_1 hallstand.n.01_1)` | no | yes |
| `(not touching gym_shoe.n.01_1 floor.n.01_1))` | no | yes |
| `(nextto gym_shoe.n.01_1 gym_shoe.n.01_2)` | no | yes |
| `(nextto sandal.n.01_1 sandal.n.01_2)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?sandal.n.01 - sandal.n.01)
                (and
                    (touching ?sandal.n.01 ?hallstand.n.01_1)
                    (not
                        (touching ?sandal.n.01 floor.n.01_1)    
                    )
                )
            )
            (forall 
                (?gym_shoe.n.01 - gym_shoe.n.01)
                (and
                    (touching ?gym_shoe.n.01 ?hallstand.n.01_1)
                    (not
                        (touching ?gym_shoe.n.01 floor.n.01_1)    
                    )
                )
            )
            (nextto gym_shoe.n.01_1 gym_shoe.n.01_2)
            (nextto sandal.n.01_1 sandal.n.01_2)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `gym_shoe.n.01_1` | gym_shoe_78 | gym_shoe / mcfcwq | corridor_0 | floor, z 0.05 | 1.92 m (range 0.71-5.19) | yes, spread 6.37 m |
| `gym_shoe.n.01_2` | gym_shoe_77 | gym_shoe / kmcbym | corridor_0 | floor, z 0.05 | 2.42 m (range 0.72-5.03) | yes, spread 6.81 m |
| `floor.n.01_1` | floors_xorxro_0 | floors / xorxro | corridor_0 | floor, z -0.15 | 1.2 m (range 0.41-3.16) | no (fixed) |
| `sandal.n.01_1` | sandal_76 | sandal / dfkzbd | corridor_0 | floor, z 0.04 | 2.36 m (range 0.95-5.71) | yes, spread 7.54 m |
| `sandal.n.01_2` | sandal_75 | sandal / vwbomj | corridor_0 | floor, z 0.04 | 2.31 m (range 0.96-6.65) | yes, spread 7.02 m |
| `hallstand.n.01_1` | hall_tree_daxzaw_0 | hall_tree / daxzaw | corridor_0 | table/counter (0.6-1.1 m), z 0.97 | 3.39 m (range 1.54-6.84) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 corridor)
(inroom hallstand.n.01_1 corridor)
(ontop agent.n.01_1 floor.n.01_1)
(ontop gym_shoe.n.01_1 floor.n.01_1)
(ontop gym_shoe.n.01_2 floor.n.01_1)
(ontop sandal.n.01_1 floor.n.01_1)
(ontop sandal.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 gym_shoe.n.01_1)
(touching floor.n.01_1 gym_shoe.n.01_2)
(touching floor.n.01_1 sandal.n.01_1)
(touching floor.n.01_1 sandal.n.01_2)
(touching gym_shoe.n.01_1 floor.n.01_1)
(touching gym_shoe.n.01_2 floor.n.01_1)
(touching sandal.n.01_1 floor.n.01_1)
(touching sandal.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 242.98 s (range 154.67-570.0). Skills per demo 14.0 (range 13-14). 2 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x6, pick up from x4, place in x4.

Representative demo `episode_00220140.json` (242.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the sandal` (2.2-8.2 s)
2. `pick up the sandal from the floors` (8.2-34.8 s)
3. `move to the gym shoe` (34.8-47.4 s)
4. `pick up the gym shoe from the floors` (47.4-65.8 s)
5. `move to the hall tree` (65.8-67.8 s)
6. `place the sandal in the high_level hall tree` (67.8-84.8 s)
7. `place the gym shoe in the high_level hall tree` (84.8-98.5 s)
8. `move to the sandal` (98.5-138.7 s)
9. `pick up the sandal from the floors` (138.7-154.7 s)
10. `move to the gym shoe` (154.7-167.0 s)
11. `pick up the gym shoe from the floors` (167.0-188.3 s)
12. `move to the hall tree` (188.3-207.6 s)
13. `place the gym shoe in the high_level hall tree` (207.6-227.9 s)
14. `place the sandal in the high_level hall tree` (227.9-244.9 s)

Mean duration per skill in this task: move to 19.1 s, pick up from 19.7 s, place in 14.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the sandal` | 400 |
| `move to the gym shoe` | 400 |
| `move to the hall tree` | 399 |
| `pick up the sandal from the floors` | 398 |
| `place the gym shoe in the high_level hall tree` | 398 |
| `place the sandal in the high_level hall tree` | 397 |
| `pick up the gym shoe from the floors` | 394 |
| `pick up the gym shoe from the hall tree` | 5 |
| `place the gym shoe in the high_level floors` | 4 |
| `pick up the sandal from the hall tree` | 3 |
| `place the hall tree in the high_level hall tree` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/22_putting_shoes_on_rack.json`. Planner notes: `task_docs/notes/22_putting_shoes_on_rack.md`.
