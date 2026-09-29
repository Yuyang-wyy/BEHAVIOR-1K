# 11 · Putting Dishes Away After Cleaning

Task name `putting_dishes_away_after_cleaning`, task index 11.

> In the kitchen, gather all eight plates from the two countertops, place them all inside a single cabinet (either one), and make sure all cabinets are closed when you're done.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 365.1 s mean (10953 steps) |
| episode time limit | 547.7 s (16430 steps at 30 Hz) |
| human base travel | 33.0487 m |
| goal literals (best ground option) | 14 |
| literals already true at start (inferred) | 6 |
| max Q short of full success | 0.571 |
| ground goal options | 6 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114057082 |

## Planner notes

**Tier:** B — eight plates, grasped by the rim, carried into a wall cabinet whose two doors must be opened and re-closed; no state change.

### Goal in plain words

- All 8 plates must end up `inside` one cabinet, the same one for all 8.
- Any of the 6 kitchen cabinets in scope may be chosen (6 ground options). The three wall cabinets `top_cabinet_lkxmne_0/1/2` and three base cabinets (`bottom_cabinet_no_top_gjeoer_0`, `bottom_cabinet_no_top_rkgjer_0`, `bottom_cabinet_fancyy_0`) are the candidates.
- All 6 cabinets must be closed at the end (`not open`, 5 % rule, PREDICATES §6).
- Plates start 4 on the bar (`bar_udatjt_0` = countertop.n.01_1, plates z ~1.06) and 4 on the sink countertop (`countertop_kelzer_0` = countertop.n.01_2, plates z ~0.90).

### Q traps

- The 6 `not open` literals are true at reset (all cabinet `joint_pos` ~0 in the template and in all 20 instances 301-320). They never score. Max partial Q = 8/14 = 0.571.
- Leaving any cabinet door ajar costs no partial Q but blocks full success (1.0). The only route above 0.571 is success.
- Splitting plates across two cabinets scores only the larger group. Pick one cabinet and put all 8 there.
- Closing a door onto a plate can push its centre out of the volume (PREDICATES §3). Close only after the last plate, then check no plate sticks out.
- A plate resting on the cabinet top or on the counter under it is not inside.
- Closed-loop ft40k on 311 scored Q=0.50, i.e. 7 of 8 plates inside. Door state at the end is not recorded; partial Q ignores it.

### Minimal plan

1. `move to the top cabinet` — base stopped, facing the counter under the wall cabinet above `countertop_kelker_0`. ~12 s.
2. `open the door of the right_door top cabinet` — right door visibly swung open. ~26 s.
3. `open the door of the left_door top cabinet` — left door open, shelf visible. ~26 s.
4. `move to the plate` — base stopped near the sink counter plates. ~12 s.
5. `pick up the plate from the countertop` — gripper closed, stopped short of full close, plate lifted off the counter. ~8 s.
6. Repeat 4-5 for a second plate with the other arm (demos always carry two plates per trip).
7. `move to the top cabinet` — ~12 s.
8. `place the plate in the low_level top cabinet` (first two plates) or `place the plate on the plate` (later ones, stacking) — gripper open, plate on the shelf behind the door line. ~10 s each.
9. Repeat 4-8 for the other sink-counter pair, then twice with `pick up the plate from the bar`.
10. `close the door of the left_door top cabinet`, then `close the door of the right_door top cabinet` — both doors flush with the frame. ~14 s each.

Budget: demo mean 365 s vs limit 548 s. Four two-plate trips fit; eight one-plate trips probably do not (8 x ~40 s travel/pick/place plus ~80 s of doors is tight, estimate only).

### What the demos do differently

- All 200 demos use `top_cabinet_lkxmne_1` (cabinet.n.01_3); 2 of them also have a stray `place the plate in the low_level countertop` segment. No demo uses a base cabinet, so the base cabinets have no trained prompts (closest: `place the plate in the low_level top cabinet`).
- All demos pick exactly 8 times and carry two plates per trip (one per hand), then place both.
- Plates after the first two are stacked: `place the plate on the plate` (1200 segments). That still scores as long as each plate's centre is inside the cabinet volume.
- Demos open both doors first and close both at the very end. That order is correct; keep it.
- The order of counter vs bar pairs varies (29 distinct orders); it does not matter.

### Hard parts and hacks

- Reach: the wall cabinet centre is at z 1.79. Placing into it needs the trunk raised and arms extended high; tipping risk is low with plates but the shelf height is not verified.
- Stacking 8 plates on one shelf: whether 8 stacked plates fit under the upper shelf/cabinet top is not verified. A stack that slides out past the door line loses literals and can block the door.
- Grasp: plates are wider than 44 mm, so only the rim is graspable. Plate models xfjmld, luhkiz, ntedfx, pkkgzc; rim thickness unknown. Demos show rim grasps work.
- Door handles on `lkxmne` doors: width not verified; the demos open them.
- Door closing must be within ~4.5° of shut per door; a rebound fails success silently.
- Unverified alternative: `bottom_cabinet_no_top_gjeoer_0` sits right under the same wall cabinet (z 0.42). It avoids high reach but needs low bending and has 4 joints (all must be closed), and no demo prompt covers it.

### Hints for the VLM

- Kitchen only. Plates are on the long bar (farther from the wall cabinets, higher) and on the countertop around the sink.
- Target: the middle one of three identical wall cabinets over the countertop without a sink (`top_cabinet_lkxmne_1`, around x 4.0, y -0.5). The other two are distractors of the same model; any works for the goal but only the middle one has demo coverage.
- A water glass is also in the kitchen; ignore it.
- Done for `inside`: no plate visible on either counter; stacked plates visible on the cabinet shelf behind the door plane.
- Done for `not open`: both wall-cabinet doors flush, no gap; also check no base cabinet door was bumped open.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside plate.n.04_1 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_3 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_6 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_2 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_7 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_5 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_8 cabinet.n.01_3)` | no | yes |
| `(inside plate.n.04_4 cabinet.n.01_3)` | no | yes |
| `(not open cabinet.n.01_3))` | yes | never (already true) |
| `(not open cabinet.n.01_5))` | yes | never (already true) |
| `(not open cabinet.n.01_6))` | yes | never (already true) |
| `(not open cabinet.n.01_2))` | yes | never (already true) |
| `(not open cabinet.n.01_4))` | yes | never (already true) |
| `(not open cabinet.n.01_1))` | yes | never (already true) |

The goal has 6 ground options (14 literals x6); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists 
                (?cabinet.n.01 - cabinet.n.01) 
                (forall 
                    (?plate.n.04 - plate.n.04) 
                    (inside ?plate.n.04 ?cabinet.n.01)
                )
            )
            (forall
                (?cabinet.n.01 - cabinet.n.01)
                (not
                    (open ?cabinet.n.01)
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
| `plate.n.04_1` | plate_214 | plate / xfjmld | kitchen_0 | table/counter (0.6-1.1 m), z 1.07 | 1.61 m (range 0.81-3.41) | yes, spread 2.74 m |
| `plate.n.04_2` | plate_213 | plate / luhkiz | kitchen_0 | table/counter (0.6-1.1 m), z 1.06 | 1.9 m (range 1.0-3.62) | yes, spread 2.85 m |
| `plate.n.04_3` | plate_212 | plate / luhkiz | kitchen_0 | table/counter (0.6-1.1 m), z 1.06 | 1.94 m (range 0.76-3.71) | yes, spread 2.83 m |
| `plate.n.04_4` | plate_211 | plate / luhkiz | kitchen_0 | table/counter (0.6-1.1 m), z 1.06 | 2.16 m (range 0.94-3.58) | yes, spread 2.78 m |
| `plate.n.04_5` | plate_210 | plate / xfjmld | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.3 m (range 0.98-3.66) | yes, spread 2.32 m |
| `plate.n.04_6` | plate_209 | plate / ntedfx | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.2 m (range 0.82-3.82) | yes, spread 2.71 m |
| `plate.n.04_7` | plate_208 | plate / pkkgzc | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.55 m (range 0.99-3.84) | yes, spread 2.69 m |
| `plate.n.04_8` | plate_207 | plate / ntedfx | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.98 m (range 0.8-3.64) | yes, spread 2.78 m |
| `countertop.n.01_1` | bar_udatjt_0 | bar / udatjt | kitchen_0 | table/counter (0.6-1.1 m), z 0.66 | 2.17 m (range 1.18-2.52) | no (fixed) |
| `countertop.n.01_2` | countertop_kelzer_0 | countertop / kelzer | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.99 m (range 1.26-3.57) | no (fixed) |
| `cabinet.n.01_1` | bottom_cabinet_no_top_gjeoer_0 | bottom_cabinet_no_top / gjeoer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 1.55 m (range 1.01-4.55) | no (fixed) |
| `cabinet.n.01_2` | bottom_cabinet_fancyy_0 | bottom_cabinet / fancyy | kitchen_0 | high (1.1-1.6 m), z 1.12 | 3.87 m (range 1.08-4.97) | no (fixed) |
| `cabinet.n.01_3` | top_cabinet_lkxmne_1 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 1.67 m (range 1.07-4.6) | no (fixed) |
| `cabinet.n.01_4` | top_cabinet_lkxmne_2 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 1.77 m (range 1.04-4.84) | no (fixed) |
| `cabinet.n.01_5` | top_cabinet_lkxmne_0 | top_cabinet / lkxmne | kitchen_0 | very high (>1.6 m), z 1.79 | 2.62 m (range 1.5-4.64) | no (fixed) |
| `cabinet.n.01_6` | bottom_cabinet_no_top_rkgjer_0 | bottom_cabinet_no_top / rkgjer | kitchen_0 | low (0.25-0.6 m), z 0.42 | 2.07 m (range 1.28-3.62) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.43 m (range 0.74-2.24) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 kitchen)
(inroom cabinet.n.01_2 kitchen)
(inroom cabinet.n.01_3 kitchen)
(inroom cabinet.n.01_4 kitchen)
(inroom cabinet.n.01_5 kitchen)
(inroom cabinet.n.01_6 kitchen)
(inroom countertop.n.01_1 kitchen)
(inroom countertop.n.01_2 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop plate.n.04_1 countertop.n.01_1)
(ontop plate.n.04_2 countertop.n.01_1)
(ontop plate.n.04_3 countertop.n.01_1)
(ontop plate.n.04_4 countertop.n.01_1)
(ontop plate.n.04_5 countertop.n.01_2)
(ontop plate.n.04_6 countertop.n.01_2)
(ontop plate.n.04_7 countertop.n.01_2)
(ontop plate.n.04_8 countertop.n.01_2)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 plate.n.04_1)
(touching countertop.n.01_1 plate.n.04_2)
(touching countertop.n.01_1 plate.n.04_3)
(touching countertop.n.01_1 plate.n.04_4)
(touching countertop.n.01_2 plate.n.04_5)
(touching countertop.n.01_2 plate.n.04_6)
(touching countertop.n.01_2 plate.n.04_7)
(touching countertop.n.01_2 plate.n.04_8)
(touching floor.n.01_1 agent.n.01_1)
(touching plate.n.04_1 countertop.n.01_1)
(touching plate.n.04_2 countertop.n.01_1)
(touching plate.n.04_3 countertop.n.01_1)
(touching plate.n.04_4 countertop.n.01_1)
(touching plate.n.04_5 countertop.n.01_2)
(touching plate.n.04_6 countertop.n.01_2)
(touching plate.n.04_7 countertop.n.01_2)
(touching plate.n.04_8 countertop.n.01_2)
```

## What the human demos did

200 annotated demos. Length 352.67 s (range 262.1-536.4). Skills per demo 32.0 (range 29-33). 29 distinct skill orders; the most common one covers 22% of demos.

Most common skill counts per demo (40% of demos): move to x12, pick up from x8, place on x6, close door x2, open door x2, place in x2.

Representative demo `episode_00111340.json` (370.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the top cabinet` (0.0-11.7 s)
2. `open the door of the right_door top cabinet` (11.7-39.5 s)
3. `open the door of the left_door top cabinet` (39.5-51.0 s)
4. `move to the plate` (51.0-70.2 s)
5. `pick up the plate from the countertop` (70.2-78.3 s)
6. `move to the plate` (78.3-78.7 s)
7. `pick up the plate from the countertop` (78.7-84.4 s)
8. `move to the top cabinet` (84.4-96.5 s)
9. `place the plate in the low_level top cabinet` (96.5-110.4 s)
10. `place the plate in the low_level top cabinet` (110.4-115.2 s)
11. `move to the plate` (116.2-123.0 s)
12. `pick up the plate from the countertop` (123.0-132.3 s)
13. `move to the plate` (132.3-146.2 s)
14. `pick up the plate from the countertop` (146.2-151.1 s)
15. `move to the top cabinet` (151.1-165.2 s)
16. `place the plate on the plate` (165.2-182.1 s)
17. `place the plate on the plate` (182.1-191.1 s)
18. `move to the plate` (191.1-215.6 s)
19. `pick up the plate from the bar` (215.6-226.7 s)
20. `move to the plate` (226.7-232.0 s)
21. `pick up the plate from the bar` (232.0-238.2 s)
22. `move to the top cabinet` (238.2-263.1 s)
23. `place the plate on the plate` (263.1-274.5 s)
24. `place the plate on the plate` (274.5-280.3 s)
25. `move to the plate` (280.3-298.1 s)
26. `pick up the plate from the bar` (298.1-305.7 s)
27. `move to the plate` (305.7-307.7 s)
28. `pick up the plate from the bar` (307.7-315.6 s)
29. `move to the top cabinet` (315.6-327.9 s)
30. `place the plate on the plate` (327.9-339.4 s)
31. `place the plate on the plate` (339.4-345.3 s)
32. `close the door of the left_door top cabinet` (345.3-355.7 s)
33. `close the door of the right_door top cabinet` (355.7-370.6 s)

Mean duration per skill in this task: close door 14.4 s, move to 11.6 s, open door 25.7 s, pick up from 8.4 s, place in 9.7 s, place on 10.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the plate` | 1340 |
| `place the plate on the plate` | 1200 |
| `move to the top cabinet` | 999 |
| `pick up the plate from the countertop` | 800 |
| `pick up the plate from the bar` | 800 |
| `place the plate in the low_level top cabinet` | 398 |
| `open the door of the right_door top cabinet` | 200 |
| `open the door of the left_door top cabinet` | 200 |
| `close the door of the left_door top cabinet` | 200 |
| `close the door of the right_door top cabinet` | 199 |
| `place the plate in the low_level countertop` | 2 |
| `close the door of the right top cabinet` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/11_putting_dishes_away_after_cleaning.json`. Planner notes: `task_docs/notes/11_putting_dishes_away_after_cleaning.md`.
