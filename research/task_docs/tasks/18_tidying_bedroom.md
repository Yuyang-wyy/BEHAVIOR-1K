# 18 · Tidying Bedroom

Task name `tidying_bedroom`, task index 18.

> In the bedroom, move the book from the bed onto either nightstand, and place the two sandals side by side next to the bed.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | bedroom |
| rooms loaded | bathroom_1, bedroom_0, corridor_0, dining_room_0, entryway_0, garden_0 |
| human demo length | 367.9 s mean (11037 steps) |
| episode time limit | 551.9 s (16556 steps at 30 Hz) |
| human base travel | 33.3982 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.67; ft40k@sulab1 Q=0.67; ft40k@local Q=0.67 |
| demo video | https://player.vimeo.com/video/1114058519 |

## Planner notes

**Tier:** B — two sandals (0.24 x 0.09 x 0.03 m, flat on the floor) and one hardback (0.19 x 0.13 x 0.02 m, flat on the bed) in one room. All three models scored 0.67 on instance 311, so at least two literals are reachable with the current policy.

### Goal in plain words

Sandal 1 (`sandal_190`) must be next to the bed, and sandal 2 (`sandal_189`) must be next to sandal 1.
The book must rest on either nightstand (2 ground options, Q takes the better one).
The two sandals are NOT interchangeable in the literals: `sandal_190` is the one that must be by the bed, and `sandal_189` must be by `sandal_190`.
Nothing has to be closed.

### Q traps

- 3 literals, all inferred False at reset. Max partial Q 1.0.
- Estimated from instance poses and asset bboxes (AABB gap vs the L/6 threshold, PREDICATES §5; ray test not checked): in instance 305 `sandal_190` starts 0.24 m from the bed, under its 0.29 m threshold, so `nextto sandal_190 bed` is probably already true there and would never score. In 306 the gap (0.287 m) is on the threshold. In 311 it is 0.46 m, so it is False.
- `nextto sandal_189 sandal_190` is a small-small pair: the AABB gap must be under about 5 cm (L/6 = 0.044-0.054 m across instances). Placing both "next to the bed" with a hand-width gap fails this literal. Put the second sandal practically touching the first.
- `nextto sandal bed` allows up to ~0.29 m gap, but the height term counts: a sandal on the floor beside the 0.8 m bed is fine because the AABBs overlap in z.
- The book on a nightstand needs its centre over the top and contact (PREDICATES §4). A table lamp stands on each nightstand; the book must not rest on the lamp base.

### Minimal plan

Everything is in bedroom_0, 0.4-4.3 m from the start.

1. `move to the sandal` — a sandal centred in view on the floor. ~27 s.
2. `pick up the sandal from the floors` — sandal off the floor in one gripper. ~36 s.
3. `move to the sandal`, `pick up the sandal from the floors` — second sandal in the other gripper. ~27 s + 36 s.
4. `move to the bed` — base stopped beside the bed. ~27 s.
5. `place the sandal on the floors next to the left bed` — place `sandal_190` first, on the floor within ~0.25 m of the bed side. ~23 s.
6. `place the sandal on the floors next to the left bed` — place `sandal_189` touching `sandal_190` (gap < 5 cm). ~23 s. `place the sandal on the floors next to the left sandal` exists (3 demos) and states the true requirement; it is rarer in training.
7. `move to the hardback` — book on the bed in view. ~27 s.
8. `push the hardback to the to_the_edge_of bed` — book overhanging the mattress edge. ~53 s.
9. `pick up the hardback from the bed` — book lifted clear. ~36 s.
10. `move to the nightstand`, `place the hardback on the nightstand` — book flat on the top, beside the lamp. ~27 s + 28 s.

Budget: about 375 s against a 552 s limit.

### What the demos do differently

- All 200 demos carry both sandals at once and place them both with the "next to the left bed" sentence. They do not distinguish which sandal goes first. The planner must: `sandal_190` goes nearest the bed.
- 199/200 demos push the book to the bed edge before picking it up. This is the trained trick for a flat book; keep it.
- Every demo uses `nightstand_wbxekb_0`; either nightstand scores.

### Hard parts and hacks

- Sandals lie flat: 0.09 m wide, 0.034 m tall. A straddling grasp must be across the height (sole to strap) or on a strap; unverified which registers.
- The book is 0.021 m thick lying flat. It is only graspable after it overhangs the bed edge (the push step).
- The sandal-sandal 5 cm tolerance is the likely lost literal. Setting the second sandal down against the side of the first is the fix; a small `push the sandal to` nudge is not in the demos.

### Hints for the VLM

- The two sandals are different models (`tkfdsk` = `sandal_190`, `txkidl` = `sandal_189`); telling them apart in RGB needs a look at colour/shape at reset. Unverified which looks like which.
- The bedroom has one bed, two identical nightstands (each with a table lamp), a bench and a wall-mounted TV. The book lies on the bed.
- Done for the sandals: first sandal on the floor right beside the bed frame, second sandal side by side with it, no visible floor gap between them.
- Done for the book: lying flat on a nightstand top, not on the bed or floor.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(nextto sandal.n.01_1 bed.n.01_1)` | no | yes |
| `(nextto sandal.n.01_2 sandal.n.01_1)` | no | yes |
| `(ontop book.n.02_1 table.n.02_2)` | no | yes |

The goal has 2 ground options (3 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (nextto ?sandal.n.01_1 ?bed.n.01_1) 
            (nextto ?sandal.n.01_2 ?sandal.n.01_1) 
            (exists 
                (?table.n.02 - table.n.02) 
                (ontop ?book.n.02_1 ?table.n.02)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `sandal.n.01_1` | sandal_190 | sandal / tkfdsk | bedroom_0 | floor, z 0.01 | 1.89 m (range 0.66-3.07) | yes, spread 4.67 m |
| `sandal.n.01_2` | sandal_189 | sandal / txkidl | bedroom_0 | floor, z 0.01 | 1.9 m (range 0.39-3.2) | yes, spread 4.82 m |
| `table.n.02_1` | nightstand_wbxekb_1 | nightstand / wbxekb | bedroom_0 | floor, z 0.16 | 2.92 m (range 1.24-4.25) | no (fixed) |
| `table.n.02_2` | nightstand_wbxekb_0 | nightstand / wbxekb | bedroom_0 | floor, z 0.16 | 3.23 m (range 2.58-5.12) | no (fixed) |
| `book.n.02_1` | hardback_188 | hardback / dmqfqx | bedroom_0 | low (0.25-0.6 m), z 0.49 | 1.95 m (range 0.86-3.39) | yes, spread 2.2 m |
| `floor.n.01_1` | floors_htolat_0 | floors / htolat | bedroom_0 | floor, z -0.14 | 1.08 m (range 0.48-2.42) | no (fixed) |
| `bed.n.01_1` | bed_gxfipj_0 | bed / gxfipj | bedroom_0 | low (0.25-0.6 m), z 0.27 | 2.08 m (range 1.58-3.74) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(inroom table.n.02_1 bedroom)
(inroom table.n.02_2 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop book.n.02_1 bed.n.01_1)
(ontop sandal.n.01_1 floor.n.01_1)
(ontop sandal.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 book.n.02_1)
(touching book.n.02_1 bed.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 sandal.n.01_1)
(touching floor.n.01_1 sandal.n.01_2)
(touching sandal.n.01_1 floor.n.01_1)
(touching sandal.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 355.87 s (range 154.0-820.77). Skills per demo 12.0 (range 11-12). 6 distinct skill orders; the most common one covers 96% of demos.

Most common skill counts per demo (98% of demos): move to x5, pick up from x3, place on next to x2, place on x1, push to x1.

Representative demo `episode_00181570.json` (356.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the sandal` (2.1-12.3 s)
2. `pick up the sandal from the floors` (12.3-45.5 s)
3. `move to the sandal` (45.5-88.5 s)
4. `pick up the sandal from the floors` (88.5-125.4 s)
5. `move to the bed` (125.4-158.6 s)
6. `place the sandal on the floors next to the left bed` (158.6-181.1 s)
7. `place the sandal on the floors next to the left bed` (181.1-201.1 s)
8. `move to the hardback` (201.1-237.9 s)
9. `push the hardback to the to_the_edge_of bed` (237.9-302.6 s)
10. `pick up the hardback from the bed` (302.7-331.7 s)
11. `move to the nightstand` (331.7-338.8 s)
12. `place the hardback on the nightstand` (338.8-358.3 s)

Mean duration per skill in this task: hand over 15.5 s, move to 26.7 s, pick up from 35.5 s, place on 28.4 s, place on next to 22.7 s, push to 52.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the sandal` | 398 |
| `pick up the sandal from the floors` | 398 |
| `place the sandal on the floors next to the left bed` | 394 |
| `move to the hardback` | 200 |
| `pick up the hardback from the bed` | 200 |
| `push the hardback to the to_the_edge_of bed` | 199 |
| `move to the bed` | 198 |
| `move to the nightstand` | 198 |
| `place the hardback on the nightstand` | 197 |
| `place the sandal on the floors next to the left sandal` | 3 |
| `place the hardback on the bed` | 2 |
| `place the sandal on the floors next to the in_front_of bed` | 2 |
| `move to the floors` | 2 |
| `hand over the hardback with the left` | 1 |
| `pick up the floors from the sandal` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/18_tidying_bedroom.json`. Planner notes: `task_docs/notes/18_tidying_bedroom.md`.
