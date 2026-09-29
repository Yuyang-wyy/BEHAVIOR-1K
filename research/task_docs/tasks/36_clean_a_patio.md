# 36 · Clean a Patio

Task name `clean_a_patio`, task index 36.

> Pick up the broom in the garden and sweep the mud off the patio floor until the floor is no longer covered in mud.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 402.4 s mean (12070 steps) |
| episode time limit | 603.5 s (18106 steps at 30 Hz) |
| human base travel | 37.2109 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060492 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered floor.n.01_1 mud.n.03_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (not 
                (covered ?floor.n.01_1 ?mud.n.03_1)
            ) 
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `mud.n.03_1` | particle system | mud | - | - | - | - |
| `broom.n.01_1` | broom_172 | broom / tpyvbt | garden_0 | floor, z 0.05 | 3.84 m (range 0.83-8.54) | yes, spread 12.37 m |
| `floor.n.01_1` | floors_ghetev_0 | floors / ghetev | garden_0 | floor, z -0.08 | 2.29 m (range 0.11-4.13) | no (fixed) |

Initial conditions from `:init`:

```lisp
(covered floor.n.01_1 mud.n.03_1)
(inroom floor.n.01_1 garden)
(ontop agent.n.01_1 floor.n.01_1)
(ontop broom.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching broom.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 broom.n.01_1)
```

## What the human demos did

200 annotated demos. Length 388.63 s (range 286.7-738.0). Skills per demo 51.0 (range 41-63). 167 distinct skill orders; the most common one covers 2% of demos.

Most common skill counts per demo (14% of demos): move to x24, sweep surface x20, push to x3, hold x2, release x2, pick up from x1, place on x1.

Representative demo `episode_00360030.json` (342.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the garden chair` (0.2-22.2 s)
2. `push the garden chair to the away robot` (22.2-45.7 s)
3. `move to the broom` (45.7-56.2 s)
4. `pick up the broom from the floors` (56.2-78.9 s)
5. `hold the broom` (78.9-84.5 s)
6. `move to the mud` (84.5-98.4 s)
7. `sweep the broom` (98.4-100.2 s)
8. `move to the mud` (100.2-114.5 s)
9. `sweep the broom` (114.5-116.1 s)
10. `move to the mud` (116.1-124.8 s)
11. `sweep the broom` (124.8-126.4 s)
12. `move to the mud` (126.4-135.4 s)
13. `sweep the broom` (135.4-138.0 s)
14. `move to the mud` (138.0-141.8 s)
15. `sweep the broom` (141.8-143.8 s)
16. `move to the mud` (143.8-153.0 s)
17. `sweep the broom` (153.0-154.5 s)
18. `move to the mud` (154.5-159.0 s)
19. `sweep the broom` (159.0-165.2 s)
20. `move to the mud` (165.2-181.0 s)
21. `sweep the broom` (181.0-182.4 s)
22. `move to the mud` (182.4-194.3 s)
23. `sweep the broom` (194.3-196.5 s)
24. `move to the mud` (196.5-207.9 s)
25. `sweep the broom` (207.9-209.9 s)
26. `move to the mud` (209.9-216.4 s)
27. `sweep the broom` (216.4-217.6 s)
28. `move to the mud` (217.6-219.3 s)
29. `sweep the broom` (219.3-220.2 s)
30. `move to the mud` (220.2-232.6 s)
31. `sweep the broom` (232.6-234.1 s)
32. `move to the mud` (234.1-241.2 s)
33. `sweep the broom` (241.2-243.0 s)
34. `move to the mud` (243.0-250.8 s)
35. `sweep the broom` (250.8-252.9 s)
36. `move to the mud` (252.9-259.1 s)
37. `sweep the broom` (259.1-267.5 s)
38. `move to the mud` (267.5-298.7 s)
39. `sweep the broom` (298.7-301.0 s)
40. `move to the mud` (301.0-312.9 s)
41. `sweep the broom` (312.9-314.6 s)
42. `move to the mud` (314.6-315.9 s)
43. `sweep the broom` (315.9-317.0 s)
44. `move to the mud` (317.0-322.4 s)
45. `sweep the broom` (322.4-324.0 s)
46. `release the broom` (324.0-326.1 s)
47. `place the broom on the floors` (326.1-343.0 s)

Mean duration per skill in this task: hand over 10.8 s, hold 7.5 s, move to 10.9 s, pick up from 28.8 s, place on 15.5 s, push to 14.0 s, release 3.7 s, sweep surface 3.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `sweep the broom` | 3837 |
| `move to the mud` | 3828 |
| `move to the garden chair` | 485 |
| `push the garden chair to the away robot` | 474 |
| `release the broom` | 448 |
| `hold the broom` | 447 |
| `move to the broom` | 200 |
| `pick up the broom from the floors` | 200 |
| `place the broom on the floors` | 200 |
| `pick up the garden chair from the floors` | 8 |
| `place the garden chair on the floors` | 8 |
| `hand over the broom with the right` | 5 |
| `hand over the broom with the left` | 4 |
| `move to the robot` | 1 |
| `hold the mud` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/36_clean_a_patio.json`. Planner notes: `task_docs/notes/36_clean_a_patio.md`.
