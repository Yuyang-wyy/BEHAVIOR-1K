# 05 · Setting Mousetraps

Task name `setting_mousetraps`, task index 5.

> Take the four mousetraps from the cabinet in the bathroom and place them on the bathroom floor. Make sure all four end up on the same floor surface, and ensure that at least two of them are either under or directly next to the same bathroom sink.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | bathroom |
| rooms loaded | bathroom_0 |
| human demo length | 339.9 s mean (10196 steps) |
| episode time limit | 509.8 s (15294 steps at 30 Hz) |
| human base travel | 31.6006 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 96 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.33; ft40k@local Q=0.33 |
| demo video | https://player.vimeo.com/video/1114054686 |

## Planner notes

**Tier:** B — plain pick-and-place of four small traps from a cabinet top to the floor; no doors, no state change. Grasp width is borderline (see Hard parts).

### Goal in plain words

- All four mousetraps must rest on the bathroom floor (`floors_tfuahz_0`, the only floor in bathroom_0).
- At least two of them must be `under` or `nextto` the bathroom sink (`furniture_sink_ojjqku_0`, the only sink in the room).
- The traps are interchangeable; any two can be the sink pair, and `under` vs `nextto` is free per trap.
- The traps start **on top of** the closed bottom cabinet (z 0.89 m), not inside it. No door needs opening, despite the instruction's "from the cabinet".

### Q traps

- 6 literals in the best option (4 `ontop floor` + 2 sink literals); none is true at reset, so every literal scores.
- The sink part is `forn (2)`: success needs **exactly** two traps under/next to the sink. A third one there blocks success (PREDICATES §0).
- Partial Q is still 6/6 = 1.0 with three or four traps at the sink, because each ground option names only two traps (PREDICATES §0-1). The overshoot only costs early termination, not score.
- A trap on the sink pedestal, the bathtub rim, the serving cart or the toilet does not count as `ontop floor`.
- A trap resting on another trap does not touch the floor, so `ontop floor` is False for it (PREDICATES §4).
- Cabinet joints start at 0 (closed) per template `joint_pos`; the goal does not check them, so bumping a door costs nothing.

### Minimal plan

Demo pattern (93% of demos): carry two traps at once, one per hand, place both at the sink, then two more at the toilet.

1. `move to the mousetrap` — done: cabinet top with traps centred in head camera, base stopped. ~24 s.
2. `pick up the mousetrap from the bottom cabinet` — done: gripper closed short of fully shut, trap lifted off the top. ~31 s.
3. `pick up the mousetrap from the bottom cabinet` (second hand) — same check on the other gripper. ~31 s.
4. `move to the furniture sink` — done: sink basin fills the view, base stopped. ~24 s.
5. `place the mousetrap on the floors next to the under furniture sink` — done: trap visible on floor below or beside the sink, gripper open. ~23 s.
6. `place the mousetrap on the floors next to the under furniture sink` (second trap). ~23 s.
7. `move to the mousetrap`, then steps 2-3 again for the last two traps. ~85 s.
8. `move to the toilet` — any floor spot at least ~0.2 m from the sink works; the toilet is the trained target. ~24 s.
9. `place the mousetrap on the floors next to the under toilet` twice. ~46 s.

Total about 330 s against a 509.8 s limit.

### What the demos do differently

- Demos put the second pair at the toilet. The goal only needs them on the floor and away from the sink; the toilet just keeps them out of the `forn (2)` count.
- The duplicated place/pick segments are the two hands; a one-handed plan doubles the move steps (~4 x 24 s extra, still inside the limit).
- 4 distinct orders across 200 demos; the rare variants place on the sink top, which the goal does not want.

### Hard parts and hacks

- Trap size is 0.108 x 0.050 x 0.018 m (asset bbox, scale 1.0). The 50 mm width is just over the ~44 mm assisted-grasp span; the 18 mm height is under it. Whether a top-down grasp registers is unverified. ft40k got Q = 0.33 on instance 311 (2 of 6 literals), so at least some traps reached the floor.
- Cheap partial Q: pushing a trap off the cabinet top onto the floor scores its `ontop floor` literal (4/6 = 0.67 for all four) without a grasp. Check it lands flat and alone.
- Picking a trap back up from the floor has no trained prompt; closest: `pick up the mousetrap from the bottom cabinet`.
- Cabinet (2.09, 2.02) to sink (-2.16, 2.22) is ~4.3 m in the template; the toilet (0.47, 3.84) lies between them.
- `nextto` threshold (derived from PREDICATES §5 with asset bboxes): gap between trap and sink AABBs must be ≤ ~0.14 m, and a horizontal ray from the trap centre (1 cm above the floor) must hit sink geometry.
- `under`: the sink root sits at z 0.63 with 0.71 m height, so the basin is raised above the floor (derived, not rendered). A trap on the floor with its centre below the basin satisfies `under`. Beside a narrow pedestal it may not (PREDICATES §9).

### Hints for the VLM

- Everything is in bathroom_0; only the bathroom is loaded.
- The four traps are small flat wooden rectangles on the top of the low bottom cabinet, all at the same height.
- The furniture sink is the only sink; the toilet, bathtub and shower are distractors for "under".
- Done for the sink pair: two traps on the tiles directly below or touching the sink base.
- Done for the others: two traps on open tiles, clearly away from the sink, not on each other.
- Do not put a third trap near the sink if full success is still possible.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop mousetrap.n.01_4 floor.n.01_1)` | no | yes |
| `(ontop mousetrap.n.01_3 floor.n.01_1)` | no | yes |
| `(ontop mousetrap.n.01_2 floor.n.01_1)` | no | yes |
| `(ontop mousetrap.n.01_1 floor.n.01_1)` | no | yes |
| `(under mousetrap.n.01_4 sink.n.01_1)` | no | yes |
| `(under mousetrap.n.01_3 sink.n.01_1)` | no | yes |

The goal has 96 ground options (6 literals x96); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?floor.n.01 - floor.n.01)
                (forall
                    (?mousetrap.n.01 - mousetrap.n.01)
                    (ontop ?mousetrap.n.01 ?floor.n.01)
                )
            )
            (exists
                (?sink.n.01 - sink.n.01)
                (forn
                    (2)
                    (?mousetrap.n.01 - mousetrap.n.01)
                    (or
                        (under ?mousetrap.n.01 ?sink.n.01)
                        (nextto ?mousetrap.n.01 ?sink.n.01)
                    )
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
| `mousetrap.n.01_1` | mousetrap_50 | mousetrap / mwfwsv | bathroom_0 | table/counter (0.6-1.1 m), z 0.89 | 1.8 m (range 1.0-2.9) | yes, spread 1.14 m |
| `mousetrap.n.01_2` | mousetrap_49 | mousetrap / mwfwsv | bathroom_0 | table/counter (0.6-1.1 m), z 0.89 | 1.82 m (range 0.89-3.21) | yes, spread 1.03 m |
| `mousetrap.n.01_3` | mousetrap_48 | mousetrap / mwfwsv | bathroom_0 | table/counter (0.6-1.1 m), z 0.89 | 1.66 m (range 1.08-3.06) | yes, spread 1.11 m |
| `mousetrap.n.01_4` | mousetrap_47 | mousetrap / mwfwsv | bathroom_0 | table/counter (0.6-1.1 m), z 0.89 | 1.66 m (range 0.88-3.1) | yes, spread 1.08 m |
| `floor.n.01_1` | floors_tfuahz_0 | floors / tfuahz | bathroom_0 | floor, z -0.15 | 0.81 m (range 0.3-1.32) | no (fixed) |
| `sink.n.01_1` | furniture_sink_ojjqku_0 | furniture_sink / ojjqku | bathroom_0 | table/counter (0.6-1.1 m), z 0.63 | 2.53 m (range 1.2-3.29) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_jhymlr_0 | bottom_cabinet / jhymlr | bathroom_0 | low (0.25-0.6 m), z 0.49 | 1.73 m (range 0.99-3.16) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 bathroom)
(inroom floor.n.01_1 bathroom)
(inroom sink.n.01_1 bathroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop mousetrap.n.01_1 cabinet.n.01_1)
(ontop mousetrap.n.01_2 cabinet.n.01_1)
(ontop mousetrap.n.01_3 cabinet.n.01_1)
(ontop mousetrap.n.01_4 cabinet.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching cabinet.n.01_1 mousetrap.n.01_1)
(touching cabinet.n.01_1 mousetrap.n.01_2)
(touching cabinet.n.01_1 mousetrap.n.01_3)
(touching cabinet.n.01_1 mousetrap.n.01_4)
(touching floor.n.01_1 agent.n.01_1)
(touching mousetrap.n.01_1 cabinet.n.01_1)
(touching mousetrap.n.01_2 cabinet.n.01_1)
(touching mousetrap.n.01_3 cabinet.n.01_1)
(touching mousetrap.n.01_4 cabinet.n.01_1)
```

## What the human demos did

200 annotated demos. Length 309.95 s (range 186.8-751.07). Skills per demo 12.0 (range 10-12). 4 distinct skill orders; the most common one covers 93% of demos.

Most common skill counts per demo (93% of demos): move to x4, pick up from x4, place on next to x4.

Representative demo `episode_00052470.json` (307.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the mousetrap` (3.7-8.8 s)
2. `pick up the mousetrap from the bottom cabinet` (8.8-39.7 s)
3. `pick up the mousetrap from the bottom cabinet` (39.7-71.4 s)
4. `move to the furniture sink` (71.5-93.0 s)
5. `place the mousetrap on the floors next to the under furniture sink` (93.0-127.0 s)
6. `place the mousetrap on the floors next to the under furniture sink` (127.0-128.1 s)
7. `move to the mousetrap` (128.1-178.7 s)
8. `pick up the mousetrap from the bottom cabinet` (178.7-211.4 s)
9. `pick up the mousetrap from the bottom cabinet` (211.4-270.9 s)
10. `move to the toilet` (270.9-281.2 s)
11. `place the mousetrap on the floors next to the under toilet` (281.3-310.3 s)
12. `place the mousetrap on the floors next to the under toilet` (310.3-311.5 s)

Mean duration per skill in this task: move to 24.0 s, pick up from 31.4 s, place on next to 22.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the mousetrap from the bottom cabinet` | 800 |
| `move to the mousetrap` | 400 |
| `place the mousetrap on the floors next to the under furniture sink` | 391 |
| `place the mousetrap on the floors next to the under toilet` | 387 |
| `move to the furniture sink` | 200 |
| `move to the toilet` | 200 |
| `place the mousetrap on the furniture sink next to the under toilet` | 2 |
| `place the mousetrap on the furniture sink next to the under floors` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/05_setting_mousetraps.json`. Planner notes: `task_docs/notes/05_setting_mousetraps.md`.
