# 84 · Tidying Bathroom

Task name `tidying_bathroom`, task index 84.

> Tidy the bathroom by putting the toilet tissue on the toilet, placing the tissue dispenser and soap dish on the countertop, putting the soap in the soap dish, and throwing the cork into the trash can.

## At a glance

| item | value |
| --- | --- |
| scene | `hotel_suite_large` |
| rooms in the goal | bathroom |
| rooms loaded | bathroom_0, bedroom_0 |
| human demo length | 433.4 s mean (13003 steps) |
| episode time limit | 650.2 s (19504 steps at 30 Hz) |
| human base travel | 19.012 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| starts open (joint_pos > 0.02) | `toilet.n.02_1` in 20/20 instances |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/EdKc0cKLITw |

## Planner notes

**Tier:** C — four independent pick-and-places, but only the cork (18 mm) fits the 44 mm jaws. The toilet roll, tissue dispenser and bar soap are all wider than 44 mm on every axis, and the toilet is behind a closed WC door.

### Goal in plain words

Four things must hold at the end: the bar soap rests on the soap dish, the tissue dispenser rests on the wall-mounted sink (the vanity counter, "countertop" in the demos), the toilet roll rests on the toilet, and the cork is inside the trash can. The soap dish itself is not in the goal and can stay where it starts, on the sink counter.

### Q traps

- Four literals, each 1/4, all false at reset. They are independent, so each one banks 0.25.
- The soap dish, bar soap and cork all start on the sink counter. Moving the soap dish (all 200 demos pick it up and re-place it) earns nothing.
- `ontop` fails when any part of the target object is directly above the placed object's centre (PREDICATES §4). On the sink, avoid the basin under the faucet; use the flat counter. The mirror above is a separate object and does not matter.
- On the toilet: one toilet joint starts at 0.524 rad (joint_pos in all 20 instances). Which part that is (seat or lid) is not verified. If a raised lid overhangs the seat, a roll on the seat fails; the tank top or a closed lid is safer (derived).
- Placing the bar soap can tip the light soap dish (0.032 m tall) off the counter. Re-check both at the end.
- The cork (0.018 x 0.018 x 0.034 m) is tiny. It must drop past the trash can's rim (can `dnvpag`, single link, no lid).

### Minimal plan

1. `move to the cork` then `pick up the cork from the countertop` — cork in hand. ~19 s + 26 s.
2. `move to the trash can` then `place the cork in the trash can` — cork gone from the gripper, not on the rim. ~19 s + 24 s.
3. `move to the bar soap` then `pick up the bar soap from the countertop`, then `place the bar soap on the soap dish` — soap sitting in the dish. ~19 + 26 + 23 s.
4. `move to the tissue dispenser`, `pick up the tissue dispenser from the floors`, `move to the countertop`, `place the tissue dispenser on the countertop` — box standing on the counter away from the basin. ~87 s.
5. `move to the door` then `open the door of the door` — WC door swung open. ~19 s + 16 s.
6. `move to the toilet tissue`, `pick up the toilet tissue from the floors`, `move to the toilet`, `place the toilet tissue on the toilet` — roll resting on the toilet. ~87 s.

Budget: 650 s limit vs 433 s demo mean. The plan puts the one easy grasp (cork) first.

### What the demos do differently

- 15 skill orders; the most common covers 30%. All 200 demos open the WC door and pick up and re-place the soap dish on the counter (not needed).
- `pick up the cork from the countertop` (189) is more common than `... from the wall mounted sink` (11). Use the countertop wording.
- The representative demo carries the roll and the dispenser together, one per hand, and opens the door with the roll still held.

### Hard parts and hacks

- Grasp widths (asset bboxes): toilet roll 0.094 x 0.092 x 0.115 m; dispenser 0.111 x 0.232 x 0.120 m; bar soap 0.113 x 0.089 x 0.061 m. None has an axis of 44 mm or less. Expect these grasps to fail; the cork is the only safe point.
- The toilet (`toilet_aapttl_0`, at (-1.33, 5.47)) sits behind `door_ydokma_0` at (-1.14, 4.96), closed at reset. A second door, `door_uptpdr_0`, is also closed and is not on the demo route.
- Opening the door needs its handle; handle width is not verified.

### Hints for the VLM

- Scene hotel_suite_large, bathroom_0. The long wall-mounted sink (2.57 m vanity with a mirror above) holds the soap dish, bar soap and cork at the start.
- The roll and the dispenser start on the floor anywhere in the bathroom, 0.6-3.4 m from the start. The trash can also moves between instances.
- Six shelves are in the bathroom; none is a target.
- Done: cork in the can; soap in the dish; dispenser on the vanity counter; roll on the toilet.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop bar_soap.n.01_1 soap_dish.n.01_1)` | no | yes |
| `(ontop tissue_dispenser.n.01_1 sink.n.01_1)` | no | yes |
| `(ontop toilet_tissue.n.01_1 toilet.n.02_1)` | no | yes |
| `(inside cork.n.04_1 ashcan.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (ontop ?bar_soap.n.01_1 ?soap_dish.n.01_1)
            (ontop ?tissue_dispenser.n.01_1 ?sink.n.01_1)
            (ontop ?toilet_tissue.n.01_1 ?toilet.n.02_1)
            (inside ?cork.n.04_1 ?ashcan.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `bar_soap.n.01_1` | bar_soap_46 | bar_soap / feqemg | bathroom_0 | table/counter (0.6-1.1 m), z 0.82 | 3.36 m (range 1.01-4.46) | yes, spread 2.38 m |
| `soap_dish.n.01_1` | soap_dish_45 | soap_dish / ownvqj | bathroom_0 | table/counter (0.6-1.1 m), z 0.81 | 3.32 m (range 1.49-4.58) | yes, spread 2.19 m |
| `tissue_dispenser.n.01_1` | tissue_dispenser_44 | tissue_dispenser / ypekre | bathroom_0 | floor, z 0.03 | 1.78 m (range 0.8-3.39) | yes, spread 5.1 m |
| `cork.n.04_1` | cork_43 | cork / ncxgpe | bathroom_0 | table/counter (0.6-1.1 m), z 0.81 | 3.17 m (range 0.8-4.4) | yes, spread 2.44 m |
| `toilet_tissue.n.01_1` | toilet_paper_42 | toilet_paper / phrpmu | bathroom_0 | floor, z 0.05 | 1.68 m (range 0.58-3.14) | yes, spread 4.77 m |
| `ashcan.n.01_1` | trash_can_41 | trash_can / dnvpag | bathroom_0 | floor, z 0.19 | 1.61 m (range 0.81-3.77) | yes, spread 4.4 m |
| `sink.n.01_1` | wall_mounted_sink_jbborl_0 | wall_mounted_sink / jbborl | bathroom_0 | table/counter (0.6-1.1 m), z 0.71 | 3.25 m (range 1.02-4.45) | no (fixed) |
| `toilet.n.02_1` | toilet_aapttl_0 | toilet / aapttl | bathroom_0 | low (0.25-0.6 m), z 0.37 | 1.8 m (range 1.34-3.01) | no (fixed) |
| `shelf.n.01_1` | shelf_rglkkf_0 | shelf / rglkkf | bathroom_0 | low (0.25-0.6 m), z 0.58 | 2.48 m (range 1.05-3.46) | no (fixed) |
| `floor.n.01_1` | floors_kudtlk_0 | floors / kudtlk | bathroom_0 | floor, z -0.14 | 0.99 m (range 0.17-1.94) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bathroom"
 ],
 "hotel_suite_large": {
  "whitelist": {
   "ashcan.n.01": {
    "trash_can": {
     "dnvpag": null
    }
   },
   "bar_soap.n.01": {
    "bar_soap": {
     "feqemg": null
    }
   },
   "cork.n.04": {
    "cork": {
     "ncxgpe": null
    }
   },
   "soap_dish.n.01": {
    "soap_dish": {
     "ownvqj": null
    }
   },
   "tissue_dispenser.n.01": {
    "tissue_dispenser": {
     "ypekre": null
    }
   },
   "toilet_tissue.n.01": {
    "toilet_paper": {
     "phrpmu": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 bathroom)
(inroom shelf.n.01_1 bathroom)
(inroom sink.n.01_1 bathroom)
(inroom toilet.n.02_1 bathroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop ashcan.n.01_1 floor.n.01_1)
(ontop bar_soap.n.01_1 sink.n.01_1)
(ontop cork.n.04_1 sink.n.01_1)
(ontop soap_dish.n.01_1 sink.n.01_1)
(ontop tissue_dispenser.n.01_1 floor.n.01_1)
(ontop toilet_tissue.n.01_1 floor.n.01_1)
(open toilet.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching ashcan.n.01_1 floor.n.01_1)
(touching bar_soap.n.01_1 sink.n.01_1)
(touching cork.n.04_1 sink.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 ashcan.n.01_1)
(touching floor.n.01_1 tissue_dispenser.n.01_1)
(touching floor.n.01_1 toilet_tissue.n.01_1)
(touching sink.n.01_1 bar_soap.n.01_1)
(touching sink.n.01_1 cork.n.04_1)
(touching sink.n.01_1 soap_dish.n.01_1)
(touching soap_dish.n.01_1 sink.n.01_1)
(touching tissue_dispenser.n.01_1 floor.n.01_1)
(touching toilet_tissue.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 394.78 s (range 290.17-692.2). Skills per demo 20.0 (range 18-21). 15 distinct skill orders; the most common one covers 30% of demos.

Most common skill counts per demo (44% of demos): move to x9, pick up from x5, place on x4, open door x1, place in x1.

Representative demo `episode_00840310.json` (394.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the toilet tissue` (0.0-9.0 s)
2. `pick up the toilet tissue from the floors` (9.0-30.0 s)
3. `move to the tissue dispenser` (30.0-50.0 s)
4. `pick up the tissue dispenser from the floors` (50.0-78.0 s)
5. `move to the countertop` (78.0-93.0 s)
6. `place the tissue dispenser on the countertop` (93.0-114.0 s)
7. `move to the door` (114.0-132.0 s)
8. `open the door of the door` (132.0-144.5 s)
9. `move to the toilet` (144.5-156.8 s)
10. `place the toilet tissue on the toilet` (156.8-177.0 s)
11. `move to the soap dish` (177.0-203.0 s)
12. `pick up the soap dish from the wall mounted sink` (203.0-223.9 s)
13. `pick up the bar soap from the countertop` (223.9-252.0 s)
14. `move to the countertop` (252.0-265.0 s)
15. `place the soap dish on the countertop` (265.0-281.0 s)
16. `place the bar soap on the soap dish` (281.0-300.0 s)
17. `move to the cork` (300.0-310.0 s)
18. `pick up the cork from the wall mounted sink` (310.0-328.0 s)
19. `move to the trash can` (328.0-346.0 s)
20. `place the cork in the trash can` (346.0-394.7 s)

Mean duration per skill in this task: move to 19.3 s, open door 15.5 s, pick up from 26.0 s, place in 24.3 s, place on 22.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the countertop` | 349 |
| `move to the toilet tissue` | 200 |
| `pick up the toilet tissue from the floors` | 200 |
| `pick up the tissue dispenser from the floors` | 200 |
| `place the tissue dispenser on the countertop` | 200 |
| `move to the door` | 200 |
| `open the door of the door` | 200 |
| `move to the toilet` | 200 |
| `place the toilet tissue on the toilet` | 200 |
| `place the soap dish on the countertop` | 200 |
| `place the cork in the trash can` | 200 |
| `place the bar soap on the soap dish` | 199 |
| `move to the soap dish` | 198 |
| `move to the trash can` | 198 |
| `move to the tissue dispenser` | 197 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/84_tidying_bathroom.json`. Planner notes: `task_docs/notes/84_tidying_bathroom.md`.
