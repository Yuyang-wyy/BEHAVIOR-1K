# 02 · Putting Away Halloween Decorations

Task name `putting_away_Halloween_decorations`, task index 2.

> Place each of the two pumpkins and all three candles from the living room inside a cabinet in the living room (use any cabinet), then make sure every cabinet is closed, and position the cauldron so it is next to a table in the living room.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | living_room |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 459.6 s mean (13788 steps) |
| episode time limit | 689.4 s (20682 steps at 30 Hz) |
| human base travel | 47.1353 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.857 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.57; ft24k@sulab1 Q=0.57; ft40k@sulab1 Q=0.29; ft40k@local Q=0.29; ft10k@sulab1 Q=0.14; pt0@sulab1 Q=0.57 |
| demo video | https://player.vimeo.com/video/1114054409 |

## Planner notes

**Tier:** C — five wide floor objects into a low drawer, a 29 cm cauldron to carry, plus drawer open/close. None of the objects fits the 44 mm span.

### Goal in plain words

Both pumpkins and all three pillar candles must end inside a living-room cabinet. Only one cabinet is in scope: `bottom_cabinet_rhdbzv_0`, a low 2.34 m console with two drawers. Any mix of drawers is fine. The cauldron must be `nextto` the coffee table, the only table in the living room. At the end every drawer of that cabinet must be closed.

### Q traps

- 7 literals. `not open cabinet` is true at start: both drawer joints are ~1e-10 in the template and all 20 instances (checked). It never scores but blocks success. Max partial Q = 6/7 = 0.857.
- Opening a drawer costs no Q; leaving it open only loses success. If time runs short, stop putting items in rather than skipping the close.
- The cauldron starts 0.97-2.53 m from the coffee-table centre, so `nextto` is false at start in all instances.
- `nextto` threshold: cauldron 0.29 x 0.29 x 0.25 m, coffee table 0.80 x 1.66 x 0.41 m, so L/6 ~ 0.20 m. The AABB gap must be under ~0.2 m (PREDICATES §5). Aim for near touching.
- The not-open literal counts both drawers. A drawer bumped ajar (> 5 % of its travel) during placing blocks success.
- Closing the drawer can snag an item on the front edge and pull its centre out of the volume. Re-check after closing.
- Whether drawers carry fillable volume is not verified in PREDICATES §18. Indirect evidence: zs_pt50 scored 4/7 on 311, which needs at least 3 `inside` literals.

### Minimal plan

1. `move to the cauldron` — base stopped at cauldron. ~15 s.
2. `pick up the cauldron from the floors` — cauldron clear of floor. ~19 s.
3. `move to the coffee table` — ~15 s.
4. `place the cauldron on the floors next to the in_front_of coffee table` — cauldron on floor, under ~0.2 m from the table side in depth. ~13 s.
5. `move to the bottom cabinet` then `open the drawer of the right bottom cabinet` — drawer visibly pulled out. ~15 + 28 s.
6. `move to the pillar candle`, `pick up the pillar candle from the floors`, then again for a second candle with the other gripper. ~2 x 34 s.
7. `move to the bottom cabinet`, `place the pillar candle in the right bottom cabinet` x2 — both grippers empty, candles below the drawer rim. ~15 + 2 x 17 s.
8. Same for the third candle and one pumpkin (`move to the pumpkin`, `pick up the pumpkin from the floors`, `place the pumpkin in the right bottom cabinet`), then the last pumpkin. ~2 trips x ~115 s.
9. `close the drawer of the right bottom cabinet` — drawer front flush with the cabinet. ~18 s.

Budget ~500 s against a 689 s limit (20682 steps). Using one drawer skips one open (28 s) and one close (18 s) versus the demos. Space check: right drawer link is 1.25 m wide, 0.36 m deep; 3 candles (0.10 m) plus 2 pumpkins (0.15 m) need ~0.6 m.

### What the demos do differently

- All demos open both drawers: candles mostly go to the "left" drawer, pumpkins to the "right". One drawer is enough.
- Humans carry two items at once (one per hand) and place both before walking back. Keep this: it halves the trips.
- 92 distinct orders; the cauldron is often done first. Order is free, but close the drawer last.
- "left bottom cabinet" and "right bottom cabinet" are the two drawers of the same console, not two cabinets.

### Hard parts and hacks

- Object sizes (asset bbox_size, scale 1.0): pumpkin 150 x 149 x 124 mm, pillar candle 100 x 100 x 139 mm, cauldron 291 x 291 x 250 mm. None has a dimension under 44 mm. A pumpkin stem or cauldron handle width is unverified. Policies did move items on 311 (zs_pt50, ft24k, pt0 all 0.57).
- The drawer sits at floor level (cabinet top 0.41 m). Placing needs a low trunk pose and reaching down over the drawer front.
- Drawer handle width is unverified against 44 mm. Closing can be a push (no grasp).
- Pushing the cauldron across the floor to the table would satisfy `nextto` without a grasp. No trained prompt; closest: `push the <obj> to the <target>` template, e.g. `push the cauldron to the coffee table` (untested wording).
- Round shapes: a dropped pumpkin or tipped candle rolls. Release low, inside the drawer.
- Closed-loop on 311: zs_pt50 0.57, ft24k 0.57, pt0 0.57, ft40k 0.29, ft10k 0.14.

### Hints for the VLM

- All task objects are on the living-room floor: 2 pumpkins, 3 pillar candles (short fat cylinders), 1 cauldron (pot shape, ~29 cm).
- Cabinet: long low console (2.34 m x 0.41 m x 0.41 m) against a wall, with two wide drawers. It is the only cabinet in the living room. Kitchen cabinets are out of scope and do not count.
- Coffee table: the low table (top ~0.41 m) in the living room (0.80 x 1.66 m). The kitchen breakfast table does not count.
- Distractors: sofa, shelf, fireplace, a living-room countertop.
- Done: no pumpkins or candles visible on the floor, both drawer fronts flush, cauldron on the floor touching or almost touching the coffee table.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside pumpkin.n.02_2 cabinet.n.01_1)` | no | yes |
| `(inside pumpkin.n.02_1 cabinet.n.01_1)` | no | yes |
| `(inside candle.n.01_3 cabinet.n.01_1)` | no | yes |
| `(inside candle.n.01_1 cabinet.n.01_1)` | no | yes |
| `(inside candle.n.01_2 cabinet.n.01_1)` | no | yes |
| `(nextto caldron.n.01_1 table.n.02_1)` | no | yes |
| `(not open cabinet.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?pumpkin.n.02 - pumpkin.n.02)
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?pumpkin.n.02 ?cabinet.n.01)
                )
            ) 
            (forall 
                (?candle.n.01 - candle.n.01) 
                (exists 
                    (?cabinet.n.01 - cabinet.n.01) 
                    (inside ?candle.n.01 ?cabinet.n.01)
                )
            )
            (exists
                (?table.n.02 - table.n.02)
                (nextto ?caldron.n.01_1 ?table.n.02)
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
| `pumpkin.n.02_1` | pumpkin_94 | pumpkin / apitmi | living_room_0 | floor, z 0.05 | 2.33 m (range 0.63-3.34) | yes, spread 4.17 m |
| `pumpkin.n.02_2` | pumpkin_93 | pumpkin / apitmi | living_room_0 | floor, z 0.05 | 2.01 m (range 0.63-3.99) | yes, spread 4.87 m |
| `floor.n.01_1` | floors_ulujpr_0 | floors / ulujpr | living_room_0 | floor, z -0.15 | 1.52 m (range 0.91-2.11) | no (fixed) |
| `caldron.n.01_1` | cauldron_92 | cauldron / zndohl | living_room_0 | floor, z 0.12 | 2.33 m (range 1.01-3.33) | yes, spread 4.31 m |
| `table.n.02_1` | coffee_table_koagbh_0 | coffee_table / koagbh | living_room_0 | low (0.25-0.6 m), z 0.36 | 1.89 m (range 1.29-2.14) | no |
| `candle.n.01_1` | pillar_candle_91 | pillar_candle / cxswbc | living_room_0 | floor, z 0.06 | 2.13 m (range 0.68-3.52) | yes, spread 4.15 m |
| `candle.n.01_2` | pillar_candle_90 | pillar_candle / cxswbc | living_room_0 | floor, z 0.06 | 1.54 m (range 0.62-3.03) | yes, spread 3.93 m |
| `candle.n.01_3` | pillar_candle_89 | pillar_candle / cxswbc | living_room_0 | floor, z 0.06 | 1.86 m (range 0.86-3.57) | yes, spread 4.5 m |
| `cabinet.n.01_1` | bottom_cabinet_rhdbzv_0 | bottom_cabinet / rhdbzv | living_room_0 | floor, z 0.21 | 1.72 m (range 0.96-3.49) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(inroom table.n.02_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop caldron.n.01_1 floor.n.01_1)
(ontop candle.n.01_1 floor.n.01_1)
(ontop candle.n.01_2 floor.n.01_1)
(ontop candle.n.01_3 floor.n.01_1)
(ontop pumpkin.n.02_1 floor.n.01_1)
(ontop pumpkin.n.02_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching caldron.n.01_1 floor.n.01_1)
(touching candle.n.01_1 floor.n.01_1)
(touching candle.n.01_2 floor.n.01_1)
(touching candle.n.01_3 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 caldron.n.01_1)
(touching floor.n.01_1 candle.n.01_1)
(touching floor.n.01_1 candle.n.01_2)
(touching floor.n.01_1 candle.n.01_3)
(touching floor.n.01_1 pumpkin.n.02_1)
(touching floor.n.01_1 pumpkin.n.02_2)
(touching pumpkin.n.02_1 floor.n.01_1)
(touching pumpkin.n.02_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 462.43 s (range 228.9-621.8). Skills per demo 27.0 (range 22-28). 92 distinct skill orders; the most common one covers 6% of demos.

Most common skill counts per demo (24% of demos): move to x12, pick up from x6, place in x5, close drawer x2, open drawer x2, place on next to x1.

Representative demo `episode_00021210.json` (479.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the cauldron` (0.0-20.4 s)
2. `pick up the cauldron from the floors` (20.4-42.2 s)
3. `move to the coffee table` (42.2-50.2 s)
4. `place the cauldron on the floors next to the in_front_of coffee table` (50.2-57.1 s)
5. `move to the bottom cabinet` (57.1-72.2 s)
6. `open the drawer of the left bottom cabinet` (72.2-94.6 s)
7. `move to the pillar candle` (94.6-103.0 s)
8. `pick up the pillar candle from the floors` (103.0-119.2 s)
9. `move to the pillar candle` (119.2-133.0 s)
10. `pick up the pillar candle from the floors` (133.0-149.5 s)
11. `move to the bottom cabinet` (149.5-179.5 s)
12. `place the pillar candle in the left bottom cabinet` (179.5-196.7 s)
13. `place the pillar candle in the left bottom cabinet` (196.7-203.2 s)
14. `move to the pillar candle` (203.2-222.9 s)
15. `pick up the pillar candle from the floors` (222.9-235.6 s)
16. `move to the bottom cabinet` (235.6-271.0 s)
17. `place the pillar candle in the left bottom cabinet` (271.0-287.6 s)
18. `close the drawer of the left bottom cabinet` (287.6-304.4 s)
19. `move to the bottom cabinet` (304.4-319.9 s)
20. `open the drawer of the right bottom cabinet` (319.9-342.7 s)
21. `move to the pumpkin` (342.7-351.3 s)
22. `pick up the pumpkin from the floors` (351.3-367.2 s)
23. `move to the pumpkin` (367.2-394.9 s)
24. `pick up the pumpkin from the floors` (394.9-410.1 s)
25. `move to the bottom cabinet` (410.1-436.9 s)
26. `place the pumpkin in the right bottom cabinet` (436.9-452.0 s)
27. `place the pumpkin in the right bottom cabinet` (452.0-457.5 s)
28. `close the drawer of the right bottom cabinet` (457.5-479.7 s)

Mean duration per skill in this task: close drawer 17.7 s, move to 14.8 s, open drawer 27.7 s, pick up from 18.9 s, place in 16.8 s, place on next to 13.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the bottom cabinet` | 981 |
| `pick up the pillar candle from the floors` | 599 |
| `move to the pillar candle` | 562 |
| `pick up the pumpkin from the floors` | 399 |
| `move to the pumpkin` | 383 |
| `place the pillar candle in the left bottom cabinet` | 324 |
| `place the pillar candle in the right bottom cabinet` | 205 |
| `close the drawer of the left bottom cabinet` | 203 |
| `open the drawer of the left bottom cabinet` | 200 |
| `open the drawer of the right bottom cabinet` | 200 |
| `move to the cauldron` | 200 |
| `pick up the cauldron from the floors` | 200 |
| `place the cauldron on the floors next to the in_front_of coffee table` | 200 |
| `close the drawer of the right bottom cabinet` | 197 |
| `place the pumpkin in the right bottom cabinet` | 195 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/02_putting_away_Halloween_decorations.json`. Planner notes: `task_docs/notes/02_putting_away_Halloween_decorations.md`.
