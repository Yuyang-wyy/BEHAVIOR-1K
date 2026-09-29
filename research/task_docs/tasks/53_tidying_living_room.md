# 53 · Tidying Living Room

Task name `tidying_living_room`, task index 53.

> In the living room, place the potted plant on the coffee table and put the books and papers into the bookcase.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | living_room |
| rooms loaded | living_room_0 |
| human demo length | 418.9 s mean (12565 steps) |
| episode time limit | 628.3 s (18848 steps at 30 Hz) |
| human base travel | 20.6534 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 4 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://www.youtube.com/embed/aTCNKnjR03c |

## Planner notes

**Tier:** C. Nothing in the goal has an axis at or under the ~44 mm jaw span except by edge-grasping: the pot plant is 0.25 x 0.26 x 0.29 m and the hardback's thinnest axis is 47 mm (asset bbox, scale 1.0).

### Goal in plain words

- Four literals, none true at reset: pot plant on the coffee table, newspaper on the coffee table, notebook on the desk, hardback inside any one of the 4 bookcases.
- The task sentence is misleading: it says "put the books and papers into the bookcase", but the BDDL wants the newspaper on the coffee table and the notebook on the desk. Only the hardback goes in a bookcase.
- The 4 bookcases are interchangeable (4 ground options). There is one coffee table and one desk in the room.
- Nothing must stay closed. The only thing to avoid is stacking: an object resting on another object does not touch the table and fails `ontop`.

### Q traps

- No literal is true at reset (checked against `:init` and the 20 instances: newspaper and pot plant start on the floor, hardback and notebook start on the coffee table). Max Q = 1.0.
- Hardback and notebook start ON the coffee table. Put the newspaper and pot plant on free table area, not on top of them: stacked, they do not touch the table and `ontop` is False (PREDICATES §4).
- Do not put the pot plant on the newspaper for the same reason.
- `inside` bookcase uses one `openfillable` volume per bookcase of about 0.29 x 0.31 x 0.26 m, centred at z ~0.53 m (task_feasibility_probe on re_shelving_library_books 301, same bookcase model `otwukr` in the same scene). That is far smaller than the 0.30 x 0.76 x 1.05 m unit. Which cubby it covers is unverified; aim for a middle-row cubby (about 0.40-0.66 m high). A book on top of the bookcase or in a top or bottom cubby likely does not count.
- The coffee table is not fixed (`fixed: false`). Bumping it can shift or tip items already placed; placed items are scored only at the end.
- Closed loop on 311 got Q = 0.50 (2 of 4), which literals is not recorded.

### Minimal plan

Demo order already matches the goal; keep it. Times are demo means for this task.

1. `move to the newspaper` — base stopped with the newspaper (flat sheet on the floor) in view. ~21 s.
2. `pick up the newspaper from the floors` — gripper closed but not fully, sheet gone from the floor. ~35 s.
3. `move to the pot plant` — ~25 s.
4. `pick up the pot plant from the floors` (other arm) — pot lifted off the floor. ~38 s.
5. `move to the coffee table` — low glass-topped table in view. ~25 s.
6. `place the newspaper on the coffee table` — sheet lying flat on the glass, clear of the hardback and notebook. ~18 s.
7. `place the pot plant on the coffee table` — pot upright on bare glass, not on the newspaper. ~19 s.
8. `move to the hardback` — ~26 s.
9. `push the hardback to the coffee table` — hardback slid until it overhangs the table edge. ~28 s.
10. `pick up the hardback from the coffee table` — book no longer on the glass. ~23 s.
11. `move to the bookcase` — nearest white cubby unit in view. ~20 s.
12. `place the hardback in the bookcase` — book inside a middle-row cubby, gripper open and withdrawn. ~20 s.
13. `move to the notebook` — ~24 s.
14. `push the notebook to the coffee table` — notebook overhangs the edge. ~28 s.
15. `pick up the notebook from the coffee table` — ~21 s.
16. `move to the desk` — ~24 s.
17. `place the notebook on the desk` — notebook flat on the desk top. ~17 s.

Total ~400 s against a 628 s limit.

### What the demos do differently

- 52% of demos follow exactly the order above; 16 distinct orders in total.
- 88 of 200 demos add `hand over the hardback` before shelving it (about 15 s). The goal does not need it; it is a regrasp to get the book upright for the cubby.
- 6 demos use `insert the hardback into the bookcase` instead of `place ... in`. Prefer `place the hardback in the bookcase` (193 uses).
- The "push to the coffee table" steps are edge-overhang manoeuvres, not moves between furniture: the book already is on the coffee table.

### Hard parts and hacks

- Pot plant: 0.25 x 0.26 x 0.29 m, no thin axis in the bbox. Demos pick it from the floor every time (200/200), so some part (pot rim or stem) is graspable, but which part is unverified. Expect the most failed grasps here.
- Hardback `prifte`: 0.256 x 0.213 x 0.047 m. Its thickness is just over the 44 mm span; lying flat it cannot be straddled. The push-to-edge trick gives a finger access under the overhang; whether the 47 mm cover then registers is unverified.
- Notebook `ksxknp`: 0.068 x 0.110 x 0.014 m. Thin, so the edge-overhang grasp should work; 68 mm across is too wide for a top-down grasp.
- Newspaper: forced size 0.29 x 0.39 x 0.03 m, rigid (not cloth). Lying on the floor it has no graspable edge; demos take ~35 s for this pick.
- The coffee table is low (0.36 m tall bbox, glass top). Placing needs the trunk bent down.
- If the hardback grasp fails repeatedly, skip it: the other three literals give Q = 0.75.

### Hints for the VLM

- Single room, living_room_0, upstairs of `house_double_floor_upper`, with an open stair well and a glass railing. Do not drive into the stair well.
- Coffee table: low table with a dark glass top and a thin metal frame, in front of the beige sectional sofa.
- Desk: light wood top on a black metal frame, with a table lamp and a white chair, next to the stair railing.
- Bookcases: four identical white cube units (0.76 m wide, 1.05 m tall) standing in one row along a wall, reading as one long cubby wall.
- Pot plant: a potted plant on the floor. Newspaper: a flat rectangular sheet on the floor.
- Done looks like: glass table holding the plant and the newspaper side by side; desk holding the small notebook; a book standing or lying inside a middle cubby.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop pot_plant.n.01_1 coffee_table.n.01_1)` | no | yes |
| `(inside hardback.n.01_1 bookcase.n.01_3)` | no | yes |
| `(ontop newspaper.n.03_1 coffee_table.n.01_1)` | no | yes |
| `(ontop notebook.n.01_1 desk.n.01_1)` | no | yes |

The goal has 4 ground options (4 literals x4); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (ontop ?pot_plant.n.01_1 ?coffee_table.n.01_1)
            (exists
                (?bookcase.n.01 - bookcase.n.01)
                (inside ?hardback.n.01_1 ?bookcase.n.01)
            )
            (ontop ?newspaper.n.03_1 ?coffee_table.n.01_1)
            (ontop ?notebook.n.01_1 ?desk.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `pot_plant.n.01_1` | pot_plant_54 | pot_plant / jatssq | living_room_0 | floor, z 0.08 | 2.25 m (range 0.84-6.22) | yes, spread 7.5 m |
| `floor.n.01_1` | floors_rfqizg_0 | floors / rfqizg | living_room_0 | floor, z -0.15 | 2.75 m (range 1.69-4.0) | no (fixed) |
| `newspaper.n.03_1` | newspaper_53 | newspaper / ukamcl | living_room_0 | floor, z 0.01 | 2.06 m (range 0.82-5.7) | yes, spread 7.7 m |
| `hardback.n.01_1` | hardback_52 | hardback / prifte | living_room_0 | low (0.25-0.6 m), z 0.38 | 4.27 m (range 2.98-5.93) | yes, spread 1.22 m |
| `notebook.n.01_1` | notebook_51 | notebook / ksxknp | living_room_0 | low (0.25-0.6 m), z 0.36 | 4.33 m (range 3.15-5.95) | yes, spread 1.4 m |
| `coffee_table.n.01_1` | coffee_table_osroux_0 | coffee_table / osroux | living_room_0 | floor, z 0.17 | 4.26 m (range 3.07-5.73) | no |
| `desk.n.01_1` | desk_iotfzl_0 | desk / iotfzl | living_room_0 | table/counter (0.6-1.1 m), z 0.62 | 3.46 m (range 2.48-4.15) | no (fixed) |
| `bookcase.n.01_1` | bookcase_otwukr_1 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.87 m (range 2.59-5.61) | no (fixed) |
| `bookcase.n.01_2` | bookcase_otwukr_3 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 4.62 m (range 3.34-6.37) | no (fixed) |
| `bookcase.n.01_3` | bookcase_otwukr_2 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.13 m (range 1.84-4.85) | no (fixed) |
| `bookcase.n.01_4` | bookcase_otwukr_0 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 5.37 m (range 4.09-7.13) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "living_room"
 ],
 "house_double_floor_upper": {
  "whitelist": {
   "hardback.n.01": {
    "hardback": {
     "prifte": null
    }
   },
   "newspaper.n.03": {
    "newspaper": {
     "ukamcl": [
      0.29,
      0.39,
      0.03
     ]
    }
   },
   "notebook.n.01": {
    "notebook": {
     "ksxknp": null
    }
   },
   "pot_plant.n.01": {
    "pot_plant": {
     "jatssq": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom bookcase.n.01_1 living_room)
(inroom bookcase.n.01_2 living_room)
(inroom bookcase.n.01_3 living_room)
(inroom bookcase.n.01_4 living_room)
(inroom coffee_table.n.01_1 living_room)
(inroom desk.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop hardback.n.01_1 coffee_table.n.01_1)
(ontop newspaper.n.03_1 floor.n.01_1)
(ontop notebook.n.01_1 coffee_table.n.01_1)
(ontop pot_plant.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching coffee_table.n.01_1 hardback.n.01_1)
(touching coffee_table.n.01_1 notebook.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 newspaper.n.03_1)
(touching floor.n.01_1 pot_plant.n.01_1)
(touching hardback.n.01_1 coffee_table.n.01_1)
(touching newspaper.n.03_1 floor.n.01_1)
(touching notebook.n.01_1 coffee_table.n.01_1)
(touching pot_plant.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 394.15 s (range 255.03-669.7). Skills per demo 17.0 (range 16-20). 16 distinct skill orders; the most common one covers 52% of demos.

Most common skill counts per demo (52% of demos): move to x7, pick up from x4, place on x3, push to x2, place in x1.

Representative demo `episode_00532850.json` (413.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the newspaper` (0.0-35.0 s)
2. `pick up the newspaper from the floors` (35.0-72.0 s)
3. `move to the pot plant` (72.0-129.0 s)
4. `pick up the pot plant from the floors` (129.0-165.5 s)
5. `move to the coffee table` (165.5-188.4 s)
6. `place the newspaper on the coffee table` (188.4-199.9 s)
7. `place the pot plant on the coffee table` (199.9-210.0 s)
8. `move to the hardback` (210.0-241.0 s)
9. `push the hardback to the coffee table` (241.0-288.9 s)
10. `pick up the hardback from the coffee table` (288.9-308.0 s)
11. `move to the bookcase` (308.0-322.0 s)
12. `place the hardback in the bookcase` (322.0-339.9 s)
13. `move to the notebook` (339.9-349.7 s)
14. `push the notebook to the coffee table` (349.7-359.3 s)
15. `pick up the notebook from the coffee table` (359.3-376.9 s)
16. `move to the desk` (376.9-400.3 s)
17. `place the notebook on the desk` (400.3-413.0 s)

Mean duration per skill in this task: hand over 15.4 s, insert 17.4 s, move to 23.1 s, pick up from 29.2 s, place in 19.8 s, place on 17.8 s, push to 28.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bookcase` | 229 |
| `place the newspaper on the coffee table` | 204 |
| `move to the coffee table` | 202 |
| `move to the notebook` | 202 |
| `move to the newspaper` | 200 |
| `pick up the newspaper from the floors` | 200 |
| `move to the pot plant` | 200 |
| `pick up the pot plant from the floors` | 200 |
| `pick up the hardback from the coffee table` | 200 |
| `push the notebook to the coffee table` | 200 |
| `pick up the notebook from the coffee table` | 200 |
| `move to the desk` | 200 |
| `place the notebook on the desk` | 200 |
| `push the hardback to the coffee table` | 198 |
| `move to the hardback` | 197 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/53_tidying_living_room.json`. Planner notes: `task_docs/notes/53_tidying_living_room.md`.
