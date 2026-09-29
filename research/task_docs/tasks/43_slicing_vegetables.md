# 43 · Slicing Vegetables

Task name `slicing_vegetables`, task index 43.

> From the refrigerator in the kitchen, take out the two bell peppers, the two beets, and the zucchini. Then, on either chopping board on the countertop, use the parer to dice all of them so that only diced bell pepper, diced beet, and diced zucchini remain. Make sure the refrigerator is closed when you finish.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 494.8 s mean (14844 steps) |
| episode time limit | 742.2 s (22267 steps at 30 Hz) |
| human base travel | 40.6344 m |
| goal literals (best ground option) | 9 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.889 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.44; ft40k@local Q=0.44 |
| demo video | https://player.vimeo.com/video/1114061183 |

## Planner notes

**Tier:** D — five slice transitions and three dice transitions with one knife. None of the vegetables fits the jaws, but none of them has to be moved.

### Goal in plain words

- Every whole bell pepper (2), beet (2) and zucchini (1) must be gone, which happens when it is sliced.
- `diced__bell_pepper`, `diced__beet` and `diced__zucchini` must each exist, which needs at least one half of each type diced.
- The fridge must be closed at the end.

**Tool:** the parer `parer_207`, the only slicer. The goal says nothing about where the pieces end up or about the chopping boards. So the cutting can happen anywhere, **including on the fridge shelves**.

### Q traps

- 9 literals. `not open fridge` is true at start (joint_pos 0.0 in all 20 instances), so it never scores. Max partial Q is 8/9 = 0.889 (page is right). Full success still needs the door closed at the end.
- A **slice alone** scores its `not real` literal, because the whole vegetable is removed (§7). The 5 slices are worth 5/9 = 0.556.
- A `real diced__X` literal needs just **one** half of that type diced, so 3 dices are worth 3/9. The other 7 halves are not in the goal. The demos dice all 10.
- Re-arm: after each contact, keep the parer off every sliceable for 2 s before the next cut (§7). Touching a half does not hold the cooldown (halves are only diceable), but the next contact then dices that half.
- Closing the fridge onto spilled pieces or halves can leave the door ajar (more than 5 %, §6). Look for a flush door.

### Minimal plan

This plan cuts in the fridge. It is derived from the goal and not tested.

1. `pick up the parer from the countertop` — go to the parer first with `move to the cutting board`, since the parer lies on `countertop_kelzer_0` near the boards. ~18 s + ~20 s.
2. `move to the fridge`, `open the door of the fridge` — ~18 s + ~47 s.
3. For each whole vegetable on the shelves: `chop the parer with the zucchini`, `chop the parer with the beet`, `chop the parer with the bell pepper` — each whole item replaced by two halves. Lift the knife and wait more than 2 s between cuts. ~4 s each, 5 cuts.
4. Dice one half of each type: `chop the parer with the half zucchini 208`, `chop the parer with the half beet 212`, `chop the parer with the half bell pepper 214` — each touched half turns into small pieces. ~4 s each, 3 cuts.
5. `close the door of the fridge` — door flush. ~29 s. Success fires here if all 8 transitions happened.

The plan takes about 200 s against a 742 s limit. That leaves time to retry missed cuts or to dice extra halves if one dice did not register.

If a shelf item is out of the knife's reach, fall back to the demo route for that item only: `pick up the beet from the high_level fridge`, `move to the cutting board`, `place the beet on the cutting board`.

### What the demos do differently

- Every demo carries all five vegetables to the two boards (5 picks, 5 places, ~180 s) and closes the fridge **before** cutting.
- They dice all 10 halves, 15 cuts in total, where 8 are enough.
- 160 of 200 put the beets and the zucchini on `cutting_board_209` and the peppers on `cutting_board_210`. The board choice does not matter.

### Hard parts and hacks

- **Grasp span.** No vegetable fits the 44 mm span: bell pepper 108 x 80 x 82 mm, beet 175 x 104 x 82 mm, zucchini 219 x 72 x 65 mm (asset bbox × scale). Carrying them out is the weak point of the demo route. Cutting in place avoids it.
- **Parer.** `lwpdhi` is 268 x 31 x 14 mm and fits the jaws.
- **Shelf heights.** The vegetables sit at z 0.50, 0.92 or 1.32 depending on the instance. The low shelf needs the trunk lowered and the high shelf needs it raised.
- Halves spawn beside the cut point (asset `object_parts`) and may drop to a lower shelf or out of the door. They stay valid targets wherever they land.
- Pieces spilled on the floor do not matter.

### Hints for the VLM

- Kitchen of `house_single_floor`. The single-door fridge `fridge_dszchb_0` is at the right end of the sink wall (7.8, -2.0). The two cutting boards and the parer are on `countertop_kelzer_0` along the same wall.
- In the fridge: two red/yellow bell peppers (roundish), two dark red beets (round with a tail), and one long green zucchini. They start chilled at -1.9 °C, which does not matter here.
- A sliced item shows two cut halves. A diced half becomes a small pile of cubes.
- Done: no whole vegetable left, at least one pile of cubes per vegetable type, fridge door flush.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real diced__zucchini.n.01_1)` | no | yes |
| `(real diced__bell_pepper.n.01_1)` | no | yes |
| `(real diced__beet.n.01_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |
| `(not real bell_pepper.n.02_2))` | no | yes |
| `(not real bell_pepper.n.02_1))` | no | yes |
| `(not real beet.n.02_1))` | no | yes |
| `(not real beet.n.02_2))` | no | yes |
| `(not real zucchini.n.02_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?diced__zucchini.n.01_1)
            (real ?diced__bell_pepper.n.01_1)
            (real ?diced__beet.n.01_1)
            (not
                (open ?electric_refrigerator.n.01_1)
            )
            (forall
                (?bell_pepper.n.02 - bell_pepper.n.02)
                (not
                    (real ?bell_pepper.n.02)
                )
            )
            (forall
                (?beet.n.02 - beet.n.02)
                (not
                    (real ?beet.n.02)
                )
            )
            (forall
                (?zucchini.n.02 - zucchini.n.02)
                (not
                    (real ?zucchini.n.02)
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
| `bell_pepper.n.02_1` | bell_pepper_214 | bell_pepper / wszvwc | kitchen_0 | table/counter (0.6-1.1 m), z 0.72 | 3.93 m (range 0.98-4.19) | yes, spread 0.37 m |
| `bell_pepper.n.02_2` | bell_pepper_213 | bell_pepper / wszvwc | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.98 m (range 1.07-4.24) | yes, spread 0.43 m |
| `diced__bell_pepper.n.01_1` | particle system | diced__bell_pepper | - | - | - | - |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 4.03 m (range 1.14-4.28) | no (fixed) |
| `beet.n.02_1` | beet_212 | beet / wantjv | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.96 m (range 1.01-4.34) | yes, spread 0.39 m |
| `beet.n.02_2` | beet_211 | beet / wantjv | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 3.92 m (range 1.12-4.34) | yes, spread 0.4 m |
| `diced__beet.n.01_1` | particle system | diced__beet | - | - | - | - |
| `chopping_board.n.01_1` | cutting_board_210 | cutting_board / tcdrzs | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.93 m (range 1.01-5.2) | yes, spread 2.52 m |
| `chopping_board.n.01_2` | cutting_board_209 | cutting_board / tcdrzs | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 3.46 m (range 0.78-3.77) | yes, spread 2.7 m |
| `zucchini.n.02_1` | zucchini_208 | zucchini / udvfaz | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 3.9 m (range 1.08-4.28) | yes, spread 0.39 m |
| `diced__zucchini.n.01_1` | particle system | diced__zucchini | - | - | - | - |
| `parer.n.02_1` | parer_207 | parer / lwpdhi | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.1 m (range 0.74-4.87) | yes, spread 2.88 m |
| `countertop.n.01_1` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 3.2 m (range 1.11-4.49) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 2.0 m (range 0.78-2.86) | no (fixed) |

Initial conditions from `:init`:

```lisp
(future diced__beet.n.01_1)
(future diced__bell_pepper.n.01_1)
(future diced__zucchini.n.01_1)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside beet.n.02_1 electric_refrigerator.n.01_1)
(inside beet.n.02_2 electric_refrigerator.n.01_1)
(inside bell_pepper.n.02_1 electric_refrigerator.n.01_1)
(inside bell_pepper.n.02_2 electric_refrigerator.n.01_1)
(inside zucchini.n.02_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop chopping_board.n.01_2 countertop.n.01_1)
(ontop parer.n.02_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_2 countertop.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_2)
(touching countertop.n.01_1 parer.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching parer.n.02_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 490.5 s (range 245.27-706.8). Skills per demo 37.0 (range 32-41). 109 distinct skill orders; the most common one covers 8% of demos.

Most common skill counts per demo (12% of demos): chop x15, move to x8, pick up from x6, place on x6, close door x1, open door x1.

Representative demo `episode_00431070.json` (456.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-27.9 s)
2. `open the door of the fridge` (27.9-68.7 s)
3. `pick up the beet from the middle_level fridge` (68.7-91.4 s)
4. `pick up the beet from the high_level fridge` (91.4-125.3 s)
5. `move to the cutting board` (125.3-133.6 s)
6. `place the beet on the cutting board` (133.6-146.2 s)
7. `place the beet on the cutting board` (146.2-161.9 s)
8. `move to the bell pepper` (161.9-179.3 s)
9. `pick up the bell pepper from the high_level fridge` (179.4-203.6 s)
10. `pick up the bell pepper from the low_level fridge` (203.6-246.1 s)
11. `move to the cutting board` (246.1-253.9 s)
12. `place the bell pepper on the cutting board` (253.9-267.2 s)
13. `place the bell pepper on the cutting board` (267.2-275.4 s)
14. `move to the zucchini` (275.4-295.8 s)
15. `pick up the zucchini from the low_level fridge` (295.8-337.2 s)
16. `close the door of the fridge` (337.2-355.6 s)
17. `place the zucchini on the cutting board` (355.6-366.7 s)
18. `pick up the parer from the countertop` (366.7-381.0 s)
19. `chop the parer with the zucchini` (381.0-389.1 s)
20. `chop the parer with the half zucchini 208` (389.1-390.4 s)
21. `chop the parer with the beet` (390.4-392.4 s)
22. `chop the parer with the half zucchini 208` (392.4-395.4 s)
23. `chop the parer with the half beet 212` (392.4-395.4 s)
24. `chop the parer with the half beet 212` (395.4-398.4 s)
25. `chop the parer with the beet` (398.4-401.7 s)
26. `chop the parer with the half beet 211` (401.8-404.0 s)
27. `chop the parer with the half beet 211` (404.0-407.3 s)
28. `move to the bell pepper` (407.3-417.8 s)
29. `chop the parer with the bell pepper` (417.8-426.3 s)
30. `chop the parer with the half bell pepper 214` (426.3-429.1 s)
31. `chop the parer with the half bell pepper 214` (429.1-432.4 s)
32. `chop the parer with the bell pepper` (432.4-436.5 s)
33. `chop the parer with the half bell pepper 213` (436.5-439.8 s)
34. `chop the parer with the half bell pepper 213` (439.8-442.0 s)
35. `place the parer on the countertop` (442.0-456.4 s)

Mean duration per skill in this task: chop 3.8 s, close door 29.4 s, move to 17.8 s, open door 47.5 s, pick up from 20.2 s, place on 16.1 s, push to 16.6 s, turn to 18.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the cutting board` | 500 |
| `place the bell pepper on the cutting board` | 400 |
| `place the beet on the cutting board` | 400 |
| `chop the parer with the bell pepper` | 400 |
| `chop the parer with the beet` | 399 |
| `chop the parer with the half bell pepper 214` | 395 |
| `chop the parer with the half bell pepper 213` | 392 |
| `chop the parer with the half beet 211` | 386 |
| `chop the parer with the half beet 212` | 375 |
| `chop the parer with the half zucchini 208` | 375 |
| `move to the zucchini` | 239 |
| `move to the beet` | 227 |
| `move to the fridge` | 200 |
| `open the door of the fridge` | 200 |
| `close the door of the fridge` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/43_slicing_vegetables.json`. Planner notes: `task_docs/notes/43_slicing_vegetables.md`.
