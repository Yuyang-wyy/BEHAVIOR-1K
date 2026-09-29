# 04 · Can Meat

Task name `can_meat`, task index 4.

> Open the kitchen cabinet, take out the two hinged jars, open them, place exactly two cooked bratwursts from the chopping board on the countertop into each jar, then close both jars, put them back inside the cabinet, and close the cabinet.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 394.9 s mean (11847 steps) |
| episode time limit | 592.4 s (17770 steps at 30 Hz) |
| human base travel | 31.6605 m |
| goal literals (best ground option) | 9 |
| literals already true at start (inferred) | 5 |
| max Q short of full success | 0.444 |
| ground goal options | 36 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00; ft10k@sulab1 Q=0.00 |
| demo video | https://player.vimeo.com/video/1114054618 |

## Planner notes

**Tier:** C — two hinged jars must come out of a high wall cabinet (z ~1.6 m), be opened and closed while held, get 2 bratwursts each, and go back. It is bimanual lid work at head height, on top of 6 pick-and-places.

### Goal in plain words

- Each of the 2 hinged jars holds **exactly 2** bratwursts. Any 2 of the 4 bratwursts may go in either jar.
- Both jar lids are closed at the end.
- Both jars are back inside `top_cabinet_lkxmne_2`.
- That cabinet is closed at the end, with every door within 5 % of closed.
- The bratwursts already start cooked (`cooked` in `:init`, MaxTemperature 72 °C in the template). No cooking is needed.

### Q traps

- There are 9 literals, and 5 of them are true at reset: both jars `inside` the cabinet, both jars `not open`, and the cabinet `not open`.
- Verified: both jars and the cabinet have joint_pos ~0 in the template and in all 20 instances. The jars' root z is 1.6 m, inside the cabinet.
- So the partial Q ceiling is 4/9 = 0.444. Only the 4 `inside bratwurst jar` literals can score.
- Partial-Q shortcut: take the jars out, open them, and put 2 bratwursts in each. That alone reaches 0.444, even with the jars left on the counter, lids open and cabinet open.
- Closing the lids, returning the jars and closing the cabinet earns 0 partial Q. It is only needed for full success (1.0).
- `forn (2)` needs exactly 2 per jar (PREDICATES §0). A third bratwurst in one jar blocks success. Partial Q is not hurt.
- The page's example option puts bratwurst_3 and _4 in both jars. It is just one of the 36 expansions. Any 2+2 split is equivalent.
- Closing a lid can push a bratwurst's centre out of the jar volume (§3). Re-check after `close the lid`.
- The cabinet has 2 doors (2 joints). A door left ajar blocks success (§6).

### Minimal plan

1. `move to the top cabinet` — base stopped under the wall cabinet. ~20 s.
2. `open the door of the right_door top cabinet`, then `open the door of the left_door top cabinet` — both doors swung open, jars visible on the lower shelf. ~67 s.
3. `pick up the hinged jar from the low_level top cabinet` — jar clear of the shelf. ~14 s.
4. `hand over the hinged jar with the right` — jar now in the other hand. ~11 s.
5. `move to the bratwurst` — cutting board with bratwursts in view. It is 2-4.6 m from the cabinet. ~20 s.
6. `open the lid of the hinged jar` — lid visibly swung up. ~10 s.
7. `pick up the bratwurst from the cutting board`, then `place the bratwurst in the hinged jar`, done 2 times — bratwurst not visible above the rim. ~46 s.
8. `close the lid of the hinged jar` — lid flush. ~7 s.
9. `move to the top cabinet`, then `place the hinged jar in the low_level top cabinet` — jar on the shelf, gripper withdrawn. ~29 s.
10. Repeat 3-9 for the second jar. ~155 s.
11. `close the door of the left_door top cabinet`, then `close the door of the right_door top cabinet` — both doors flush. ~40 s.

- The total is about 420 s against a 592.4 s limit.
- If the timer passes ~450 s before step 10 finishes, stop after the second jar's bratwursts. Q = 0.444 is already banked.

### What the demos do differently

- There are 24 distinct orders, and the most common covers only 32 % of demos. The variation is mostly which hand holds the jar and when the lid opens.
- Humans keep the jar in one hand and work the lid and bratwursts with the other. No demo sets the jar down on the counter. So `place the hinged jar on the ...` has no trained prompt.
- Humans return jar 1 before fetching jar 2, leaving the cabinet doors open in between.
- About 12 % of jar pickups (49 of ~400) and placements (48) use the `high_level` shelf wording. Either shelf is inside the cabinet.
- `turn to the hinged jar` appears 9 times. Its purpose is unclear; skip it.

### Hard parts and hacks

- Height: the jars sit at ~1.6 m, and the cabinet centre is at 1.79 m. Reaching in and back out is near the top of the R1Pro workspace. Tipping risk while holding the jar extended high is real.
- The jar's size vs the 44 mm span is unknown (model vzwhbg, scale 0.9). The bratwurst's width is also unknown (scale 0.5). It is long and thin, so it is likely graspable but unverified.
- The lid hinge needs a fingertip push while the other hand holds the jar still. VLA failures here are likely: the lid stays shut, or the jar is dropped.
- Dropping a bratwurst into a jar held at an angle can bounce it out. Place it low, over the opening.
- Travel: the cutting board is 2.0-4.6 m from the cabinet (x ~6.0-8.6 vs 4.0), and the robot does 4 legs. Rotation drift makes the return to the cabinet unreliable. Re-localise on the cabinet visually.
- Cheap legal shortcut for Q: after step 7 for both jars, the planner may skip everything else when time is short. See Q traps.

### Hints for the VLM

- The target is `top_cabinet_lkxmne_2`, a wall cabinet with 2 doors above the counter in `kitchen_0`. Its centre is at world x ~4.0, y ~0.65, z ~1.8.
- The kitchen has 3 top cabinets. Only the one holding the jars counts, so open doors until you see the 2 jars.
- The jars sit side by side on the lower shelf. Each has a hinged lid; its look is not verified.
- The cutting board lies on a counter at ~1.06 m with 4 bratwursts on it. It is the only cutting board. Its position varies by up to 2.7 m across instances.
- Distractors: 2 countertops, a bar, shelves, and a water glass. Do not put bratwursts in the glass.
- Done: each jar holds 2 bratwursts with the lid down, both jars are on the cabinet shelf, and both cabinet doors are flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside hinged_jar.n.01_1 cabinet.n.01_1)` | yes | never (already true) |
| `(inside hinged_jar.n.01_2 cabinet.n.01_1)` | yes | never (already true) |
| `(not open hinged_jar.n.01_1))` | yes | never (already true) |
| `(not open hinged_jar.n.01_2))` | yes | never (already true) |
| `(inside bratwurst.n.01_4 hinged_jar.n.01_1)` | no | yes |
| `(inside bratwurst.n.01_1 hinged_jar.n.01_1)` | no | yes |
| `(inside bratwurst.n.01_4 hinged_jar.n.01_2)` | no | yes |
| `(inside bratwurst.n.01_1 hinged_jar.n.01_2)` | no | yes |
| `(not open cabinet.n.01_1))` | yes | never (already true) |

The goal has 36 ground options (9 literals x36); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?hinged_jar.n.01 - hinged_jar.n.01) 
                (inside ?hinged_jar.n.01 ?cabinet.n.01_1)
            ) 
            (forall 
                (?hinged_jar.n.01 - hinged_jar.n.01)
                (not
                    (open ?hinged_jar.n.01)
                )
            )
            (forall 
                (?hinged_jar.n.01 - hinged_jar.n.01) 
                (forn
                    (2)
                    (?bratwurst.n.01 - bratwurst.n.01)
                    (inside ?bratwurst.n.01 ?hinged_jar.n.01)
                )
            )
            (not
                (open ?cabinet.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `hinged_jar.n.01_1` | hinged_jar_236 | hinged_jar / vzwhbg | kitchen_0 | high (1.1-1.6 m), z 1.6 | 1.72 m (range 1.05-4.99) | yes, spread 0.83 m |
| `hinged_jar.n.01_2` | hinged_jar_235 | hinged_jar / vzwhbg | kitchen_0 | high (1.1-1.6 m), z 1.6 | 1.9 m (range 1.01-4.73) | yes, spread 0.84 m |
| `cabinet.n.01_1` | top_cabinet_lkxmne_2 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 1.83 m (range 1.1-4.93) | no (fixed) |
| `countertop.n.01_1` | bar_udatjt_0 | bar / udatjt | kitchen_0 | table/counter (0.6-1.1 m), z 0.66 | 2.14 m (range 1.18-2.64) | no (fixed) |
| `chopping_board.n.01_1` | cutting_board_234 | cutting_board / jfrbuz | kitchen_0 | table/counter (0.6-1.1 m), z 1.06 | 1.58 m (range 0.83-3.75) | yes, spread 2.71 m |
| `bratwurst.n.01_1` | bratwurst_233 | bratwurst / pqfrrn | kitchen_0 | table/counter (0.6-1.1 m), z 1.09 | 1.57 m (range 0.75-3.77) | yes, spread 2.88 m |
| `bratwurst.n.01_2` | bratwurst_232 | bratwurst / pqfrrn | kitchen_0 | table/counter (0.6-1.1 m), z 1.09 | 1.59 m (range 0.78-3.76) | yes, spread 2.84 m |
| `bratwurst.n.01_3` | bratwurst_231 | bratwurst / pqfrrn | kitchen_0 | table/counter (0.6-1.1 m), z 1.09 | 1.69 m (range 0.74-3.8) | yes, spread 3.06 m |
| `bratwurst.n.01_4` | bratwurst_230 | bratwurst / pqfrrn | kitchen_0 | table/counter (0.6-1.1 m), z 1.09 | 1.59 m (range 0.88-3.7) | yes, spread 2.79 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.55 m (range 0.82-2.41) | no (fixed) |

Initial conditions from `:init`:

```lisp
(cooked bratwurst.n.01_1)
(cooked bratwurst.n.01_2)
(cooked bratwurst.n.01_3)
(cooked bratwurst.n.01_4)
(inroom cabinet.n.01_1 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside hinged_jar.n.01_1 cabinet.n.01_1)
(inside hinged_jar.n.01_2 cabinet.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bratwurst.n.01_1 chopping_board.n.01_1)
(ontop bratwurst.n.01_2 chopping_board.n.01_1)
(ontop bratwurst.n.01_3 chopping_board.n.01_1)
(ontop bratwurst.n.01_4 chopping_board.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bratwurst.n.01_1 chopping_board.n.01_1)
(touching bratwurst.n.01_2 chopping_board.n.01_1)
(touching bratwurst.n.01_3 chopping_board.n.01_1)
(touching bratwurst.n.01_4 chopping_board.n.01_1)
(touching chopping_board.n.01_1 bratwurst.n.01_1)
(touching chopping_board.n.01_1 bratwurst.n.01_2)
(touching chopping_board.n.01_1 bratwurst.n.01_3)
(touching chopping_board.n.01_1 bratwurst.n.01_4)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 385.4 s (range 266.9-566.0). Skills per demo 27.0 (range 24-28). 24 distinct skill orders; the most common one covers 32% of demos.

Most common skill counts per demo (54% of demos): pick up from x6, place in x6, move to x5, close door x2, close lid x2, hand over x2, open door x2, open lid x2.

Representative demo `episode_00042780.json` (355.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the top cabinet` (0.0-23.3 s)
2. `open the door of the right_door top cabinet` (23.3-52.1 s)
3. `open the door of the left_door top cabinet` (52.1-80.9 s)
4. `pick up the hinged jar from the low_level top cabinet` (80.9-93.2 s)
5. `hand over the hinged jar with the right` (93.2-105.1 s)
6. `move to the bratwurst` (105.1-139.3 s)
7. `open the lid of the hinged jar` (128.0-135.7 s)
8. `pick up the bratwurst from the cutting board` (139.3-145.6 s)
9. `place the bratwurst in the hinged jar` (145.6-149.0 s)
10. `pick up the bratwurst from the cutting board` (149.0-155.4 s)
11. `place the bratwurst in the hinged jar` (155.4-158.3 s)
12. `close the lid of the hinged jar` (158.3-161.9 s)
13. `move to the top cabinet` (162.0-177.7 s)
14. `place the hinged jar in the low_level top cabinet` (177.7-187.6 s)
15. `pick up the hinged jar from the low_level top cabinet` (187.6-204.3 s)
16. `hand over the hinged jar with the left` (204.3-211.8 s)
17. `move to the bratwurst` (211.8-244.2 s)
18. `open the lid of the hinged jar` (230.7-240.3 s)
19. `pick up the bratwurst from the cutting board` (244.2-255.0 s)
20. `place the bratwurst in the hinged jar` (255.0-258.0 s)
21. `pick up the bratwurst from the cutting board` (258.0-266.9 s)
22. `place the bratwurst in the hinged jar` (266.9-269.9 s)
23. `close the lid of the hinged jar` (269.9-274.6 s)
24. `move to the top cabinet` (274.6-298.4 s)
25. `place the hinged jar in the low_level top cabinet` (298.4-307.7 s)
26. `close the door of the left_door top cabinet` (307.7-330.2 s)
27. `close the door of the right_door top cabinet` (330.2-355.0 s)

Mean duration per skill in this task: close door 20.1 s, close lid 6.5 s, hand over 11.0 s, move to 19.8 s, open door 33.3 s, open lid 10.1 s, pick up from 14.2 s, place in 8.9 s, turn to 28.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the bratwurst in the hinged jar` | 800 |
| `pick up the bratwurst from the cutting board` | 798 |
| `move to the top cabinet` | 594 |
| `open the lid of the hinged jar` | 400 |
| `move to the bratwurst` | 400 |
| `close the lid of the hinged jar` | 400 |
| `place the hinged jar in the low_level top cabinet` | 352 |
| `pick up the hinged jar from the low_level top cabinet` | 351 |
| `open the door of the right_door top cabinet` | 201 |
| `open the door of the left_door top cabinet` | 200 |
| `close the door of the right_door top cabinet` | 200 |
| `close the door of the left_door top cabinet` | 199 |
| `hand over the hinged jar with the left` | 174 |
| `hand over the hinged jar with the right` | 167 |
| `pick up the hinged jar from the high_level top cabinet` | 49 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/04_can_meat.json`. Planner notes: `task_docs/notes/04_can_meat.md`.
