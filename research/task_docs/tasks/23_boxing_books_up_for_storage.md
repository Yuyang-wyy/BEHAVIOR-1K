# 23 · Boxing Books Up for Storage

Task name `boxing_books_up_for_storage`, task index 23.

> Put all six books from the bookcases in the living room into the box on the living room floor.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_upper` |
| rooms in the goal | living_room |
| rooms loaded | living_room_0 |
| human demo length | 807.6 s mean (24227 steps) |
| episode time limit | 1211.4 s (36341 steps at 30 Hz) |
| human base travel | 72.27 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114059113 |

## Planner notes

**Tier:** B — six hardbacks (0.018-0.031 m thick) go from four low bookcases into one storage box, all in one room. The thickness fits the 44 mm span, but only once a book overhangs its shelf edge (a push first, as every demo does). ft40k and zs_pt50 both scored 0 on instance 311.

### Goal in plain words

All six books must be inside the storage box (`storage_box_49`).
Book order and position inside the box are free, and the box can be anywhere.
Nothing else matters: the bookcases need no tidying and the box need not return to the floor.

### Q traps

- 6 literals, all False at reset (each book starts inside a bookcase, the box on the floor). Each book is worth 1/6.
- `inside` needs each book's AABB centre in the box's volume (PREDICATES §3). The box is shallow (0.48 x 0.50 x 0.12 m). A book leaning on the rim with its centre above the rim does not count. Lay books flat in the box.
- Stacked books are fine as long as each centre stays below the top of the box volume; six flat books of up to 0.031 m make a ~0.16 m stack, taller than the 0.12 m box. Lay them in two or more piles side by side (the box floor fits about four 0.25 x 0.19 m books).
- If the box is carried to the sofa and later tips or slides, books spill out and lose their literals.

### Minimal plan

All objects are in living_room_0 (the only room loaded). Bookcases are 0.85-7 m from the start; the box 1.5-6.6 m.

1. Optional: `move to the storage box`, `pick up the storage box from the floors`, `move to the sofa`, `place the storage box on the sofa` — box sitting level on the sofa seat. ~34 + 18 + 34 + 21 s. All 200 demos do this to raise the box; it is not required by the goal. Skip it if the arm can reach into a floor-level box.
2. `move to the hardback` — book visible on a bookcase shelf. ~34 s.
3. `push the hardback to the to_the_edge_of bookcase` — book overhangs the shelf front edge. ~27 s.
4. `pick up the hardback from the 2X1 bookcase` (shelf label as seen: `2X1`, `2X2`, `3X1`, `3X2`) — book lifted clear. ~18 s.
5. Repeat 2-4 for a second book with the other hand.
6. `move to the storage box`, `place the hardback in the storage box` twice — books lying flat inside, grippers open. ~34 s + 18 s each.
7. Repeat steps 2-6 two more times.

Done-check per book: book no longer on its shelf, visible lying inside the box walls.
Budget: about 700 s with step 1, 600 s without, against a 1211 s limit.

### What the demos do differently

- 199/200 demos move the box onto the sofa first.
- All 200 demos push every book to the shelf edge before picking; 1200 push segments in total. Keep this.
- Books are collected two per trip (one per hand) in all demos, in varied bookcase orders.

### Hard parts and hacks

- Books lie flat on low shelves (z 0.40-0.76 m). The grasp across the 0.02-0.03 m thickness is only possible at the shelf edge, hence the push. Per project memory, a book flat on a surface is one of the hardest grasps for the R1Pro.
- The box has no handle link (0.48 x 0.50 x 0.12 m); step 1 needs a grasp across a wall, unverified.
- The four bookcases are identical and low (1.05 m). Keep track of which books are done; the demo's shelf words (`2X1`, `3X2`) are shelf-grid positions.

### Hints for the VLM

- Four identical short bookcases (0.76 m wide, 1.05 m tall) stand in the living room; bookcases 1 and 2 hold two books each, 3 and 4 hold one each. There are no other books in the room.
- The storage box is the only box: a wide, shallow open box on the floor.
- The room also has a sofa, an armchair, a coffee table, a desk and a staircase with railings. Keep the base away from the stairs.
- Done: all four bookcases empty of hardbacks, six books inside the box.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside book.n.02_4 box.n.01_1)` | no | yes |
| `(inside book.n.02_6 box.n.01_1)` | no | yes |
| `(inside book.n.02_3 box.n.01_1)` | no | yes |
| `(inside book.n.02_2 box.n.01_1)` | no | yes |
| `(inside book.n.02_5 box.n.01_1)` | no | yes |
| `(inside book.n.02_1 box.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?book.n.02 - book.n.02) 
                (inside ?book.n.02 ?box.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `book.n.02_1` | hardback_55 | hardback / hrxujh | living_room_0 | low (0.25-0.6 m), z 0.58 | 3.17 m (range 0.85-6.24) | yes, spread 0.48 m |
| `book.n.02_2` | hardback_54 | hardback / okcflv | living_room_0 | table/counter (0.6-1.1 m), z 0.73 | 3.35 m (range 0.83-5.95) | yes, spread 0.42 m |
| `book.n.02_3` | hardback_53 | hardback / acbrnv | living_room_0 | low (0.25-0.6 m), z 0.42 | 2.65 m (range 1.04-5.58) | yes, spread 0.46 m |
| `book.n.02_4` | hardback_52 | hardback / znlewl | living_room_0 | table/counter (0.6-1.1 m), z 0.73 | 2.51 m (range 0.96-5.51) | yes, spread 0.39 m |
| `book.n.02_5` | hardback_51 | hardback / poanfs | living_room_0 | low (0.25-0.6 m), z 0.57 | 3.96 m (range 1.24-7.01) | yes, spread 0.41 m |
| `book.n.02_6` | hardback_50 | hardback / dichmv | living_room_0 | table/counter (0.6-1.1 m), z 0.73 | 1.91 m (range 1.06-4.77) | yes, spread 0.44 m |
| `floor.n.01_1` | floors_rfqizg_0 | floors / rfqizg | living_room_0 | floor, z -0.15 | 1.41 m (range 0.39-4.01) | no (fixed) |
| `bookcase.n.01_1` | bookcase_otwukr_3 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.23 m (range 0.85-6.1) | no (fixed) |
| `bookcase.n.01_2` | bookcase_otwukr_1 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 2.51 m (range 1.14-5.34) | no (fixed) |
| `bookcase.n.01_3` | bookcase_otwukr_0 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 3.97 m (range 1.14-6.86) | no (fixed) |
| `bookcase.n.01_4` | bookcase_otwukr_2 | bookcase / otwukr | living_room_0 | low (0.25-0.6 m), z 0.53 | 1.81 m (range 0.98-4.6) | no (fixed) |
| `box.n.01_1` | storage_box_49 | storage_box / bwbpvg | living_room_0 | floor, z 0.03 | 3.31 m (range 1.46-6.61) | yes, spread 8.02 m |

Initial conditions from `:init`:

```lisp
(inroom bookcase.n.01_1 living_room)
(inroom bookcase.n.01_2 living_room)
(inroom bookcase.n.01_3 living_room)
(inroom bookcase.n.01_4 living_room)
(inroom floor.n.01_1 living_room)
(inside book.n.02_1 bookcase.n.01_1)
(inside book.n.02_2 bookcase.n.01_1)
(inside book.n.02_3 bookcase.n.01_2)
(inside book.n.02_4 bookcase.n.01_2)
(inside book.n.02_5 bookcase.n.01_3)
(inside book.n.02_6 bookcase.n.01_4)
(ontop agent.n.01_1 floor.n.01_1)
(ontop box.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching box.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 box.n.01_1)
```

## What the human demos did

200 annotated demos. Length 778.92 s (range 433.53-1039.5). Skills per demo 31.0 (range 28-31). 8 distinct skill orders; the most common one covers 84% of demos.

Most common skill counts per demo (84% of demos): move to x11, pick up from x7, place in x6, push to x6, place on x1.

Representative demo `episode_00232140.json` (808.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the storage box` (0.0-27.1 s)
2. `pick up the storage box from the floors` (27.1-56.2 s)
3. `move to the sofa` (56.2-115.1 s)
4. `place the storage box on the sofa` (115.1-139.2 s)
5. `move to the hardback` (139.2-182.1 s)
6. `push the hardback to the to_the_edge_of bookcase` (182.1-212.3 s)
7. `pick up the hardback from the 3X1 bookcase` (212.3-230.0 s)
8. `move to the hardback` (230.0-235.4 s)
9. `push the hardback to the to_the_edge_of bookcase` (235.4-258.5 s)
10. `pick up the hardback from the 3X1 bookcase` (258.5-270.0 s)
11. `move to the storage box` (270.0-322.3 s)
12. `place the hardback in the storage box` (322.3-336.3 s)
13. `place the hardback in the storage box` (336.3-360.2 s)
14. `move to the hardback` (360.2-402.4 s)
15. `push the hardback to the to_the_edge_of bookcase` (402.4-431.2 s)
16. `pick up the hardback from the 2X1 bookcase` (431.2-445.2 s)
17. `move to the hardback` (445.2-449.5 s)
18. `push the hardback to the to_the_edge_of bookcase` (449.6-478.4 s)
19. `pick up the hardback from the 2X2 bookcase` (478.5-495.9 s)
20. `move to the storage box` (495.9-548.2 s)
21. `place the hardback in the storage box` (548.2-563.0 s)
22. `place the hardback in the storage box` (563.0-583.3 s)
23. `move to the hardback` (583.3-630.0 s)
24. `push the hardback to the to_the_edge_of bookcase` (630.0-660.2 s)
25. `pick up the hardback from the 2X1 bookcase` (660.2-671.2 s)
26. `move to the hardback` (671.2-676.2 s)
27. `push the hardback to the to_the_edge_of bookcase` (676.2-700.9 s)
28. `pick up the hardback from the 2X1 bookcase` (700.9-722.4 s)
29. `move to the storage box` (722.4-776.4 s)
30. `place the hardback in the storage box` (776.4-788.9 s)
31. `place the hardback in the storage box` (788.9-808.4 s)

Mean duration per skill in this task: move to 33.5 s, pick up from 17.6 s, place in 17.6 s, place on 21.3 s, push to 27.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `push the hardback to the to_the_edge_of bookcase` | 1200 |
| `place the hardback in the storage box` | 1199 |
| `move to the hardback` | 1145 |
| `move to the storage box` | 800 |
| `pick up the hardback from the 2X1 bookcase` | 348 |
| `pick up the hardback from the 2X2 bookcase` | 343 |
| `pick up the hardback from the 3X1 bookcase` | 292 |
| `pick up the hardback from the 3X2 bookcase` | 216 |
| `pick up the storage box from the floors` | 200 |
| `move to the sofa` | 200 |
| `place the storage box on the sofa` | 199 |
| `pick up the hardback from the 3X2 floors` | 1 |
| `place the storage box on the floors` | 1 |
| `place the hardback in the hardback` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/23_boxing_books_up_for_storage.json`. Planner notes: `task_docs/notes/23_boxing_books_up_for_storage.md`.
