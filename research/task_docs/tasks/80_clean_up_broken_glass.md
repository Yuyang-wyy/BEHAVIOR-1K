# 80 · Clean Up Broken Glass

Task name `clean_up_broken_glass`, task index 80.

> Pick up all of the broken glass pieces and put them into the trash can.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | corridor, dining_room |
| rooms loaded | dining_room_0, corridor_0, bar_0, kitchen_0, bathroom_0 |
| human demo length | 289.7 s mean (8691 steps) |
| episode time limit | 434.6 s (13037 steps at 30 Hz) |
| human base travel | 29.1154 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/qXliGIYzh2w |

## Planner notes

**Tier:** C — three floor picks carried about 10 m to one trash can, and two of the three shards have no bbox axis under 44 mm.

### Goal in plain words

All three broken-glass pieces must end inside the single trash can in the corridor. The pieces are interchangeable and any order works. The trash can may be moved. Nothing else is checked.

### Q traps

- Three literals, each worth 1/3. None is true at reset.
- `inside` tests only the shard's AABB centre against the can's fillable volume (PREDICATES §3). A shard caught on the rim does not count.
- Knocking the can over moves its volume and can spill shards already in it. Every literal is read at the final step only.
- The can (`trash_can/cjmezk`) has a single link, so no lid to open (asset metadata).

### Minimal plan

1. `move to the broken glass` — a shard on the floor in view. ~31 s.
2. `pick up the broken glass from the floors` — shard off the floor, gripper stopped short of closed. ~28 s.
3. `move to the broken glass` then `pick up the broken glass from the floors` with the other hand — second shard held. ~31 s + 28 s.
4. `move to the trash can` — can in view at close range. ~31 s.
5. `place the broken glass in the trash can` twice — shards no longer visible in either gripper and not on the rim. ~17 s each.
6. `move to the broken glass`, `pick up the broken glass from the floors`, `move to the trash can`, `place the broken glass in the trash can` — third shard. ~107 s.

Budget: 435 s limit vs 290 s demo mean. The plan above is the demo plan (90% of demos), and the walk dominates.

### What the demos do differently

- 90% of demos use exactly this order: two shards, one trip, then the third.
- No demo moves the trash can closer.

### Hard parts and hacks

- Grasp: shard `rvpgpt` (2 of the 3 pieces) has asset bbox 0.051 x 0.122 x 0.047 m; `beltgg` is 0.066 x 0.066 x 0.044 m. No axis of `rvpgpt` is under 44 mm. The real shard may be thinner than its bbox, but that is not verified. Expect grasp retries.
- The shards lie flat on the floor (z 0.01-0.02), so each pick needs a full trunk bend.
- Distances: shards spread over the whole dining room (0.25-10 m from the start); the can stands in corridor_0, 2.8-12.2 m from the start.
- Hack (unverified): the can is 0.38 m wide with no handle, so carrying it to the shards is unlikely to work. Carry two shards per trip instead, as the demos do.
- The dining room is cluttered: 8 benches, 4 booths, 7 chairs and 6 stools. Small flat shards are easy to lose behind furniture legs.

### Hints for the VLM

- Scene restaurant_diner. The shards are small glass pieces on the dining-room floor. There is only one trash can in dining_room_0 and corridor_0 together, standing on the corridor floor.
- The shards are 5-12 cm pieces lying flat on the floor; their rendered appearance was not checked.
- Done per literal: shard not visible on the floor and not on the rim, seen inside the can from above.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside broken__glass.n.01_2 ashcan.n.01_1)` | no | yes |
| `(inside broken__glass.n.01_1 ashcan.n.01_1)` | no | yes |
| `(inside broken__glass.n.01_3 ashcan.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?broken__glass.n.01 - broken__glass.n.01)
                (inside ?broken__glass.n.01 ?ashcan.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `broken__glass.n.01_1` | broken_glass_99 | broken_glass / rvpgpt | dining_room_0 | floor, z 0.02 | 2.44 m (range 0.7-9.98) | yes, spread 10.97 m |
| `broken__glass.n.01_2` | broken_glass_98 | broken_glass / beltgg | dining_room_0 | floor, z 0.01 | 3.56 m (range 1.12-9.24) | yes, spread 11.9 m |
| `broken__glass.n.01_3` | broken_glass_97 | broken_glass / rvpgpt | dining_room_0 | floor, z 0.02 | 4.68 m (range 0.25-10.0) | yes, spread 11.98 m |
| `floor.n.01_1` | floors_cxcxqq_0 | floors / cxcxqq | dining_room_0 | floor, z -0.0 | 3.63 m (range 1.42-5.12) | no (fixed) |
| `floor.n.01_2` | floors_fcxkki_0 | floors / fcxkki | corridor_0 | floor, z -0.15 | 10.51 m (range 2.61-12.21) | no (fixed) |
| `ashcan.n.01_1` | trash_can_96 | trash_can / cjmezk | corridor_0 | floor, z 0.2 | 10.51 m (range 2.81-12.18) | yes, spread 1.24 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "corridor",
  "dining_room"
 ],
 "restaurant_diner": {
  "whitelist": {
   "ashcan.n.01": {
    "trash_can": {
     "cjmezk": null
    }
   },
   "broken__glass.n.01": {
    "broken_glass": {
     "beltgg": null,
     "rvpgpt": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 dining_room)
(inroom floor.n.01_2 corridor)
(ontop agent.n.01_1 floor.n.01_1)
(ontop ashcan.n.01_1 floor.n.01_2)
(ontop broken__glass.n.01_1 floor.n.01_1)
(ontop broken__glass.n.01_2 floor.n.01_1)
(ontop broken__glass.n.01_3 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching ashcan.n.01_1 floor.n.01_2)
(touching broken__glass.n.01_1 floor.n.01_1)
(touching broken__glass.n.01_2 floor.n.01_1)
(touching broken__glass.n.01_3 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 broken__glass.n.01_1)
(touching floor.n.01_1 broken__glass.n.01_2)
(touching floor.n.01_1 broken__glass.n.01_3)
(touching floor.n.01_2 ashcan.n.01_1)
```

## What the human demos did

200 annotated demos. Length 284.77 s (range 151.6-467.37). Skills per demo 11.0 (range 10-12). 4 distinct skill orders; the most common one covers 90% of demos.

Most common skill counts per demo (90% of demos): move to x5, pick up from x3, place in x3.

Representative demo `episode_00802800.json` (284.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the broken glass` (0.0-10.0 s)
2. `pick up the broken glass from the floors` (10.0-32.2 s)
3. `move to the broken glass` (32.2-76.0 s)
4. `pick up the broken glass from the floors` (76.0-106.0 s)
5. `move to the trash can` (106.0-119.9 s)
6. `place the broken glass in the trash can` (119.9-129.0 s)
7. `place the broken glass in the trash can` (129.0-135.0 s)
8. `move to the broken glass` (135.0-187.0 s)
9. `pick up the broken glass from the floors` (187.0-206.0 s)
10. `move to the trash can` (206.0-269.5 s)
11. `place the broken glass in the trash can` (269.5-284.8 s)

Mean duration per skill in this task: move to 31.3 s, pick up from 27.5 s, place in 16.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the broken glass from the floors` | 600 |
| `place the broken glass in the trash can` | 600 |
| `move to the broken glass` | 591 |
| `move to the trash can` | 410 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/80_clean_up_broken_glass.json`. Planner notes: `task_docs/notes/80_clean_up_broken_glass.md`.
