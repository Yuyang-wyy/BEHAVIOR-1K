# 12 · Preparing Lunch Box

Task name `preparing_lunch_box`, task index 12.

> Put both apple halves, the club sandwich, and the chocolate chip cookie from the chopping board on the kitchen countertop into the packing box on the countertop. Then take the bottle of tea out of the refrigerator, put it into the same box, and close the refrigerator when you're done.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 274.8 s mean (8245 steps) |
| episode time limit | 412.3 s (12367 steps at 30 Hz) |
| human base travel | 21.398 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.833 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.67; ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114057330 |

## Planner notes

**Tier:** B — five small pick-and-place items into an open box, plus one fridge door open/close; no state change. The flat cookie is the awkward grasp.

### Goal in plain words

- Two apple halves, the club sandwich, the chocolate chip cookie and the bottle of tea must all be `inside` the one packing box.
- The fridge must be closed at the end (`not open`, 5 % rule, PREDICATES §6).
- The box has no joints (no `joint_pos` in the template), so it is always open; nothing to close on it.
- Where the box stands does not matter. Moving it is allowed.
- There is exactly one of each object in the kitchen; no distractors of the same category.

### Q traps

- `not open fridge` is true at reset (fridge `joint_pos` 0.0 in the template and all 20 instances). It never scores. Max partial Q = 5/6 = 0.833.
- Leaving the fridge open after taking the tea costs no partial Q but blocks success. Close it right after the tea pick, as every demo does.
- `inside` tests only the item's AABB centre in the box volume (PREDICATES §3). An item resting on the rim or on another item poking out of the box can fail. Check after each drop.
- Knocking the box (e.g. while carrying the tea bottle into it) can tip it and spill earlier items. Items lost at the end score 0.
- Closed-loop on 311: zs_pt50 Q=0.67 (4 of 5 items), ft40k Q=0.50 (3 of 5).

### Minimal plan

1. `move to the packing box` — box centred in view, base stopped. ~10 s.
2. `pick up the packing box from the countertop` — box lifted. ~13 s. Optional, see below.
3. `move to the chopping board` — ~10 s.
4. `place the packing box on the countertop next to the right chopping board` — box resting beside the board. ~5 s.
5. `push the chocolate chip cookie to the to_the_edge_of chopping board` — cookie overhangs the board edge. ~20 s.
6. `pick up the chocolate chip cookie from the chopping board` — gripper stopped short of full close, cookie lifted. ~13 s.
7. `place the chocolate chip cookie in the packing box` — cookie not visible outside the box. ~10 s.
8. `pick up the half apple from the chopping board` (x2, one per arm), then `place the half apple in the packing box` (x2). ~13 s + ~10 s each.
9. `pick up the club sandwich from the chopping board`, `place the club sandwich in the packing box`. ~23 s.
10. `move to the fridge` — ~10 s. `open the door of the fridge` — door swung wide, shelves visible. ~32 s.
11. `pick up the bottle of tea from the low_level fridge` (or `middle_level` / `high_level` by which shelf it is on) — bottle lifted clear. ~13 s.
12. `close the door of the fridge` — door flush. ~18 s. Do this before walking back.
13. `move to the packing box`, `place the bottle of tea in the packing box`. ~20 s.

Budget: demo mean 275 s vs limit 412 s. Steps 2-4 cost ~30 s but save two or three carries of ~1.8 m.

### What the demos do differently

- 191/200 demos move the box next to the chopping board first (onto the countertop, or onto the burner in 76 demos). The goal does not need it; it only shortens carries.
- 187/200 demos push the cookie to the board edge before picking it. Keep this; the cookie is flat (scaled 1.25 x 1.25 x 2.99 on a thin model).
- All 200 demos do the food first and the tea last, and all close the fridge before placing the tea.
- The tea pick prompt names the shelf level: low 95, middle 60, high 45 demos. Tea z is 1.31 or 1.38 m across instances 301-320.

### Hard parts and hacks

- Fridge door: opening needs the handle; handle width vs 44 mm not verified. Demos take ~32 s for it, the slowest skill.
- Tea bottle high in the fridge (z 1.31-1.38): reach past the open door; clutter on the shelf unknown.
- Cookie: flat, only graspable once it overhangs the board edge. A VLA that skips the push will close on air.
- Apple halves and club sandwich: sizes not in custom_lists (unknown vs 44 mm). The sandwich model is scaled 0.74. Demos grasp both.
- Box position: on the same countertop (`countertop_kelker_0`) as the board, about 1.5-2 m away in most instances (box y 0.0-0.4, board y -1.5 to -1.8). In instance 315 the box already sits near the board (y -1.16); skip steps 2-4 there.
- Placing the bottle upright into the box may catch the rim and tip the box. Lower it well inside before releasing.

### Hints for the VLM

- Kitchen only. The chopping board with the four food items is on the countertop near the wall cabinets, not the sink counter. The fridge is at the far end of the kitchen near the sink counter (around x 7.8, y -2.0); tea x-y stays within ~0.2 m of the fridge centre in all 20 instances, so it sits on a shelf inside the body, not in the door.
- The packing box is a small open cardboard box on the same countertop as the board.
- Done for each food item: board empty of that item and the item visible inside the box from above.
- Done for tea: bottle visible standing or lying inside the box, not leaning on the rim.
- Done for the fridge: door flush with the body, no gap.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside half__apple.n.01_2 packing_box.n.02_1)` | no | yes |
| `(inside half__apple.n.01_1 packing_box.n.02_1)` | no | yes |
| `(inside club_sandwich.n.01_1 packing_box.n.02_1)` | no | yes |
| `(inside chocolate_chip_cookie.n.01_1 packing_box.n.02_1)` | no | yes |
| `(inside bottle__of__tea.n.01_1 packing_box.n.02_1)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?half__apple.n.01 - half__apple.n.01)
                (inside ?half__apple.n.01 ?packing_box.n.02_1)
            )
            (inside ?club_sandwich.n.01_1 ?packing_box.n.02_1) 
            (inside ?chocolate_chip_cookie.n.01_1 ?packing_box.n.02_1) 
            (inside ?bottle__of__tea.n.01_1 ?packing_box.n.02_1)
            (not 
                (open ?electric_refrigerator.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `half__apple.n.01_1` | half_apple_213 | half_apple / qusmpx | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.81 m (range 1.24-4.7) | yes, spread 0.76 m |
| `half__apple.n.01_2` | half_apple_212 | half_apple / qusmpx | kitchen_0 | table/counter (0.6-1.1 m), z 0.94 | 2.95 m (range 0.98-4.96) | yes, spread 0.9 m |
| `chopping_board.n.01_1` | chopping_board_211 | chopping_board / afwefw | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.98 m (range 1.22-4.71) | yes, spread 0.32 m |
| `countertop.n.01_1` | countertop_kelker_0 | countertop / kelker | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 2.38 m (range 1.02-4.66) | no (fixed) |
| `packing_box.n.02_1` | packing_box_210 | packing_box / cjhskr | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 2.64 m (range 1.02-4.62) | yes, spread 1.58 m |
| `club_sandwich.n.01_1` | club_sandwich_209 | club_sandwich / ablfyd | kitchen_0 | table/counter (0.6-1.1 m), z 0.96 | 3.0 m (range 1.13-4.88) | yes, spread 0.68 m |
| `bottle__of__tea.n.01_1` | bottle_of_tea_208 | bottle_of_tea / iladfg | kitchen_0 | high (1.1-1.6 m), z 1.32 | 1.64 m (range 0.88-4.32) | yes, spread 0.45 m |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 1.7 m (range 0.88-4.37) | no (fixed) |
| `chocolate_chip_cookie.n.01_1` | chocolate_chip_cookie_207 | chocolate_chip_cookie / xprsse | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 2.91 m (range 1.22-4.64) | yes, spread 0.86 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.44 m (range 0.8-2.31) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inside bottle__of__tea.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop chocolate_chip_cookie.n.01_1 chopping_board.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop club_sandwich.n.01_1 chopping_board.n.01_1)
(ontop half__apple.n.01_1 chopping_board.n.01_1)
(ontop half__apple.n.01_2 chopping_board.n.01_1)
(ontop packing_box.n.02_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching chocolate_chip_cookie.n.01_1 chopping_board.n.01_1)
(touching chopping_board.n.01_1 chocolate_chip_cookie.n.01_1)
(touching chopping_board.n.01_1 club_sandwich.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_1 half__apple.n.01_1)
(touching chopping_board.n.01_1 half__apple.n.01_2)
(touching club_sandwich.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 packing_box.n.02_1)
(touching floor.n.01_1 agent.n.01_1)
(touching half__apple.n.01_1 chopping_board.n.01_1)
(touching half__apple.n.01_2 chopping_board.n.01_1)
(touching packing_box.n.02_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 251.58 s (range 187.0-590.0). Skills per demo 23.0 (range 16-26). 95 distinct skill orders; the most common one covers 12% of demos.

Most common skill counts per demo (18% of demos): move to x9, pick up from x6, place in x5, close door x1, open door x1, place on next to x1, push to x1.

Representative demo `episode_00122300.json` (223.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the packing box` (0.0-6.6 s)
2. `pick up the packing box from the countertop` (6.6-15.3 s)
3. `move to the chopping board` (15.3-20.1 s)
4. `place the packing box on the countertop next to the right chopping board` (20.1-22.0 s)
5. `push the chocolate chip cookie to the to_the_edge_of chopping board` (22.0-37.1 s)
6. `pick up the chocolate chip cookie from the chopping board` (37.1-46.6 s)
7. `place the chocolate chip cookie in the packing box` (46.6-53.1 s)
8. `pick up the half apple from the chopping board` (53.1-66.7 s)
9. `pick up the half apple from the chopping board` (66.7-78.0 s)
10. `place the half apple in the packing box` (78.0-83.8 s)
11. `place the half apple in the packing box` (83.8-88.8 s)
12. `pick up the club sandwich from the chopping board` (88.8-106.6 s)
13. `place the club sandwich in the packing box` (106.6-116.7 s)
14. `move to the fridge` (116.7-139.9 s)
15. `open the door of the fridge` (139.9-169.5 s)
16. `pick up the bottle of tea from the low_level fridge` (169.5-185.9 s)
17. `close the door of the fridge` (185.9-195.7 s)
18. `move to the packing box` (195.7-205.7 s)
19. `place the bottle of tea in the packing box` (205.7-223.9 s)

Mean duration per skill in this task: close door 17.7 s, move to 9.5 s, open door 32.0 s, pick up from 13.4 s, place in 10.0 s, place on next to 4.7 s, push to 19.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the packing box` | 742 |
| `pick up the half apple from the chopping board` | 399 |
| `place the half apple in the packing box` | 399 |
| `place the club sandwich in the packing box` | 201 |
| `move to the fridge` | 200 |
| `open the door of the fridge` | 200 |
| `close the door of the fridge` | 200 |
| `pick up the club sandwich from the chopping board` | 199 |
| `place the chocolate chip cookie in the packing box` | 199 |
| `pick up the chocolate chip cookie from the chopping board` | 198 |
| `place the bottle of tea in the packing box` | 198 |
| `pick up the packing box from the countertop` | 191 |
| `push the chocolate chip cookie to the to_the_edge_of chopping board` | 187 |
| `move to the chocolate chip cookie` | 121 |
| `move to the club sandwich` | 120 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/12_preparing_lunch_box.json`. Planner notes: `task_docs/notes/12_preparing_lunch_box.md`.
