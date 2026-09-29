# 55 · Re Shelving Library Books

Task name `re_shelving_library_books`, task index 55.

> Put the library books and notebooks from the desk into the bookcase.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | living_room |
| rooms loaded | living_room_0 |
| human demo length | 317.6 s mean (9528 steps) |
| episode time limit | 476.4 s (14292 steps at 30 Hz) |
| human base travel | 19.6242 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 64 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/AQdhTrye7NQ |

## Planner notes

**Tier:** C. Three flat books (26-33 mm thick, 0.12-0.21 m across) lying on a desk; the only graspable axis is the thickness, which needs the push-to-edge overhang and usually a hand-over to fit the book into a small cubby. Closed loop scored Q = 0.00 on 311.

### Goal in plain words

- All three `book.n.02` objects must end inside any bookcase: hardback `aceozs` (0.198 x 0.149 x 0.026 m), notebook `aanuhi` (0.151 x 0.120 x 0.027 m), hardback `agbqsy` (0.213 x 0.169 x 0.033 m). Sizes are asset bbox at scale 1.0.
- Any book may go in any of the 4 bookcases (64 ground options). All three in the same cubby is fine.
- Nothing needs to be closed. Nothing is required to stay on the desk.

### Q traps

- No literal is true at reset; max Q = 1.0, 1/3 per book. Books start on the desk top (z 0.75) in all 20 instances.
- `inside` passes only if the book's AABB centre is inside the bookcase's `openfillable` volume (PREDICATES §3). The probe on instance 301 measured one volume per bookcase of about 0.29 x 0.31 x 0.26 m, centred at z ~0.53 m (TASK_AUDIT.md). The unit is 0.30 x 0.76 x 1.05 m, so the volume is one cubby-sized box, not the whole unit.
- Which cubby that box covers is unverified. It sits at the unit's mid-height (about 0.40-0.66 m), so aim for a middle-row cubby. A book on top of the bookcase (1.05 m) or in a top or bottom cubby most likely scores 0.
- A book resting half out of the cubby still counts if its centre is inside; one balanced on the front edge does not.

### Minimal plan

One book at a time, as all demos do. Times are demo means for this task.

1. `move to the notebook` (or `move to the hardback`) — base stopped facing the desk with the book in view. ~24 s.
2. `push the notebook to the desk` — book slid until part of it overhangs the desk edge. ~22 s.
3. `pick up the notebook from the desk` — gripper closed on the overhang, short of fully closed; book lifted off the desk. ~13 s.
4. `move to the bookcase` — white cube unit in view at close range. ~10 s.
5. `hand over the notebook` — book now held by the other hand in an orientation that fits the cubby. ~11 s.
6. `move to the bookcase` — small approach to face a middle-row cubby. ~10 s.
7. `insert the notebook into the bookcase` — book inside the cubby opening, gripper open and withdrawn. ~15 s.
8. Repeat 1-7 for each hardback with `move to the hardback`, `push the hardback to the desk`, `pick up the hardback from the desk`, `hand over the hardback`, `insert the hardback into the bookcase`.

About 105 s per book, ~320 s total against a 476 s limit.

### What the demos do differently

- 80% of demos follow exactly this 21-step order; 19 distinct orders.
- The hand-over appears in about 570 of 600 book transfers. It is a regrasp, not required by the goal; skip it only if the book is already held in a way that clears the cubby opening.
- Demos always use `insert ... into the bookcase`, never `place ... in`. Use `insert`.
- The two `move to the bookcase` steps around the hand-over are one approach split in two.

### Hard parts and hacks

- Grasp: lying flat, no book has a horizontal axis near 44 mm (smallest is 120 mm). Only the 26-33 mm thickness fits the jaws, which needs a finger under the book. The push-to-edge overhang is the enabling step; a top-down grasp on the flat book cannot work (PICK_PLACE_STATUS.md).
- The push must leave the book overhanging but not falling. A book that drops to the floor must be picked from the floor, which is harder still.
- Placement: the target volume is about 0.31 m wide and 0.26 m tall. A 0.21 m book held flat by its edge fits; a book held so that it sticks out towards the robot may collide with the cubby frame.
- No verified scripted pick exists for this task yet; three scripted attempts on a similar task achieved zero grasps.
- Partial credit is per book, so securing one book (Q = 0.33) beats spending the whole budget on retries.

### Hints for the VLM

- Single room, living_room_0 of `house_double_floor_upper` (the same room as tidying_living_room). Sloped ceiling, beige sectional sofa, glass coffee table, stair well with glass railing.
- Desk: light wood top on a black metal frame with wheels, with a table lamp and a white chair; the three books lie flat on it about 0.74 m high. The coffee table is not the target table (blacklisted for `table.n.02`).
- Bookcases: four identical white cube units in one row along the wall, 0.76 m apart, about 2.3 m from the desk. They read as one long cubby wall; any unit counts.
- Distractors: none of category hardback or notebook outside the three goal books.
- Done looks like: desk top empty of books; three books visible inside middle-row cubbies.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside book.n.02_3 bookcase.n.01_3)` | no | yes |
| `(inside book.n.02_2 bookcase.n.01_3)` | no | yes |
| `(inside book.n.02_1 bookcase.n.01_3)` | no | yes |

The goal has 64 ground options (3 literals x64); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?book.n.02 - book.n.02)
                (exists
                    (?bookcase.n.01 - bookcase.n.01)
                    (inside ?book.n.02 ?bookcase.n.01)
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
| `book.n.02_1` | hardback_53 | hardback / aceozs | living_room_0 | table/counter (0.6-1.1 m), z 0.75 | 3.5 m (range 1.56-4.36) | yes, spread 1.18 m |
| `book.n.02_2` | notebook_52 | notebook / aanuhi | living_room_0 | table/counter (0.6-1.1 m), z 0.75 | 3.4 m (range 2.28-4.81) | yes, spread 1.16 m |
| `book.n.02_3` | hardback_51 | hardback / agbqsy | living_room_0 | table/counter (0.6-1.1 m), z 0.75 | 3.57 m (range 2.1-4.68) | yes, spread 0.77 m |
| `table.n.02_1` | desk_iotfzl_0 | desk / iotfzl | living_room_0 | table/counter (0.6-1.1 m), z 0.62 | 3.29 m (range 1.99-4.4) | no (fixed) |
| `bookcase.n.01_1` | bookcase_otwukr_0 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 5.14 m (range 1.24-7.19) | no (fixed) |
| `bookcase.n.01_2` | bookcase_otwukr_1 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.66 m (range 0.96-5.69) | no (fixed) |
| `bookcase.n.01_3` | bookcase_otwukr_2 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 2.94 m (range 0.84-4.94) | no (fixed) |
| `bookcase.n.01_4` | bookcase_otwukr_3 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 4.39 m (range 1.02-6.44) | no (fixed) |
| `floor.n.01_1` | floors_rfqizg_0 | floors / rfqizg | living_room_0 | floor, z -0.15 | 2.83 m (range 0.92-4.23) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room"
 ],
 "house_double_floor_upper": {
  "whitelist": {
   "book.n.02": {
    "notebook": {
     "aanuhi": null
    },
    "hardback": {
     "aceozs": null,
     "agbqsy": null,
     "atxzzy": null
    }
   }
  },
  "blacklist": {
   "table.n.02": {
    "coffee_table": {
     "osroux": null
    }
   }
  }
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom bookcase.n.01_1 living_room)
(inroom bookcase.n.01_2 living_room)
(inroom bookcase.n.01_3 living_room)
(inroom bookcase.n.01_4 living_room)
(inroom floor.n.01_1 living_room)
(inroom table.n.02_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop book.n.02_1 table.n.02_1)
(ontop book.n.02_2 table.n.02_1)
(ontop book.n.02_3 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching book.n.02_1 table.n.02_1)
(touching book.n.02_2 table.n.02_1)
(touching book.n.02_3 table.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching table.n.02_1 book.n.02_1)
(touching table.n.02_1 book.n.02_2)
(touching table.n.02_1 book.n.02_3)
```

## What the human demos did

200 annotated demos. Length 321.48 s (range 165.4-475.7). Skills per demo 21.0 (range 17-22). 19 distinct skill orders; the most common one covers 80% of demos.

Most common skill counts per demo (80% of demos): move to x9, hand over x3, insert x3, pick up from x3, push to x3.

Representative demo `episode_00552620.json` (325.5 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the notebook` (0.0-30.0 s)
2. `push the notebook to the desk` (30.0-50.8 s)
3. `pick up the notebook from the desk` (50.8-64.0 s)
4. `move to the bookcase` (64.0-75.5 s)
5. `hand over the notebook` (75.5-89.1 s)
6. `move to the bookcase` (89.1-97.1 s)
7. `insert the notebook into the bookcase` (97.1-115.0 s)
8. `move to the hardback` (115.0-142.0 s)
9. `push the hardback to the desk` (142.0-157.1 s)
10. `pick up the hardback from the desk` (157.1-170.0 s)
11. `move to the bookcase` (170.0-187.3 s)
12. `hand over the hardback` (187.3-204.0 s)
13. `move to the bookcase` (204.0-209.9 s)
14. `insert the hardback into the bookcase` (209.9-223.0 s)
15. `move to the hardback` (223.0-241.9 s)
16. `push the hardback to the desk` (241.9-267.4 s)
17. `pick up the hardback from the desk` (267.4-276.0 s)
18. `move to the bookcase` (276.0-286.1 s)
19. `hand over the hardback` (286.1-298.0 s)
20. `move to the bookcase` (298.0-303.8 s)
21. `insert the hardback into the bookcase` (303.8-325.0 s)

Mean duration per skill in this task: hand over 11.9 s, insert 14.7 s, move to 15.2 s, pick up from 12.9 s, push to 22.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bookcase` | 1160 |
| `move to the hardback` | 400 |
| `pick up the hardback from the desk` | 400 |
| `insert the hardback into the bookcase` | 400 |
| `push the hardback to the desk` | 396 |
| `hand over the hardback` | 382 |
| `move to the notebook` | 200 |
| `push the notebook to the desk` | 200 |
| `pick up the notebook from the desk` | 200 |
| `insert the notebook into the bookcase` | 200 |
| `hand over the notebook` | 188 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/55_re_shelving_library_books.json`. Planner notes: `task_docs/notes/55_re_shelving_library_books.md`.
