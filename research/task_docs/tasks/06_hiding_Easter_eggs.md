# 06 · Hiding Easter Eggs

Task name `hiding_Easter_eggs`, task index 6.

> Take the three Easter eggs out of the wicker basket on the lawn in the garden, then place them on the lawn next to a single tree (choose any tree) so that all three eggs are next to the same tree and none are left in the basket.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 254.0 s mean (7619 steps) |
| episode time limit | 381.0 s (11429 steps at 30 Hz) |
| human base travel | 21.8954 m |
| goal literals (best ground option) | 9 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 26 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=1.00 (success); ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114055436 |

## Planner notes

**Tier:** C — the eggs are ~15 cm wide, far past the 44 mm grasp span, and the basket can be up to 44 m from the start; long outdoor navigation with no global pose.

### Goal in plain words

- All three Easter eggs must be out of the wicker basket and resting on the main lawn (`lawn_aztwla_0`).
- All three must be `nextto` the **same** tree; any of the 26 garden trees works.
- The eggs are interchangeable. The basket can go anywhere; its position is not checked.
- Eggs on a paver, the driveway, or one of the three other lawn patches (`lawn_srfikq_0`, `lawn_tiqndr_0`, `lawn_zjtrpt_0`) do not count as `ontop lawn.n.01_1`.

### Q traps

- 9 literals in the best option: 3 `nextto tree`, 3 `not inside basket`, 3 `ontop lawn`. None is true at reset, so all nine score.
- `not inside basket` is the cheapest: any egg out of the basket volume scores it, even if held (PREDICATES §3).
- An egg lying out of the basket on the lawn scores 2 of its 3 literals anywhere. That is 6/9 = 0.67 with no tree at all.
- An egg resting on the basket, on another egg or against a root/bush it sits on does not touch the lawn, so `ontop` fails.
- Splitting eggs between two trees loses the `nextto` literals of the minority tree; pick one tree and stick to it.

### Minimal plan

Most common demo order (53%): carry the basket to a tree, then shuttle the eggs.

1. `move to the wicker basket` — done: basket centred in view, base stopped. Budget 28 s mean, but up to ~80 s on far instances.
2. `pick up the wicker basket from the lawn` — done: basket lifted, gripper stopped on the handle. ~21 s.
3. `move to the tree` — pick the nearest tree; one is always 0.8-5.6 m from the basket across the 20 public instances. ~28 s.
4. `place the wicker basket on the lawn` — done: basket upright on grass beside the trunk. ~10 s.
5. `pick up the easter egg from the wicker basket` — done: egg above the rim. ~21 s.
6. `place the easter egg on the lawn next to the in_front_of tree` — done: egg on grass close to the trunk, gripper open. ~19 s.
7. Repeat 5-6 twice (use `move to the wicker basket` if the base must reposition). ~80 s.

Roughly 230 s plus navigation against a 381 s limit. On far instances the drive dominates.

### What the demos do differently

- 26 distinct skill orders. 45% leave the basket in place and walk each egg to the tree instead of carrying the basket; that costs extra walking.
- Two demos put the basket "on the tree"; irrelevant to the goal.
- Humans pick the tree nearest the basket. Copy that.

### Hard parts and hacks

- Egg size: asset bbox 0.057 x 0.043 x 0.043 m times instance scale (2.73, 3.37, 3.00) gives about 0.16 x 0.14 x 0.13 m. No dimension is under 44 mm, so a normal assisted grasp should not register. Yet zs_pt50 reached full success on instance 311 (n=1); how it moved the eggs is unverified.
- Basket is 0.39 x 0.41 x 0.43 m (scale 1.0); the demos grasp it, presumably by the handle (handle width unverified).
- Hack worth testing (unverified): carry the basket next to a trunk and tip it (`tip over the <obj>` exists in the vocabulary, but no demo in this task uses it; no trained prompt here). Spilled eggs that roll onto the lawn near the trunk could score all nine literals without any egg grasp.
- `nextto` on a tree (PREDICATES §5): the tree AABB includes the canopy, so an egg under the canopy has AABB gap 0. The binding test is the ray check: one of the egg's 16 horizontal rays, cast at ~7 cm height, must hit tree geometry within 5 m. At that height only the trunk exists, and rays are 22.5° apart. Place eggs within a few tens of cm of the trunk. Trunk width is unverified.
- Robot start to basket: 3.6-44 m (median ~15 m) over the public instances; the basket position changes per instance (spread 47 m), trees are fixed.
- Eggs are round and may roll after release; re-check they rest on grass.

### Hints for the VLM

- Everything happens outdoors in garden_0; the robot starts on the lawn.
- The wicker basket is a brown woven basket, about knee height, sitting on grass with the three large eggs inside.
- Trees: 26 in the garden, five models. Any trunk works; bushes (many `bush_*` objects), garden lights, fence posts and the swing set are not trees.
- Stay on grass: avoid the pavers, driveway and playground surface near the house.
- Done per egg: egg lying on grass, touching or within a hand's width of the trunk, basket no longer around it.
- Done overall: three eggs clustered at one trunk, basket empty.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(nextto easter_egg.n.01_1 tree.n.01_3)` | no | yes |
| `(nextto easter_egg.n.01_3 tree.n.01_3)` | no | yes |
| `(nextto easter_egg.n.01_2 tree.n.01_3)` | no | yes |
| `(not inside easter_egg.n.01_1 wicker_basket.n.01_1))` | no | yes |
| `(ontop easter_egg.n.01_1 lawn.n.01_1)` | no | yes |
| `(not inside easter_egg.n.01_3 wicker_basket.n.01_1))` | no | yes |
| `(ontop easter_egg.n.01_3 lawn.n.01_1)` | no | yes |
| `(not inside easter_egg.n.01_2 wicker_basket.n.01_1))` | no | yes |
| `(ontop easter_egg.n.01_2 lawn.n.01_1)` | no | yes |

The goal has 26 ground options (9 literals x26); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?tree.n.01 - tree.n.01)
                (forall
                    (?easter_egg.n.01 - easter_egg.n.01)
                    (and
                        (nextto ?easter_egg.n.01 ?tree.n.01)
                    )
                )
            )
            (forall
                (?easter_egg.n.01 - easter_egg.n.01)
                (and
                    (not
                        (inside ?easter_egg.n.01 ?wicker_basket.n.01_1)
                    )
                    (ontop ?easter_egg.n.01 ?lawn.n.01_1)
                )
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `easter_egg.n.01_1` | easter_egg_181 | easter_egg / rxwfse | garden_0 | floor, z 0.15 | 14.8 m (range 3.66-43.96) | yes, spread 47.18 m |
| `easter_egg.n.01_2` | easter_egg_180 | easter_egg / rxwfse | garden_0 | floor, z 0.09 | 14.83 m (range 3.55-43.92) | yes, spread 47.21 m |
| `easter_egg.n.01_3` | easter_egg_179 | easter_egg / rxwfse | garden_0 | floor, z 0.2 | 14.8 m (range 3.55-43.88) | yes, spread 47.04 m |
| `wicker_basket.n.01_1` | wicker_basket_178 | wicker_basket / drxfmr | garden_0 | floor, z 0.19 | 14.81 m (range 3.61-43.95) | yes, spread 47.18 m |
| `lawn.n.01_1` | lawn_aztwla_0 | lawn / aztwla | garden_0 | floor, z -0.15 | 13.46 m (range 4.26-23.61) | no (fixed) |
| `tree.n.01_1` | tree_wtyipq_6 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 12.91 m (range 1.31-34.17) | no (fixed) |
| `tree.n.01_2` | tree_wtyipq_1 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 24.84 m (range 1.79-34.67) | no (fixed) |
| `tree.n.01_3` | tree_gmzozb_4 | tree / gmzozb | garden_0 | very high (>1.6 m), z 4.97 | 23.82 m (range 17.32-36.53) | no (fixed) |
| `tree.n.01_4` | tree_gmzozb_2 | tree / gmzozb | garden_0 | very high (>1.6 m), z 4.97 | 30.97 m (range 19.74-43.24) | no (fixed) |
| `tree.n.01_5` | tree_rrhqpw_0 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 11.61 m (range 1.54-41.05) | no (fixed) |
| `tree.n.01_6` | tree_wtyipq_3 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 19.16 m (range 3.0-29.03) | no (fixed) |
| `tree.n.01_7` | tree_rrhqpw_3 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 9.32 m (range 2.9-39.48) | no (fixed) |
| `tree.n.01_8` | tree_wtyipq_7 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 17.01 m (range 4.33-32.38) | no (fixed) |
| `tree.n.01_9` | tree_rrhqpw_1 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 12.34 m (range 5.28-24.91) | no (fixed) |
| `tree.n.01_10` | tree_wtyipq_2 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 9.34 m (range 2.04-37.56) | no (fixed) |
| `tree.n.01_11` | tree_flkzbo_2 | tree / flkzbo | garden_0 | very high (>1.6 m), z 3.78 | 36.65 m (range 2.96-46.46) | no (fixed) |
| `tree.n.01_12` | tree_dyymaq_2 | tree / dyymaq | garden_0 | very high (>1.6 m), z 3.72 | 12.68 m (range 2.28-30.9) | no (fixed) |
| `tree.n.01_13` | tree_gmzozb_1 | tree / gmzozb | garden_0 | very high (>1.6 m), z 4.97 | 28.42 m (range 18.71-40.89) | no (fixed) |
| `tree.n.01_14` | tree_rrhqpw_4 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 11.49 m (range 3.95-40.37) | no (fixed) |
| `tree.n.01_15` | tree_wtyipq_5 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 16.0 m (range 2.72-38.52) | no (fixed) |
| `tree.n.01_16` | tree_wtyipq_0 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 37.16 m (range 5.2-46.99) | no (fixed) |
| `tree.n.01_17` | tree_flkzbo_1 | tree / flkzbo | garden_0 | very high (>1.6 m), z 3.78 | 27.2 m (range 2.05-37.11) | no (fixed) |
| `tree.n.01_18` | tree_gmzozb_0 | tree / gmzozb | garden_0 | very high (>1.6 m), z 4.97 | 26.37 m (range 17.99-38.84) | no (fixed) |
| `tree.n.01_19` | tree_rrhqpw_2 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 14.95 m (range 1.63-23.64) | no (fixed) |
| `tree.n.01_20` | tree_flkzbo_0 | tree / flkzbo | garden_0 | very high (>1.6 m), z 3.78 | 35.6 m (range 6.41-45.54) | no (fixed) |
| `tree.n.01_21` | tree_wtyipq_4 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 10.45 m (range 4.33-41.13) | no (fixed) |
| `tree.n.01_22` | tree_rrhqpw_5 | tree / rrhqpw | garden_0 | very high (>1.6 m), z 3.86 | 18.71 m (range 1.65-38.36) | no (fixed) |
| `tree.n.01_23` | tree_gmzozb_3 | tree / gmzozb | garden_0 | very high (>1.6 m), z 4.97 | 33.35 m (range 20.24-45.45) | no (fixed) |
| `tree.n.01_24` | tree_dyymaq_0 | tree / dyymaq | garden_0 | very high (>1.6 m), z 3.72 | 31.98 m (range 2.97-41.75) | no (fixed) |
| `tree.n.01_25` | tree_wtyipq_8 | tree / wtyipq | garden_0 | very high (>1.6 m), z 2.21 | 13.88 m (range 3.15-23.8) | no (fixed) |
| `tree.n.01_26` | tree_dyymaq_1 | tree / dyymaq | garden_0 | very high (>1.6 m), z 3.72 | 12.86 m (range 2.0-37.71) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom lawn.n.01_1 garden)
(inroom tree.n.01_1 garden)
(inroom tree.n.01_10 garden)
(inroom tree.n.01_11 garden)
(inroom tree.n.01_12 garden)
(inroom tree.n.01_13 garden)
(inroom tree.n.01_14 garden)
(inroom tree.n.01_15 garden)
(inroom tree.n.01_16 garden)
(inroom tree.n.01_17 garden)
(inroom tree.n.01_18 garden)
(inroom tree.n.01_19 garden)
(inroom tree.n.01_2 garden)
(inroom tree.n.01_20 garden)
(inroom tree.n.01_21 garden)
(inroom tree.n.01_22 garden)
(inroom tree.n.01_23 garden)
(inroom tree.n.01_24 garden)
(inroom tree.n.01_25 garden)
(inroom tree.n.01_26 garden)
(inroom tree.n.01_3 garden)
(inroom tree.n.01_4 garden)
(inroom tree.n.01_5 garden)
(inroom tree.n.01_6 garden)
(inroom tree.n.01_7 garden)
(inroom tree.n.01_8 garden)
(inroom tree.n.01_9 garden)
(inside easter_egg.n.01_1 wicker_basket.n.01_1)
(inside easter_egg.n.01_2 wicker_basket.n.01_1)
(inside easter_egg.n.01_3 wicker_basket.n.01_1)
(ontop agent.n.01_1 lawn.n.01_1)
(ontop wicker_basket.n.01_1 lawn.n.01_1)
(touching agent.n.01_1 lawn.n.01_1)
(touching lawn.n.01_1 agent.n.01_1)
(touching lawn.n.01_1 wicker_basket.n.01_1)
(touching wicker_basket.n.01_1 lawn.n.01_1)
```

## What the human demos did

200 annotated demos. Length 230.0 s (range 106.33-532.83). Skills per demo 12.0 (range 8-15). 26 distinct skill orders; the most common one covers 53% of demos.

Most common skill counts per demo (55% of demos): move to x4, pick up from x4, place on next to x3, place on x1.

Representative demo `episode_00062920.json` (227.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the wicker basket` (13.2-96.4 s)
2. `pick up the wicker basket from the lawn` (96.4-107.5 s)
3. `move to the tree` (107.5-125.5 s)
4. `place the wicker basket on the lawn` (125.5-138.1 s)
5. `pick up the easter egg from the wicker basket` (138.1-154.3 s)
6. `place the easter egg on the lawn next to the in_front_of tree` (154.3-168.8 s)
7. `move to the wicker basket` (168.8-170.7 s)
8. `pick up the easter egg from the wicker basket` (170.7-184.3 s)
9. `place the easter egg on the lawn next to the in_front_of tree` (184.3-196.0 s)
10. `move to the wicker basket` (196.1-203.1 s)
11. `pick up the easter egg from the wicker basket` (203.1-221.4 s)
12. `place the easter egg on the lawn next to the in_front_of tree` (221.4-241.0 s)

Mean duration per skill in this task: move to 27.7 s, pick up from 21.0 s, place on 9.6 s, place on next to 18.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the easter egg from the wicker basket` | 599 |
| `place the easter egg on the lawn next to the in_front_of tree` | 565 |
| `move to the wicker basket` | 498 |
| `move to the tree` | 248 |
| `pick up the wicker basket from the lawn` | 190 |
| `place the wicker basket on the lawn` | 188 |
| `place the wicker basket on the tree` | 2 |
| `pick up the easter egg from the lawn` | 1 |
| `place the easter egg on the wicker basket next to the in_front_of tree` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/06_hiding_Easter_eggs.json`. Planner notes: `task_docs/notes/06_hiding_Easter_eggs.md`.
