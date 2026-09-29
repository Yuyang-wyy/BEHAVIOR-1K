# 16 · Moving Boxes To Storage

Task name `moving_boxes_to_storage`, task index 16.

> Move the two storage containers from the living room to the garage. In the garage, place one container on the floor and stack the other container on top of it (either order is fine).

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage, living_room |
| rooms loaded | corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 486.5 s mean (14596 steps) |
| episode time limit | 729.8 s (21894 steps at 30 Hz) |
| human base travel | 36.8051 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.50; ft40k@sulab1 Q=1.00 (success); ft40k@local Q=1.00 (success) |
| demo video | https://player.vimeo.com/video/1114058315 |

## Planner notes

**Tier:** C — two storage boxes of 0.40 x 0.41 x 0.21 m each must be carried ~9 m and stacked. No dimension is under the 44 mm span, yet ft40k succeeded on instance 311 (Q 1.0 in 14103 steps, 470 s), so the boxes are graspable in practice. How the grasp registers (across a box wall, or bimanual) is unverified.

### Goal in plain words

One storage box must rest on the garage floor and the other box must rest on top of it.
The two boxes are interchangeable: either can be the bottom one (2 ground options, Q takes the better).
Nothing has to be closed afterwards; the corridor door may stay open.

### Q traps

- 2 literals per option, both False at reset. Max partial Q is 1.0.
- One box on the garage floor alone gives Q = 0.5 (what zs_pt50 reached on 311).
- Both boxes side by side on the garage floor still gives only 0.5. The stack is the second half.
- `ontop top bottom` needs the top box's AABB-centre x-y over the bottom box and direct contact (PREDICATES §4). A top box hanging half off the edge, or tipped against the bottom box while touching the floor, can fail.
- The bottom box must be on the garage floor, not on the corridor floor or the threshold.
- Knocking the bottom box while placing the top one can shift it; re-check both after release.

### Minimal plan

The robot starts in the garage, 0.7-3.7 m from the garage floor centre. The boxes are on the living-room floor, 5.3-13.3 m away. The garage-corridor door `door_bexenl_0` starts closed (template joint_pos ~0); every demo opens it first.

1. `move to the door`, `open the door of the door` — door swung open, corridor visible. ~60 s + 24 s.
2. `move to the storage box` — first box centred in view on the living-room floor. ~60 s.
3. `pick up the storage box from the floors` — box lifted clear of the floor; depth shows the gap. ~42 s.
4. `move to the floors` — base stopped inside the garage, clear floor ahead. ~60 s.
5. `place the storage box on the floors` — box on the garage floor, grippers open. ~33 s. Scores 1/2.
6. `move to the storage box`, `pick up the storage box from the floors` — second box lifted. ~60 s + 42 s.
7. `move to the storage box` — base stopped facing the first box in the garage. ~60 s.
8. `place the storage box on the storage box` — top box centred on the bottom box, grippers open. ~33 s. Success ends the episode.

Budget: about 475 s against a 730 s limit. This plan is exactly the demo plan; there is nothing to cut.

### What the demos do differently

- All 200 demos follow this plan. 111 carry `storage_box_80` first, 89 carry `storage_box_79` first; either works.
- No push, hand-over or re-grasp segments are annotated.

### Hard parts and hacks

- The boxes are large for the R1Pro: 0.40 m square. Carrying one box through the corridor doorway (door width unknown) with arms extended risks collisions and tipping (robot can tip with loads held high).
- Placing the top box needs the box lowered to ~0.21 m above the floor and centred; a misaligned drop slides it off.
- The long carry is the main time sink. If the first trip overruns ~250 s, bank the 0.5 and keep going only if time remains.

### Hints for the VLM

- The two storage boxes are identical closed boxes on the living-room floor; there are no other storage boxes in the living room or garage.
- Besides the boxes, the living room has one coffee table, a sofa, a shelf, a bottom cabinet and a fireplace.
- The garage has a car (fixed, large). Put the boxes on open floor away from the car, near the corridor door to shorten the second trip.
- Done: bottom box flat on the garage floor, top box sitting squarely on it, both upright, grippers away.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop storage_container.n.01_1 floor.n.01_2)` | no | yes |
| `(ontop storage_container.n.01_2 storage_container.n.01_1)` | no | yes |

The goal has 2 ground options (2 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (or
                (and
                    (ontop ?storage_container.n.01_1 ?floor.n.01_2)
                    (ontop ?storage_container.n.01_2 ?storage_container.n.01_1)
                )
                (and
                    (ontop ?storage_container.n.01_2 ?floor.n.01_2)
                    (ontop ?storage_container.n.01_1 ?storage_container.n.01_2)
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
| `storage_container.n.01_1` | storage_box_80 | storage_box / izcglf | living_room_0 | floor, z 0.07 | 9.41 m (range 5.27-12.41) | yes, spread 4.36 m |
| `storage_container.n.01_2` | storage_box_79 | storage_box / izcglf | living_room_0 | floor, z 0.07 | 9.7 m (range 6.99-13.26) | yes, spread 3.83 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 8.84 m (range 6.53-11.67) | no (fixed) |
| `floor.n.01_2` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 2.52 m (range 0.67-3.65) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom floor.n.01_2 garage)
(ontop agent.n.01_1 floor.n.01_2)
(ontop storage_container.n.01_1 floor.n.01_1)
(ontop storage_container.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_2)
(touching floor.n.01_1 storage_container.n.01_1)
(touching floor.n.01_1 storage_container.n.01_2)
(touching floor.n.01_2 agent.n.01_1)
(touching storage_container.n.01_1 floor.n.01_1)
(touching storage_container.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 478.07 s (range 312.5-635.23). Skills per demo 10.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x5, pick up from x2, place on x2, open door x1.

Representative demo `episode_00161010.json` (478.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the door` (0.6-15.5 s)
2. `open the door of the door` (15.5-33.9 s)
3. `move to the storage box` (34.0-83.6 s)
4. `pick up the storage box from the floors` (83.6-127.4 s)
5. `move to the floors` (127.4-198.7 s)
6. `place the storage box on the floors` (198.7-227.6 s)
7. `move to the storage box` (242.8-312.6 s)
8. `pick up the storage box from the floors` (312.7-361.3 s)
9. `move to the storage box` (361.4-439.5 s)
10. `place the storage box on the storage box` (439.5-478.7 s)

Mean duration per skill in this task: move to 60.0 s, open door 24.0 s, pick up from 42.0 s, place on 33.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the storage box` | 600 |
| `pick up the storage box from the floors` | 400 |
| `place the storage box on the floors` | 201 |
| `move to the door` | 200 |
| `open the door of the door` | 200 |
| `move to the floors` | 200 |
| `place the storage box on the storage box` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/16_moving_boxes_to_storage.json`. Planner notes: `task_docs/notes/16_moving_boxes_to_storage.md`.
