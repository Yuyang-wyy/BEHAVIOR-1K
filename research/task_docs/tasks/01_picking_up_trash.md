# 01 · Picking Up Trash

Task name `picking_up_trash`, task index 1.

> Put the three cans of soda from the living room inside the trash can in the kitchen.

Comet pretraining used this sentence instead: "Put the three can of soda from the living room inside the tash can in the kitchen."

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen, living_room |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 175.6 s mean (5267 steps) |
| episode time limit | 263.4 s (7901 steps at 30 Hz) |
| human base travel | 16.1977 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=1.00 (success); ft24k@sulab1 Q=0.67; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00; ft10k@sulab1 Q=0.00; pt0@sulab1 Q=0.67 |
| demo video | https://player.vimeo.com/video/1109202972 |

## Planner notes

**Tier:** B — three soda cans into one open-top trash can, all on the floor. No doors, no state changes.

### Goal in plain words

All three cans of soda must end with their AABB centres inside the trash can's volume. The cans are interchangeable. There is exactly one trash can (kitchen) and it is the only valid container. The goal has no room literal, so the trash can may be carried into the living room and left there. Nothing must be closed or put back.

### Q traps

- 3 literals, none true at start (cans on the living-room floor, trash can in the kitchen in all 20 instances). Max Q = 1.0.
- Success is checked every step. The episode ends the moment the third can is inside, so the demo's final `place the trash can on the floors` is never needed.
- Partial Q reads only the final state. Tipping the trash can (held or on the floor) can spill cans already scored.
- A can resting on the rim is not inside (centre test, PREDICATES §3). Re-check after each release.
- A held trash can still counts as the container. Cans inside a held, upright bin score.

### Minimal plan

Demo order (100% of 200 demos). It is also the order zs_pt50 used to succeed on 311 (Q 1.0, 5493 of 7901 steps).

1. `move to the trash can` — base stopped, bin centred in the head camera. ~14 s.
2. `pick up the trash can from the floors` — bin lifted clear of the floor in one gripper, upright. ~16 s.
3. `move to the can of soda` — a can visible near the free gripper. ~14 s.
4. `pick up the can of soda from the floors` — can off the floor in the free gripper. ~16 s.
5. `place the can of soda in the trash can` — can no longer in the gripper; depth shows it below the bin rim. ~8 s.
6. Repeat 3-5 for the other two cans. ~2 x 38 s.
7. Skip `place the trash can on the floors` unless the episode is still running; if used, keep the bin upright. ~12 s.

Budget ~155 s against a 263 s limit (7901 steps).

Alternative if carrying the bin fails: leave it on the kitchen floor and ferry cans. Can-to-bin distance is 1.7-6.5 m (median ~3.4 m) across instances, so three single-can trips roughly double travel. Carrying one can per hand halves it.

### What the demos do differently

- Every demo picks up the trash can first and carries it to the cans (200/200). The goal does not need this, but it is the in-distribution order and saves trips.
- Every demo ends by putting the bin down (198/200). Not needed.
- 5 demos contain `place the can of soda in the floors` and 4 contain `pick up the can of soda from the trash can`: recovery from a miss. Do not send these.

### Hard parts and hacks

- Can size: 75 x 75 x 135 mm (itolcg) and 76 x 76 x 127 mm (lugwcz), upright on the floor (z 0.06-0.07), from asset metadata bbox_size at scale 1.0. No dimension fits the 44 mm assisted-grasp span. Yet zs_pt50 binned all three on 311, so the cans can be held; how (friction without assisted-grasp registration) is unverified.
- Trash can wkxtxh: 230 x 230 x 279 mm body. It is grasped by the rim wall in the demos; rim thickness is unverified.
- Floor pickups need a low trunk pose. A knocked-over can rolls; re-locate it before re-grasping.
- Cans are spread up to 3.9 m apart in the living room. Plan the visiting order by nearest can.
- Closed-loop on 311: zs_pt50 1.0, ft24k 0.67, pt0 0.67, ft40k 0.0, ft10k 0.0. The zero-shot checkpoint beats the fine-tunes here; one rollout each, so treat as weak evidence.

### Hints for the VLM

- Cans of soda: small upright cylinders on the living-room floor, 3 of them (two itolcg, one lugwcz, different labels). No other cans in the loaded rooms.
- Trash can: one ~23 cm wide, ~28 cm tall open bin on the kitchen floor. Its position moves up to 6.3 m between instances; search the kitchen floor first.
- The robot starts in the kitchen (BDDL `ontop agent floor_2`; not checked against instance robot poses).
- Done per can: the can is not in the gripper, not on the floor, and not visible above the rim; depth inside the bin shows it.
- Done overall: episode ends by itself on success. If it has not, count cans on the floor.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside can__of__soda.n.01_3 ashcan.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_1 ashcan.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_2 ashcan.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?can__of__soda.n.01 - can__of__soda.n.01) 
                (inside ?can__of__soda.n.01 ?ashcan.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `ashcan.n.01_1` | trash_can_116 | trash_can / wkxtxh | kitchen_0 | floor, z 0.13 | 3.07 m (range 1.31-5.36) | yes, spread 6.32 m |
| `can__of__soda.n.01_1` | can_of_soda_115 | can_of_soda / itolcg | living_room_0 | floor, z 0.07 | 3.74 m (range 0.84-5.91) | yes, spread 4.94 m |
| `can__of__soda.n.01_2` | can_of_soda_114 | can_of_soda / itolcg | living_room_0 | floor, z 0.07 | 3.8 m (range 1.49-6.48) | yes, spread 4.21 m |
| `can__of__soda.n.01_3` | can_of_soda_113 | can_of_soda / lugwcz | living_room_0 | floor, z 0.06 | 3.67 m (range 0.99-5.71) | yes, spread 4.66 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 3.6 m (range 2.5-5.61) | no (fixed) |
| `floor.n.01_2` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.15 m (range 0.98-2.94) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom floor.n.01_2 kitchen)
(ontop agent.n.01_1 floor.n.01_2)
(ontop ashcan.n.01_1 floor.n.01_2)
(ontop can__of__soda.n.01_1 floor.n.01_1)
(ontop can__of__soda.n.01_2 floor.n.01_1)
(ontop can__of__soda.n.01_3 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_2)
(touching ashcan.n.01_1 floor.n.01_2)
(touching can__of__soda.n.01_1 floor.n.01_1)
(touching can__of__soda.n.01_2 floor.n.01_1)
(touching can__of__soda.n.01_3 floor.n.01_1)
(touching floor.n.01_1 can__of__soda.n.01_1)
(touching floor.n.01_1 can__of__soda.n.01_2)
(touching floor.n.01_1 can__of__soda.n.01_3)
(touching floor.n.01_2 agent.n.01_1)
(touching floor.n.01_2 ashcan.n.01_1)
```

## What the human demos did

200 annotated demos. Length 164.85 s (range 54.0-404.0). Skills per demo 12.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x4, pick up from x4, place in x3, place on x1.

Representative demo `episode_00012890.json` (165.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the trash can` (2.4-48.6 s)
2. `pick up the trash can from the floors` (48.6-62.3 s)
3. `move to the can of soda` (62.3-91.0 s)
4. `pick up the can of soda from the floors` (91.0-104.9 s)
5. `place the can of soda in the trash can` (104.9-110.6 s)
6. `move to the can of soda` (110.6-119.0 s)
7. `pick up the can of soda from the floors` (119.0-130.9 s)
8. `place the can of soda in the trash can` (131.0-138.6 s)
9. `move to the can of soda` (138.6-145.5 s)
10. `pick up the can of soda from the floors` (145.5-154.6 s)
11. `place the can of soda in the trash can` (154.7-159.6 s)
12. `place the trash can on the floors` (159.6-167.6 s)

Mean duration per skill in this task: move to 13.7 s, pick up from 16.3 s, place in 7.5 s, place on 12.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the can of soda` | 600 |
| `pick up the can of soda from the floors` | 595 |
| `place the can of soda in the trash can` | 595 |
| `move to the trash can` | 200 |
| `pick up the trash can from the floors` | 200 |
| `place the trash can on the floors` | 198 |
| `place the can of soda in the floors` | 5 |
| `pick up the can of soda from the trash can` | 4 |
| `place the can of soda on the trash can` | 1 |
| `place the can of soda on the floors` | 1 |
| `pick up the can of soda from the can of soda` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/01_picking_up_trash.json`. Planner notes: `task_docs/notes/01_picking_up_trash.md`.
