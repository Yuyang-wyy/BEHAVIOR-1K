# 87 · Collecting Aluminum Cans

Task name `collecting_aluminum_cans`, task index 87.

> Collect all of the soda cans and put them into the ice bucket.

## At a glance

| item | value |
| --- | --- |
| scene | `hotel_suite_large` |
| rooms in the goal | bedroom |
| rooms loaded | bathroom_0, bedroom_0 |
| human demo length | 340.1 s mean (10202 steps) |
| episode time limit | 510.1 s (15304 steps at 30 Hz) |
| human base travel | 18.5138 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/QRgCjhEdNzA |

## Planner notes

**Tier:** C — six pick-and-places into one ice bucket, but every can is 63-81 mm across (asset bboxes), wider than the 44 mm jaw span.

### Goal in plain words

All six soda cans must be inside the ice bucket. Three start on a bed and three on the bedroom floor. The cans are interchangeable. The bucket may be moved. Nothing else is checked.

### Q traps

- Six literals, each 1/6, all false at reset. Every can banks 1/6 independently.
- `inside` tests only the can's AABB centre against the bucket's fillable volume (PREDICATES §3). A can wedged upright on the rim does not count.
- The bucket (`ice_bucket/vlurir`, 0.34 x 0.41 x 0.39 m) is a single link. Knocking it over spills cans already scored; every literal is read at the final step.
- Six cans of 0.11-0.15 m height in a 0.34 x 0.41 m bucket: they fit side by side or stacked, but a late can can land on top of others with its centre above the rim (derived; inner volume not verified).

### Minimal plan

1. `move to the can of soda` then `pick up the can of soda from the floors` — can in one hand. ~18 s + 19 s.
2. `move to the can of soda` then `pick up the can of soda from the floors` (or `from the bed`) — second can in the other hand. ~18 s + 19 s.
3. `move to the ice bucket` — bucket in view at close range. ~18 s.
4. `place the can of soda in the ice bucket` twice — both cans dropped in, none on the rim. ~15 s each.
5. Repeat 1-4 twice more for the remaining four cans.

Budget: 510 s limit vs 340 s demo mean. Each two-can trip is about 110 s of skills.

### What the demos do differently

- 74% of demos follow the plan above: two cans per trip, three trips.
- No demo moves the bucket.

### Hard parts and hacks

- Grasp widths (asset bboxes, 6 different models): 0.063 x 0.063 x 0.114 m up to 0.081 x 0.081 x 0.130 m. No can fits the 44 mm span. Expect the grasp to fail unless the pull tab or rim registers; not verified.
- Three cans stand on `bed_kddswt_1` (top about 0.6 m); three stand on the floor (full trunk bend).
- The bucket starts on the floor, 0.9-5.6 m from the start, and moves up to 6.6 m between instances. Some floor cans start within 0.3 m of it (for example instance 304).
- Hack (unverified): pushing the bucket next to the floor cans shortens every trip; the bucket is too wide to grasp (no axis under 0.33 m).

### Hints for the VLM

- Scene hotel_suite_large, bedroom_0. Two beds; only the bed at y -0.29 (`bed_kddswt_1`) holds cans. The six cans are six different can models, so they look different.
- The ice bucket is the only bucket in the room.
- Done per literal: can visibly inside the bucket, top below the rim.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside can__of__soda.n.01_4 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_6 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_5 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_3 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_1 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_2 bucket.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?can__of__soda.n.01 - can__of__soda.n.01) 
                (inside ?can__of__soda.n.01 ?bucket.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `can__of__soda.n.01_1` | can_of_soda_48 | can_of_soda / itolcg | bedroom_0 | low (0.25-0.6 m), z 0.57 | 2.11 m (range 1.0-4.2) | yes, spread 2.25 m |
| `can__of__soda.n.01_2` | can_of_soda_47 | can_of_soda / opivig | bedroom_0 | low (0.25-0.6 m), z 0.56 | 2.04 m (range 1.11-4.33) | yes, spread 2.12 m |
| `can__of__soda.n.01_3` | can_of_soda_46 | can_of_soda / frewxk | bedroom_0 | low (0.25-0.6 m), z 0.57 | 2.13 m (range 0.97-4.22) | yes, spread 2.15 m |
| `can__of__soda.n.01_4` | can_of_soda_45 | can_of_soda / xmjfcg | bedroom_0 | floor, z 0.07 | 2.58 m (range 0.62-6.81) | yes, spread 7.58 m |
| `can__of__soda.n.01_5` | can_of_soda_44 | can_of_soda / bfrzvk | bedroom_0 | floor, z 0.06 | 3.15 m (range 0.63-6.6) | yes, spread 7.49 m |
| `can__of__soda.n.01_6` | can_of_soda_43 | can_of_soda / evcxlr | bedroom_0 | floor, z 0.06 | 3.97 m (range 0.58-6.44) | yes, spread 7.92 m |
| `bed.n.01_1` | bed_kddswt_1 | bed / kddswt | bedroom_0 | floor, z 0.18 | 2.33 m (range 1.6-4.01) | no (fixed) |
| `floor.n.01_1` | floors_nwjrkc_0 | floors / nwjrkc | bedroom_0 | floor, z -0.14 | 3.07 m (range 1.47-3.57) | no (fixed) |
| `bucket.n.01_1` | ice_bucket_42 | ice_bucket / vlurir | bedroom_0 | floor, z 0.19 | 3.24 m (range 0.92-5.55) | yes, spread 6.64 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom"
 ],
 "hotel_suite_large": {
  "whitelist": {
   "bucket.n.01": {
    "ice_bucket": {
     "vlurir": null
    }
   },
   "can__of__soda.n.01": {
    "can_of_soda": {
     "bfrzvk": null,
     "evcxlr": null,
     "frewxk": null,
     "itolcg": null,
     "opivig": null,
     "xmjfcg": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 bedroom)
(inroom floor.n.01_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bucket.n.01_1 floor.n.01_1)
(ontop can__of__soda.n.01_1 bed.n.01_1)
(ontop can__of__soda.n.01_2 bed.n.01_1)
(ontop can__of__soda.n.01_3 bed.n.01_1)
(ontop can__of__soda.n.01_4 floor.n.01_1)
(ontop can__of__soda.n.01_5 floor.n.01_1)
(ontop can__of__soda.n.01_6 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 can__of__soda.n.01_1)
(touching bed.n.01_1 can__of__soda.n.01_2)
(touching bed.n.01_1 can__of__soda.n.01_3)
(touching bucket.n.01_1 floor.n.01_1)
(touching can__of__soda.n.01_1 bed.n.01_1)
(touching can__of__soda.n.01_2 bed.n.01_1)
(touching can__of__soda.n.01_3 bed.n.01_1)
(touching can__of__soda.n.01_4 floor.n.01_1)
(touching can__of__soda.n.01_5 floor.n.01_1)
(touching can__of__soda.n.01_6 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 bucket.n.01_1)
(touching floor.n.01_1 can__of__soda.n.01_4)
(touching floor.n.01_1 can__of__soda.n.01_5)
(touching floor.n.01_1 can__of__soda.n.01_6)
```

## What the human demos did

200 annotated demos. Length 327.5 s (range 197.17-518.57). Skills per demo 20.0 (range 18-21). 12 distinct skill orders; the most common one covers 74% of demos.

Most common skill counts per demo (76% of demos): move to x8, pick up from x6, place in x6.

Representative demo `episode_00871520.json` (329.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the can of soda` (0.0-10.0 s)
2. `pick up the can of soda from the floors` (10.0-24.0 s)
3. `move to the can of soda` (24.0-40.2 s)
4. `pick up the can of soda from the floors` (40.2-63.0 s)
5. `move to the ice bucket` (63.0-77.7 s)
6. `place the can of soda in the ice bucket` (77.7-95.0 s)
7. `place the can of soda in the ice bucket` (95.0-116.0 s)
8. `move to the can of soda` (116.0-142.0 s)
9. `pick up the can of soda from the floors` (142.0-160.1 s)
10. `move to the can of soda` (160.1-170.4 s)
11. `pick up the can of soda from the bed` (170.4-179.3 s)
12. `move to the ice bucket` (179.3-200.8 s)
13. `place the can of soda in the ice bucket` (200.8-212.6 s)
14. `place the can of soda in the ice bucket` (212.6-225.0 s)
15. `move to the can of soda` (225.0-259.0 s)
16. `pick up the can of soda from the bed` (259.0-269.0 s)
17. `pick up the can of soda from the bed` (269.0-278.4 s)
18. `move to the ice bucket` (278.4-303.0 s)
19. `place the can of soda in the ice bucket` (303.0-316.0 s)
20. `place the can of soda in the ice bucket` (316.0-329.0 s)

Mean duration per skill in this task: move to 17.8 s, pick up from 18.8 s, place in 14.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the can of soda in the ice bucket` | 1200 |
| `move to the can of soda` | 978 |
| `pick up the can of soda from the bed` | 602 |
| `pick up the can of soda from the floors` | 599 |
| `move to the ice bucket` | 593 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/87_collecting_aluminum_cans.json`. Planner notes: `task_docs/notes/87_collecting_aluminum_cans.md`.
