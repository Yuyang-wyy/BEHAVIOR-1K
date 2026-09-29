# 29 · Clean Up Your Desk

Task name `clean_up_your_desk`, task index 29.

> In the child's room, clean up the desk: put both folders and both paperback books into the bookcase; put the pencil and both pens into the pencil case and leave the case on the desk; take the stapler out of the bookcase and place it on the desk; move the laptop from the bed onto the desk and close it.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | childs_room |
| rooms loaded | childs_room_0, childs_room_1, childs_room_2, corridor_0, dining_room_0, entryway_0, garden_0 |
| human demo length | 713.9 s mean (21417 steps) |
| episode time limit | 1070.9 s (32126 steps at 30 Hz) |
| human base travel | 60.5127 m |
| goal literals (best ground option) | 11 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.909 |
| ground goal options | 1 |
| starts open (joint_pos > 0.02) | `laptop.n.01_1` in 20/20 instances |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.09; ft40k@sulab1 Q=0.27; ft40k@local Q=0.27 |
| demo video | https://player.vimeo.com/video/1114059839 |

## Planner notes

**Tier:** C. Seven pick-and-place moves plus a laptop lid close; the laptop (0.32 x 0.45 m per asset bbox, unverified) and the flat books and folders must be pushed to an edge before they can be grasped, and the stapler sits on a bookcase shelf up to 1.38 m high.

### Goal in plain words

Both folders and both paperback books end inside the one bookcase in childs_room_1; any shelf is fine if the bookcase's fillable volume covers it (unverified). Both pens and the pencil end inside the pencil case, and the case must still rest on the desk. The stapler comes out of the bookcase onto the desk. The laptop moves from the bed onto the desk and its lid ends closed. There is one ground option, so no choice of container.

### Q traps

- `ontop pencil_box desk` is true at reset and never scores (11 literals, max partial Q 0.909). It still blocks success, so if the case is lifted it must go back on the desk.
- `not open laptop` is NOT true at reset: the template gives the laptop hinge `joint_pos` 2.4 rad in all 20 instances, so it starts open and closing it scores. The joint range is not in the asset metadata; "closed" means within 5 % of the closed end (PREDICATES §6).
- The stapler starts inside the bookcase; there is no `not inside` literal, only `ontop stapler desk`.
- `inside pen pencil_case` needs the pen's AABB centre inside the case's fillable volume. The case asset metadata lists no meta links; whether the runtime USD has a fillable link is not verified (PREDICATES §3). A pen resting across the rim scores nothing.
- Books or folders placed on top of the bookcase (1.76 m tall) are not inside it.
- Placing items on the desk next to the pencil case can knock it; the case sitting on a folder or pen instead of the desk breaks `ontop pencil_box desk` (needs direct contact, §4).
- Closing the lid while the laptop overhangs the desk edge can tip it off.

### Minimal plan

1. `move to the paperback book` -> `push the paperback book to the to_the_edge_of desk` -> `pick up the paperback book from the desk` -> `move to the bookcase` -> `place the paperback book in the 2X3 bookcase`. Done: book no longer on desk, visible on a shelf in the depth image. ~65 s each; repeat for the second book.
2. Same for the folder on the desk: `push the folder to the to_the_edge_of desk`, `pick up the folder from the desk`, `place the folder in the 3X3 bookcase`. ~70 s.
3. Folder on the chair: `move to the folder`, `push the folder to the to_the_edge_of eames chair`, `pick up the folder from the eames chair`, `move to the bookcase`, `place the folder in the 3X3 bookcase`. ~75 s. Skip the demo's `push the eames chair to the under desk`; the chair is not in the goal.
4. `move to the pen` -> `pick up the pen from the desk` -> `insert the pen into the pencil case`. Done: pen gone from desk surface, not lying across the case. ~35 s each; repeat for the second pen, then the pencil (`pick up the pencil from the desk`, `insert the pencil into the pencil case`). The demos hold the case with the other hand (`pick up the pencil case from the desk` first); inserting into the case while it rests on the desk avoids having to re-place it (untested). If the case was lifted: `place the pencil case on the desk`.
5. `move to the laptop` -> `push the laptop to the to_the_edge_of bed` -> `pick up the laptop from the bed` -> `move to the desk` -> `place the laptop on the desk`. Done: laptop visible flat on the desk top. Budget ~150 s; the push alone averages 34.5 s and took 114 s in the representative demo.
6. `close the lid of the laptop`. Done: screen no longer vertical, laptop a thin slab in depth. ~23 s.
7. `move to the stapler` -> `pick up the stapler from the 1x1 bookcase` -> `move to the desk` -> `place the stapler on the desk`. ~60 s; longer when the stapler is on the top shelf.

Total roughly 650 s against a 1071 s limit.

### What the demos do differently

- 167 distinct orders; no single order dominates (3 %). Order among the sub-goals is free.
- Humans stack the second folder and second book on the first (`place the folder on the folder`, `place the paperback book on the paperback book`). That is fine if the stack's centre stays inside the bookcase volume.
- Humans push the eames chair under the desk; not needed.
- Humans pick up the pencil case and insert pens while holding it, then put it back on the desk.
- The shelf words `1x1`, `2X3`, `3X3` in the prompts are annotation labels for bookcase cells; keep them verbatim.

### Hard parts and hacks

- Grasp widths from asset metadata bbox times template scale (no custom list; unverified at runtime): paperback book 20 mm thick, folder 45 mm (at the 44 mm limit), pen and pencil 15 mm, stapler 40 mm wide, laptop 37 mm closed. Flat items on a surface need the push-to-edge step so a jaw can go under.
- The laptop is the largest and slowest item; ft40k scored 0.27 (3/11) on instance 311, which literals is unknown.
- Stapler shelf height varies by instance (root z): 0.17-0.18 m in 301, 302, 310, 314, 316; ~0.58 m in 307, 312, 313, 315; ~0.98 m in 303, 317, 319, 320; ~1.38 m in 304, 305, 306, 308, 309, 311, 318. Half the leaderboard instances (301-310) have it on the top shelf. Reaching 1.38 m at 0.33 m depth needs the trunk raised; low shelves need the trunk bent.
- For the books and folders, prefer the lowest reachable empty shelf that is at arm height.
- Pens into a ~105 mm-tall case (asset bbox, unverified): a vertical drop from above the opening is the natural motion; failure is the pen landing across the rim.

### Hints for the VLM

- Room childs_room_1 has exactly one desk, one bookcase, one bed, one eames chair and one nightstand; no same-category distractors for goal furniture.
- Layout is fixed: bookcase near (22.9, 12.5), desk near (23.9, 13.2), bed near (21.3, 13.0); all within ~2.7 m, so few long drives.
- At start one folder is on the chair, the other folder, both books, both pens, the pencil and the pencil case are on the desk, the laptop is open on the bed, the stapler is on a bookcase shelf.
- Done looks like: desk holds only the pencil case (with pens and pencil hidden inside), the stapler and the closed laptop; four flat items on bookcase shelves.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside folder.n.02_2 bookcase.n.01_1)` | no | yes |
| `(inside folder.n.02_1 bookcase.n.01_1)` | no | yes |
| `(inside pen.n.01_2 pencil_box.n.01_1)` | no | yes |
| `(inside pen.n.01_1 pencil_box.n.01_1)` | no | yes |
| `(inside paperback_book.n.01_1 bookcase.n.01_1)` | no | yes |
| `(inside paperback_book.n.01_2 bookcase.n.01_1)` | no | yes |
| `(inside pencil.n.01_1 pencil_box.n.01_1)` | no | yes |
| `(ontop stapler.n.01_1 desk.n.01_1)` | no | yes |
| `(ontop pencil_box.n.01_1 desk.n.01_1)` | yes | never (already true) |
| `(ontop laptop.n.01_1 desk.n.01_1)` | no | yes |
| `(not open laptop.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and  
            (forall 
                (?folder.n.02 - folder.n.02) 
                (inside ?folder.n.02 ?bookcase.n.01_1)
            ) 
            (forall 
                (?pen.n.01 - pen.n.01) 
                (inside ?pen.n.01 ?pencil_box.n.01_1)
            ) 
            (forall 
                (?paperback_book.n.01 - paperback_book.n.01) 
                (inside ?paperback_book.n.01 ?bookcase.n.01_1)
            ) 
            (inside ?pencil.n.01_1 ?pencil_box.n.01_1) 
            (ontop ?stapler.n.01_1 ?desk.n.01_1) 
            (ontop ?pencil_box.n.01_1 ?desk.n.01_1) 
            (ontop ?laptop.n.01_1 ?desk.n.01_1)
            (not
                (open ?laptop.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `laptop.n.01_1` | laptop_233 | laptop / izydvb | childs_room_1 | low (0.25-0.6 m), z 0.51 | 1.62 m (range 1.3-2.22) | yes, spread 1.35 m |
| `desk.n.01_1` | desk_bhkhxo_0 | desk / bhkhxo | childs_room_1 | low (0.25-0.6 m), z 0.49 | 2.02 m (range 1.4-2.79) | no (fixed) |
| `folder.n.02_1` | folder_232 | folder / lktggf | childs_room_1 | table/counter (0.6-1.1 m), z 0.79 | 2.22 m (range 1.42-2.96) | yes, spread 1.5 m |
| `folder.n.02_2` | folder_231 | folder / lktggf | childs_room_1 | low (0.25-0.6 m), z 0.55 | 1.47 m (range 0.94-2.05) | yes, spread 0.32 m |
| `floor.n.01_1` | floors_qnvzkr_0 | floors / qnvzkr | childs_room_1 | floor, z -0.14 | 0.83 m (range 0.66-1.17) | no (fixed) |
| `pencil.n.01_1` | pencil_230 | pencil / lamaxq | childs_room_1 | table/counter (0.6-1.1 m), z 0.77 | 1.99 m (range 1.44-3.09) | yes, spread 1.61 m |
| `pen.n.01_1` | pen_229 | pen / gqwdor | childs_room_1 | table/counter (0.6-1.1 m), z 0.77 | 2.08 m (range 1.24-2.96) | yes, spread 1.74 m |
| `pen.n.01_2` | pen_228 | pen / gqwdor | childs_room_1 | table/counter (0.6-1.1 m), z 0.77 | 2.18 m (range 1.46-3.27) | yes, spread 1.69 m |
| `stapler.n.01_1` | stapler_227 | stapler / kgnsas | childs_room_1 | table/counter (0.6-1.1 m), z 0.98 | 2.09 m (range 1.69-2.47) | yes, spread 0.81 m |
| `paperback_book.n.01_1` | paperback_book_226 | paperback_book / yxujzs | childs_room_1 | table/counter (0.6-1.1 m), z 0.78 | 1.92 m (range 1.14-2.52) | yes, spread 1.48 m |
| `paperback_book.n.01_2` | paperback_book_225 | paperback_book / yxujzs | childs_room_1 | table/counter (0.6-1.1 m), z 0.78 | 2.04 m (range 1.03-2.97) | yes, spread 1.42 m |
| `pencil_box.n.01_1` | pencil_case_224 | pencil_case / otcmih | childs_room_1 | table/counter (0.6-1.1 m), z 0.82 | 2.22 m (range 1.39-3.05) | yes, spread 1.55 m |
| `bookcase.n.01_1` | bookcase_jaysra_0 | bookcase / jaysra | childs_room_1 | table/counter (0.6-1.1 m), z 0.91 | 2.04 m (range 1.69-2.44) | no (fixed) |
| `chair.n.01_1` | eames_chair_hndxiw_0 | eames_chair / hndxiw | childs_room_1 | low (0.25-0.6 m), z 0.52 | 1.37 m (range 0.9-2.03) | no |
| `bed.n.01_1` | bed_rrcvaq_1 | bed / rrcvaq | childs_room_1 | low (0.25-0.6 m), z 0.4 | 1.71 m (range 1.29-2.08) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom bed.n.01_1 childs_room)
(inroom bookcase.n.01_1 childs_room)
(inroom chair.n.01_1 childs_room)
(inroom desk.n.01_1 childs_room)
(inroom floor.n.01_1 childs_room)
(inside stapler.n.01_1 bookcase.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop folder.n.02_1 desk.n.01_1)
(ontop folder.n.02_2 chair.n.01_1)
(ontop laptop.n.01_1 bed.n.01_1)
(ontop paperback_book.n.01_1 desk.n.01_1)
(ontop paperback_book.n.01_2 desk.n.01_1)
(ontop pen.n.01_1 desk.n.01_1)
(ontop pen.n.01_2 desk.n.01_1)
(ontop pencil.n.01_1 desk.n.01_1)
(ontop pencil_box.n.01_1 desk.n.01_1)
(open laptop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bed.n.01_1 laptop.n.01_1)
(touching chair.n.01_1 folder.n.02_2)
(touching desk.n.01_1 folder.n.02_1)
(touching desk.n.01_1 paperback_book.n.01_1)
(touching desk.n.01_1 paperback_book.n.01_2)
(touching desk.n.01_1 pen.n.01_1)
(touching desk.n.01_1 pen.n.01_2)
(touching desk.n.01_1 pencil.n.01_1)
(touching desk.n.01_1 pencil_box.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching folder.n.02_1 desk.n.01_1)
(touching folder.n.02_2 chair.n.01_1)
(touching laptop.n.01_1 bed.n.01_1)
(touching paperback_book.n.01_1 desk.n.01_1)
(touching paperback_book.n.01_2 desk.n.01_1)
(touching pen.n.01_1 desk.n.01_1)
(touching pen.n.01_2 desk.n.01_1)
(touching pencil.n.01_1 desk.n.01_1)
(touching pencil_box.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 711.73 s (range 441.3-1034.4). Skills per demo 42.0 (range 37-48). 167 distinct skill orders; the most common one covers 3% of demos.

Most common skill counts per demo (12% of demos): move to x15, pick up from x10, push to x6, place on x5, insert x3, place in x2, close lid x1.

Representative demo `episode_00290660.json` (633.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the folder` (2.5-13.6 s)
2. `push the folder to the to_the_edge_of eames chair` (13.6-29.8 s)
3. `pick up the folder from the eames chair` (29.8-55.5 s)
4. `push the eames chair to the under desk` (55.5-77.5 s)
5. `move to the bookcase` (77.5-88.2 s)
6. `place the folder in the 3X3 bookcase` (88.2-98.5 s)
7. `move to the paperback book` (98.5-108.0 s)
8. `push the paperback book to the to_the_edge_of desk` (108.0-123.0 s)
9. `pick up the paperback book from the desk` (123.0-131.2 s)
10. `move to the bookcase` (131.2-137.7 s)
11. `place the paperback book in the 2X3 bookcase` (137.7-149.1 s)
12. `move to the folder` (149.1-156.3 s)
13. `push the folder to the to_the_edge_of desk` (156.3-191.0 s)
14. `pick up the folder from the desk` (191.0-199.3 s)
15. `move to the folder` (199.3-205.8 s)
16. `place the folder on the folder` (205.8-215.9 s)
17. `move to the paperback book` (215.9-218.5 s)
18. `push the paperback book to the to_the_edge_of desk` (218.5-248.1 s)
19. `pick up the paperback book from the desk` (248.1-258.7 s)
20. `move to the paperback book` (258.7-264.7 s)
21. `place the paperback book on the paperback book` (264.7-273.6 s)
22. `move to the pencil case` (273.6-281.8 s)
23. `pick up the pencil case from the desk` (281.8-295.5 s)
24. `move to the pen` (295.5-300.8 s)
25. `pick up the pen from the desk` (300.8-310.8 s)
26. `insert the pen into the pencil case` (310.8-320.6 s)
27. `move to the pencil` (320.6-323.2 s)
28. `pick up the pencil from the desk` (323.2-333.7 s)
29. `insert the pencil into the pencil case` (333.7-348.3 s)
30. `move to the pen` (348.3-350.4 s)
31. `pick up the pen from the desk` (350.4-365.3 s)
32. `insert the pen into the pencil case` (365.3-373.7 s)
33. `move to the desk` (373.7-376.0 s)
34. `place the pencil case on the desk` (376.0-383.1 s)
35. `move to the laptop` (383.1-399.3 s)
36. `push the laptop to the to_the_edge_of bed` (399.3-513.7 s)
37. `pick up the laptop from the bed` (513.7-530.9 s)
38. `move to the desk` (530.9-551.5 s)
39. `place the laptop on the desk` (551.5-555.5 s)
40. `close the lid of the laptop` (555.5-572.2 s)
41. `move to the stapler` (572.2-575.9 s)
42. `pick up the stapler from the 1x1 bookcase` (575.9-623.0 s)
43. `move to the desk` (623.0-627.1 s)
44. `place the stapler on the desk` (627.1-635.6 s)

Mean duration per skill in this task: close lid 22.9 s, hand over 16.3 s, insert 14.7 s, move to 8.3 s, pick up from 20.7 s, place in 19.3 s, place on 15.1 s, place on next to 22.0 s, push to 34.5 s, turn to 21.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the folder` | 588 |
| `move to the paperback book` | 576 |
| `move to the desk` | 443 |
| `pick up the pen from the desk` | 406 |
| `pick up the paperback book from the desk` | 400 |
| `insert the pen into the pencil case` | 400 |
| `move to the bookcase` | 395 |
| `push the paperback book to the to_the_edge_of desk` | 394 |
| `move to the pen` | 269 |
| `pick up the pencil from the desk` | 206 |
| `pick up the pencil case from the desk` | 203 |
| `place the pencil case on the desk` | 203 |
| `pick up the folder from the desk` | 200 |
| `close the lid of the laptop` | 200 |
| `place the stapler on the desk` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/29_clean_up_your_desk.json`. Planner notes: `task_docs/notes/29_clean_up_your_desk.md`.
