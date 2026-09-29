# 82 · Store Batteries

Task name `store_batteries`, task index 82.

> Put all of the batteries into the bottom-cabinet drawer, then close the drawer.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | kitchen, living_room |
| rooms loaded | bedroom_0, entryway_0, kitchen_0, living_room_0 |
| human demo length | 256.8 s mean (7704 steps) |
| episode time limit | 385.2 s (11556 steps at 30 Hz) |
| human base travel | 14.1564 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/jMSkFQy95FY |

## Planner notes

**Tier:** B — three batteries (34 x 35 x 61 mm) fit the jaws, but one sits on a high counter behind bar chairs and the target is a cabinet drawer.

### Goal in plain words

All three batteries must be inside one bottom cabinet in the living room; either of the two living-room bottom cabinets counts (`exists`). The goal has **no** `not open` literal, so the drawer may be left open. Nothing else is checked.

### Q traps

- Three literals, each 1/3. None is true at reset. All must be in the same cabinet.
- The task sentence says "then close the drawer", but closing is not a goal literal.
- `inside` tests the battery's AABB centre against the cabinet's fillable volume (PREDICATES §3). Whether an open drawer carries its own volume is not verified. If only the carcass has one, a battery in a pulled-out drawer counts only after the drawer is shut. Closing is cheap (~7 s), so close it anyway.
- Closing the drawer can push a battery that sits near its front edge out of the volume; drop batteries toward the back.
- Every door and drawer of both cabinets starts closed (joint_pos 0 in all 20 instances).

### Minimal plan

1. `move to the battery` — two batteries on the coffee table in view. ~14 s.
2. `pick up the battery from the coffee table` twice, one per hand — both grippers stopped short of closed. ~16 s each.
3. `move to the bottom cabinet` — cabinet front in view. ~14 s.
4. `open the drawer of the bottom cabinet` — drawer visibly pulled out. ~11 s.
5. `place the battery in the bottom cabinet` twice — both batteries in the drawer. ~9 s each.
6. `move to the chair` / `pick up the chair from the floors` / `move to the floors` / `place the chair on the floors` — only if a bar chair blocks the counter. ~50 s.
7. `move to the battery` then `pick up the battery from the countertop` — third battery in hand. ~14 s + 16 s.
8. `move to the bottom cabinet`, `place the battery in the bottom cabinet` — third battery in the drawer. ~23 s.
9. `close the drawer of the bottom cabinet` — drawer flush. ~7 s.

Budget: 385 s limit vs 257 s demo mean.

### What the demos do differently

- 62% of demos fetch the countertop battery first, then the two coffee-table batteries together.
- 392 chair segments in 200 demos: humans move a bar chair away from the counter and later put a chair back. Putting it back is not needed.
- `move to the floors` / `place the chair on the floors` are the demo words for parking the chair.

### Hard parts and hacks

- The countertop battery sits at z 1.11 m on the kitchen-living counter `countertop_tpuwys_0`. Two straight chairs stand at (-0.4, 1.1) and (-1.26, 1.1), in front of the counter (y 1.53) where the battery lies. Reaching over them is the hard step.
- Target choice: `bottom_cabinet_jhymlr_0` (1.65 m wide, 6 openable links, 1.0-2.6 m from start) or `bottom_cabinet_bamfsz_1` (0.42 m wide, 4 links, 1.7-3.7 m). Which link is a drawer is not verified. The demos call both "the bottom cabinet".
- Opening a drawer needs its handle; handle width vs 44 mm is not verified.
- Hack: the coffee table is 1.5 m from `bamfsz_1` and 2.2 m from `jhymlr_0`. Carrying both coffee-table batteries at once saves a round trip.

### Hints for the VLM

- Scene Rs_int. Two batteries lie on the low coffee table in front of the sofa. The third is on the high kitchen counter that divides the kitchen from the living room.
- Two more bottom cabinets stand in the kitchen, one in the entryway and one in the bedroom. They are not in the task scope and do not count.
- Done: all three batteries in the same living-room cabinet, drawer closed.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside battery.n.02_2 cabinet.n.01_2)` | no | yes |
| `(inside battery.n.02_1 cabinet.n.01_2)` | no | yes |
| `(inside battery.n.02_3 cabinet.n.01_2)` | no | yes |

The goal has 2 ground options (3 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists 
                (?cabinet.n.01 - cabinet.n.01)
                (forall 
                    (?battery.n.02 - battery.n.02)
                    (inside ?battery.n.02 ?cabinet.n.01)
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
| `battery.n.02_1` | battery_74 | battery / dcjyzg | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.26 m (range 0.8-2.03) | yes, spread 1.17 m |
| `battery.n.02_2` | battery_73 | battery / dcjyzg | living_room_0 | low (0.25-0.6 m), z 0.43 | 1.19 m (range 0.82-2.13) | yes, spread 0.94 m |
| `battery.n.02_3` | battery_72 | battery / dcjyzg | kitchen_0, living_room_0 | high (1.1-1.6 m), z 1.11 | 3.1 m (range 1.42-4.79) | yes, spread 1.74 m |
| `coffee_table.n.01_1` | coffee_table_fqluyq_0 | coffee_table / fqluyq | living_room_0 | low (0.25-0.6 m), z 0.26 | 1.25 m (range 0.86-2.22) | no |
| `cabinet.n.01_1` | bottom_cabinet_jhymlr_0 | bottom_cabinet / jhymlr | living_room_0 | low (0.25-0.6 m), z 0.38 | 1.49 m (range 0.99-2.56) | no (fixed) |
| `cabinet.n.01_2` | bottom_cabinet_bamfsz_1 | bottom_cabinet / bamfsz | living_room_0 | low (0.25-0.6 m), z 0.38 | 2.43 m (range 1.69-3.69) | no (fixed) |
| `countertop.n.01_1` | countertop_tpuwys_0 | countertop / tpuwys | kitchen_0, living_room_0 | table/counter (0.6-1.1 m), z 1.06 | 2.98 m (range 1.36-4.76) | no (fixed) |
| `floor.n.01_1` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.0 m (range 0.45-1.91) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom",
  "entryway",
  "kitchen",
  "living_room"
 ],
 "Rs_int": {
  "whitelist": {
   "battery.n.02": {
    "battery": {
     "dcjyzg": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 living_room)
(inroom cabinet.n.01_2 living_room)
(inroom coffee_table.n.01_1 living_room)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop battery.n.02_1 coffee_table.n.01_1)
(ontop battery.n.02_2 coffee_table.n.01_1)
(ontop battery.n.02_3 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching battery.n.02_1 coffee_table.n.01_1)
(touching battery.n.02_2 coffee_table.n.01_1)
(touching battery.n.02_3 countertop.n.01_1)
(touching coffee_table.n.01_1 battery.n.02_1)
(touching coffee_table.n.01_1 battery.n.02_2)
(touching countertop.n.01_1 battery.n.02_3)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 267.32 s (range 149.3-359.67). Skills per demo 20.0 (range 16-21). 4 distinct skill orders; the most common one covers 62% of demos.

Most common skill counts per demo (62% of demos): move to x8, pick up from x5, place in x3, place on x2, close drawer x1, open drawer x1.

Representative demo `episode_00820570.json` (256.8 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the chair` (0.0-19.0 s)
2. `pick up the chair from the floors` (19.0-33.6 s)
3. `move to the floors` (33.6-42.4 s)
4. `place the chair on the floors` (42.4-47.1 s)
5. `move to the battery` (47.1-58.0 s)
6. `pick up the battery from the countertop` (58.0-75.0 s)
7. `move to the bottom cabinet` (75.0-86.0 s)
8. `open the drawer of the bottom cabinet` (86.0-96.1 s)
9. `place the battery in the bottom cabinet` (96.1-106.0 s)
10. `move to the chair` (106.0-124.0 s)
11. `pick up the chair from the floors` (124.0-137.0 s)
12. `move to the countertop` (137.0-145.1 s)
13. `place the chair on the floors` (145.1-150.0 s)
14. `move to the battery` (150.0-173.0 s)
15. `pick up the battery from the coffee table` (173.0-190.6 s)
16. `pick up the battery from the coffee table` (190.6-207.0 s)
17. `move to the bottom cabinet` (207.0-221.0 s)
18. `place the battery in the bottom cabinet` (221.0-237.0 s)
19. `place the battery in the bottom cabinet` (237.0-249.0 s)
20. `close the drawer of the bottom cabinet` (249.0-256.8 s)

Mean duration per skill in this task: close drawer 7.3 s, move to 14.2 s, open drawer 10.9 s, pick up from 15.8 s, place in 9.0 s, place on 7.3 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the battery in the bottom cabinet` | 600 |
| `move to the bottom cabinet` | 400 |
| `pick up the battery from the coffee table` | 400 |
| `move to the chair` | 393 |
| `pick up the chair from the floors` | 392 |
| `place the chair on the floors` | 392 |
| `move to the battery` | 308 |
| `pick up the battery from the countertop` | 200 |
| `open the drawer of the bottom cabinet` | 200 |
| `close the drawer of the bottom cabinet` | 200 |
| `move to the floors` | 199 |
| `move to the countertop` | 192 |
| `move to the coffee table` | 160 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/82_store_batteries.json`. Planner notes: `task_docs/notes/82_store_batteries.md`.
