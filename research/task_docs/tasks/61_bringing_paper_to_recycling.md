# 61 · Bringing Paper To Recycling

Task name `bringing_paper_to_recycling`, task index 61.

> Put the paper and newspaper into the recycling bin, then close the recycling bin.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden, kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 373.8 s mean (11214 steps) |
| episode time limit | 560.7 s (16821 steps at 30 Hz) |
| human base travel | 35.2436 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.667 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/5OU6Zq9bGG4 |

## Planner notes

**Tier:** C — two flat or bulky paper items carried 7-22 m through a closed door to a lidded bin in the garden, with a two-handed lid opening.

### Goal in plain words

- The paper bag (`sack.n.01_1`, a `paper_bag`) and the newspaper must both end with their centres inside the recycling bin.
- The recycling bin's lid must be closed at the end.
- One ground option, 3 literals. There is one recycling bin in the scene and no trash can, so there is no choice of container.
- Doors along the way are not in the goal; leaving them open costs nothing.

### Q traps

- `not open recycling_bin` is true at reset and never scores. Verified: the lid joint is ~0 (closed) in the template and in all 20 instance files. Max partial Q is therefore 2/3; full success needs the lid shut again.
- The lid must be within 5% of its range from closed (PREDICATES §6). A lid resting on a newspaper edge that sticks up stays "open" and costs the success.
- Close the lid only after both items are in. Opening the lid again does not remove credit, but it wastes ~30 s.
- `inside` checks the item's AABB centre in the bin volume (PREDICATES §3). An item that lands on the closed lid, or drapes over the rim, does not count.
- Partial Q reads the final state only. Items set on the garden floor near the bin score nothing.

### Minimal plan

1. `move to the newspaper` — newspaper on the kitchen bar in view; ~19 s.
2. `pick up the newspaper from the bar` — newspaper lifted clear of the bar; ~15 s.
3. `move to the paper bag` — ~19 s.
4. `pick up the paper bag from the floors` — bag off the floor in the other gripper; ~15 s.
5. `move to the door` — base stopped at the closed door to the garden; ~19 s (route length varies, see hints).
6. `open the door of the door` — door visibly swung open; ~11 s.
7. `move to the floors` — base in the garden near the bin; ~19 s or more (humans take ~45 s here).
8. `place the paper bag on the floors` — ~15 s.
9. `place the newspaper on the floors next to the paper bag` — both hands free; ~13 s.
10. `move to the recycling bin` — ~19 s.
11. `open the lid of the recycling bin` — lid visibly raised and staying up; ~30 s.
12. `move to the paper bag`, `pick up the paper bag from the floors` — ~34 s.
13. `move to the newspaper`, `pick up the newspaper from the floors` — ~34 s.
14. `move to the recycling bin`, `place the paper bag in the recycling bin` — bag no longer visible above the rim; ~32 s.
15. `place the newspaper in the recycling bin` — ~13 s.
16. `move to the recycling bin`, `close the lid of the recycling bin` — lid flat on the bin; ~28 s.

Demo mean is 374 s against a 560.7 s limit. Dropping the demo's `close the door of the door` (~23 s) is safe for the goal.

### What the demos do differently

- Every demo opens and then closes a door on the way out (`close the door of the door`, 22.7 s mean, mostly labelled as navigation). Only opening it is needed to pass; closing it is optional. Whether the "close" segment also covers driving through the doorway is unverified.
- Every demo sets both items on the garden floor before opening the lid; the lid opening is labelled bimanual ("coordinated") in all 200 demos.
- Humans carry both items in one trip, one per hand. Keep that: a second round trip costs 15-45 s of driving each way.

### Hard parts and hacks

- **Distance.** The bin is in garden_0, 6.7-21.6 m from the start (301-310: 16.6, 14.7, 14.0, 21.6, 6.7, 13.6, 21.3, 12.4, 18.0, 10.2 m). Instances 304 and 307 are the longest.
- **Doors.** All garden doors start closed (joint_pos 0 in the template): kitchen-garden door_vudhlc_2 at (7.71, 3.43), corridor-garden door_vudhlc_1 at (0.11, -1.19) and door_vudhlc_0 at (0.12, 7.76), living_room-garden door_vudhlc_3 at (4.7, 7.67). The bin is always at x -16 to 0, y -3 to 2. The door humans use is not recorded; door_vudhlc_1 opens nearest the bin (unverified as the demo route).
- **Opening a door while both hands hold paper** is what the demos do. If the VLA drops items here, set them down first.
- **Newspaper grasp.** Forced size 0.41 x 0.31 x 0.03 m, lying flat on the bar top (z ~0.9). The only dimension under 44 mm is the vertical 30 mm, so a jaw must get under an edge. Fallback: `push the newspaper to the bar` is a trained sentence in task 52 (slide it to overhang the edge); it has no demo in this task.
- **Paper bag grasp.** Forced size 0.15 x 0.225 x 0.36 m; only the thin wall at the rim fits the jaw (unverified).
- **Lid.** Bin asset `recycling_bin/pdmzhv` is 0.57 x 0.43 x 0.82 m. Lid opening averages 30 s and is bimanual in demos. The lid must stay up by itself while the items go in (unverified). Closing is a push and needs no grasp.
- Both closed-loop runs on 311 scored Q 0.00.

### Hints for the VLM

- Start in kitchen_0. The newspaper is always on the bar `bar_egwapq_0` (the kitchen has two bars; the newspaper's bar is at x ~8). The paper bag stands on the kitchen floor, 0.7-4.9 m from the start.
- The recycling bin is the only bin in the loaded rooms. It stands on a garden_0 floor patch (z 0.4 root), 0.57 x 0.43 x 0.82 m, with a lid.
- The garden is large (6 floor patches, 26 trees, 55 bushes); bring the bin into view before driving far.
- Done: neither item visible outside the bin, and the lid lying flat on the bin.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside sack.n.01_1 recycling_bin.n.01_1)` | no | yes |
| `(inside newspaper.n.03_1 recycling_bin.n.01_1)` | no | yes |
| `(not open recycling_bin.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
       	    (inside sack.n.01_1 ?recycling_bin.n.01_1)
       	    (inside newspaper.n.03_1 ?recycling_bin.n.01_1)
            (not
                (open ?recycling_bin.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `sack.n.01_1` | paper_bag_198 | paper_bag / bzsxgw | kitchen_0 | floor, z 0.16 | 2.45 m (range 0.71-4.87) | yes, spread 7.32 m |
| `newspaper.n.03_1` | newspaper_197 | newspaper / edarlp | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.51 m (range 1.32-6.64) | yes, spread 1.99 m |
| `recycling_bin.n.01_1` | recycling_bin_196 | recycling_bin / pdmzhv | garden_0 | low (0.25-0.6 m), z 0.4 | 14.73 m (range 6.68-21.6) | yes, spread 16.69 m |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 2.83 m (range 1.94-6.77) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 1.83 m (range 0.98-3.38) | no (fixed) |
| `floor.n.01_2` | floors_qadhjb_0 | floors / qadhjb | garden_0 | floor, z -0.15 | 14.53 m (range 11.32-15.7) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen",
  "garden"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "recycling_bin.n.01": {
    "recycling_bin": {
     "pdmzhv": null
    }
   },
   "sack.n.01": {
    "paper_bag": {
     "bzsxgw": [
      0.15,
      0.225,
      0.36
     ]
    }
   },
   "newspaper.n.03": {
    "newspaper": {
     "edarlp": [
      0.41,
      0.31,
      0.03
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom floor.n.01_2 garden)
(ontop agent.n.01_1 floor.n.01_1)
(ontop newspaper.n.03_1 countertop.n.01_1)
(ontop recycling_bin.n.01_1 floor.n.01_2)
(ontop sack.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 newspaper.n.03_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 sack.n.01_1)
(touching floor.n.01_2 recycling_bin.n.01_1)
(touching newspaper.n.03_1 countertop.n.01_1)
(touching recycling_bin.n.01_1 floor.n.01_2)
(touching sack.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 370.7 s (range 252.63-500.17). Skills per demo 22.0 (range 19-24). 36 distinct skill orders; the most common one covers 18% of demos.

Most common skill counts per demo (30% of demos): move to x11, pick up from x4, place in x2, close door x1, close lid x1, open door x1, open lid x1, place on x1, place on next to x1.

Representative demo `episode_00612380.json` (340.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the newspaper` (0.0-11.0 s)
2. `pick up the newspaper from the bar` (11.0-28.0 s)
3. `move to the paper bag` (28.0-37.0 s)
4. `pick up the paper bag from the floors` (37.0-50.0 s)
5. `move to the door` (50.0-100.4 s)
6. `open the door of the door` (100.4-106.0 s)
7. `close the door of the door` (106.0-121.8 s)
8. `move to the floors` (121.8-167.0 s)
9. `place the paper bag on the floors` (167.0-187.7 s)
10. `place the newspaper on the floors next to the paper bag` (187.7-196.0 s)
11. `move to the recycling bin` (196.0-210.0 s)
12. `open the lid of the recycling bin` (210.0-236.0 s)
13. `move to the paper bag` (236.0-259.0 s)
14. `pick up the paper bag from the floors` (259.0-268.6 s)
15. `move to the newspaper` (268.6-277.9 s)
16. `pick up the newspaper from the floors` (277.9-290.0 s)
17. `move to the recycling bin` (290.0-304.2 s)
18. `place the paper bag in the recycling bin` (304.2-310.0 s)
19. `move to the recycling bin` (310.0-317.8 s)
20. `place the newspaper in the recycling bin` (317.8-328.0 s)
21. `move to the recycling bin` (328.0-334.4 s)
22. `close the lid of the recycling bin` (334.4-339.0 s)

Mean duration per skill in this task: close door 22.7 s, close lid 9.4 s, move to 18.7 s, open door 10.5 s, open lid 29.7 s, pick up from 15.3 s, place in 13.2 s, place on 14.8 s, place on next to 12.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the recycling bin` | 696 |
| `move to the paper bag` | 404 |
| `pick up the paper bag from the floors` | 400 |
| `move to the newspaper` | 375 |
| `move to the door` | 248 |
| `move to the floors` | 238 |
| `pick up the newspaper from the floors` | 201 |
| `pick up the newspaper from the bar` | 200 |
| `open the door of the door` | 200 |
| `close the door of the door` | 200 |
| `place the newspaper on the floors next to the paper bag` | 200 |
| `open the lid of the recycling bin` | 200 |
| `place the paper bag in the recycling bin` | 200 |
| `close the lid of the recycling bin` | 200 |
| `place the newspaper in the recycling bin` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/61_bringing_paper_to_recycling.json`. Planner notes: `task_docs/notes/61_bringing_paper_to_recycling.md`.
