# 54 · Putting Away Toys

Task name `putting_away_toys`, task index 54.

> Pick up all the toy figures from the floor and put them inside the toy boxes.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | dining_room, living_room |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 376.6 s mean (11296 steps) |
| episode time limit | 564.8 s (16945 steps at 30 Hz) |
| human base travel | 35.1468 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 256 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.75; ft40k@local Q=0.75 |
| demo video | https://www.youtube.com/embed/StbSZCTn7D4 |

## Planner notes

**Tier:** B. Eight small rigid toy figures (bbox 0.08-0.16 m long, 0.04-0.09 m tall) into two open boxes; closed loop already reached Q = 0.75 on 311, so the grasps work in practice even though no bbox axis is clearly under 44 mm.

### Goal in plain words

- All 8 toy figures must end inside a toy box. Each figure may go in either box (256 ground options), so mixing boxes is fine.
- Figures 1-4 start on the living-room floor, 5-8 on the dining-room floor (`:init`; instance x-coordinates agree: living figures at x 9.4-17.3, dining figures at x 5.1-9.3).
- Toy box 1 (`qgfbdj`, 0.46 x 0.80 x 0.40 m) sits on the living-room floor. Toy box 2 (`kvithq` scaled 5x, 0.59 x 0.63 x 0.31 m) sits on the dining breakfast table, rim at roughly 1.1 m.
- No doors, lids or switches are involved. Neither box has joints in the template.

### Q traps

- No literal is true at reset. Max Q = 1.0; each figure is worth 1/8.
- `inside` tests only the figure's AABB centre against the box's fillable volume (PREDICATES §3). A figure caught on the rim or lying across the edge does not count. Drop it well inside.
- Box 1 is on the floor and is not fixed. Driving into it moves it; box 2 can be knocked off the table, spilling its figures and losing their literals.
- Scoring reads only the final state. Check that earlier figures are still in the box after each drop.

### Minimal plan

Two figures per trip, one per hand, as in the demos. Times are demo means.

1. `move to the toy figure` — base stopped with a figure on the floor within reach. ~17 s.
2. `pick up the toy figure from the floors` — gripper closed short of fully closed, figure gone from the floor. ~12 s.
3. `move to the toy figure` / `pick up the toy figure from the floors` with the other hand. ~30 s.
4. `move to the toy box` — nearest box in view (floor box in the living room, table box in the dining room). ~20 s.
5. `place the toy figure in the toy box` twice — figures visible inside the box, grippers open. ~7 s each.
6. Repeat 1-5 for the other living-room pair, then for the two dining-room pairs using the box on the breakfast table.

Budget: 4 trips x ~90 s = ~360 s against a 565 s limit. Leaves ~200 s for re-grasps.

### What the demos do differently

- 48% of demos use exactly this pattern (move to x12, pick up x8, place in x8); 40 distinct orders.
- About 46 of 1600 picks add `hand over the toy figure`. Not needed.
- One demo picked up a toy box. Not needed and not advised.
- Humans often chain figures regardless of room; the nearest box is always the right box.

### Hard parts and hacks

- Grasp on figures lying on the floor: bboxes are 76-113 mm across the short horizontal axis, so the 44 mm jaw span must close on a narrower part (limb, neck, base). Which part works per model is unverified. Expect several retries per figure.
- Picking from the floor needs the trunk folded down; carrying two figures while driving 5-10 m between rooms risks dropping one. Check both grippers after every move.
- Box 2 is high (table top ~0.78 m plus a 0.31 m box). Raise the arm above the rim before releasing to avoid knocking the box off the table.
- Travel dominates: the humans drive 35 m. Figures in the dining room are 3-12 m from the start.
- Cheap check: after each place, the figure should be seen inside the box outline in the head camera; if it sits on the rim, push it in with the open gripper.

### Hints for the VLM

- Scene `house_single_floor`. The robot starts in the living room (sofas, wall-mounted TV, gas fireplace, coffee table). The dining room has one long breakfast table with 6 chairs; the box there sits on the table top.
- Toy figures are small figurines (under 0.16 m) lying on the floor. No figure starts under the dining table in any of the 20 instances.
- There are exactly 2 toy boxes and 8 figures; no same-category distractors.
- Done looks like: no figures visible on either floor; all eight inside the two boxes.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside toy_figure.n.01_5 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_3 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_1 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_8 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_4 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_6 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_2 toy_box.n.01_1)` | no | yes |
| `(inside toy_figure.n.01_7 toy_box.n.01_1)` | no | yes |

The goal has 256 ground options (8 literals x256); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?toy_figure.n.01 - toy_figure.n.01) 
                (exists 
                    (?toy_box.n.01 - toy_box.n.01) 
                    (inside ?toy_figure.n.01 ?toy_box.n.01)
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
| `toy_figure.n.01_1` | toy_figure_249 | toy_figure / acymin | living_room_0 | floor, z 0.03 | 2.06 m (range 0.69-8.04) | yes, spread 9.37 m |
| `toy_figure.n.01_2` | toy_figure_248 | toy_figure / aihmqy | living_room_0 | floor, z 0.03 | 2.88 m (range 1.03-6.93) | yes, spread 9.01 m |
| `toy_figure.n.01_3` | toy_figure_247 | toy_figure / vcmcoi | living_room_0 | floor, z 0.02 | 2.33 m (range 0.38-6.08) | yes, spread 8.26 m |
| `toy_figure.n.01_4` | toy_figure_246 | toy_figure / gnofgv | living_room_0 | floor, z 0.02 | 2.69 m (range 0.72-7.06) | yes, spread 8.58 m |
| `toy_figure.n.01_5` | toy_figure_245 | toy_figure / zuntus | dining_room_0 | floor, z 0.02 | 7.31 m (range 3.92-11.83) | yes, spread 4.8 m |
| `toy_figure.n.01_6` | toy_figure_244 | toy_figure / lfxygp | dining_room_0 | floor, z 0.02 | 7.11 m (range 3.62-11.74) | yes, spread 4.73 m |
| `toy_figure.n.01_7` | toy_figure_243 | toy_figure / fnueyn | dining_room_0 | floor, z 0.02 | 7.93 m (range 2.74-11.47) | yes, spread 4.85 m |
| `toy_figure.n.01_8` | toy_figure_242 | toy_figure / orunry | dining_room_0 | floor, z 0.02 | 8.29 m (range 2.59-11.82) | yes, spread 4.77 m |
| `floor.n.01_1` | floors_uzsntg_0 | floors / uzsntg | living_room_0 | floor, z -0.14 | 2.08 m (range 0.66-4.22) | no (fixed) |
| `floor.n.01_2` | floors_qgmjvd_0 | floors / qgmjvd | dining_room_0 | floor, z -0.14 | 7.31 m (range 5.1-10.19) | no (fixed) |
| `toy_box.n.01_1` | toy_box_241 | toy_box / qgfbdj | living_room_0 | floor, z 0.16 | 2.64 m (range 0.85-7.03) | yes, spread 8.6 m |
| `toy_box.n.01_2` | toy_box_240 | toy_box / kvithq | dining_room_0 | table/counter (0.6-1.1 m), z 0.93 | 6.67 m (range 3.43-10.5) | yes, spread 2.6 m |
| `table.n.02_1` | breakfast_table_rhjoby_0 | breakfast_table / rhjoby | dining_room_0 | table/counter (0.6-1.1 m), z 0.76 | 6.82 m (range 4.62-9.76) | no |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "dining_room",
  "living_room"
 ],
 "house_single_floor": {
  "whitelist": {
   "toy_box.n.01": {
    "toy_box": {
     "qgfbdj": null,
     "kvithq": 5.0
    }
   },
   "toy_figure.n.01": {
    "toy_figure": {
     "aihmqy": null,
     "gnofgv": null,
     "fnueyn": null,
     "lfxygp": null,
     "acymin": null,
     "vcmcoi": null,
     "zuntus": null,
     "orunry": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 living_room)
(inroom floor.n.01_2 dining_room)
(inroom table.n.02_1 dining_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop toy_box.n.01_1 floor.n.01_1)
(ontop toy_box.n.01_2 table.n.02_1)
(ontop toy_figure.n.01_1 floor.n.01_1)
(ontop toy_figure.n.01_2 floor.n.01_1)
(ontop toy_figure.n.01_3 floor.n.01_1)
(ontop toy_figure.n.01_4 floor.n.01_1)
(ontop toy_figure.n.01_5 floor.n.01_2)
(ontop toy_figure.n.01_6 floor.n.01_2)
(ontop toy_figure.n.01_7 floor.n.01_2)
(ontop toy_figure.n.01_8 floor.n.01_2)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 toy_box.n.01_1)
(touching floor.n.01_1 toy_figure.n.01_1)
(touching floor.n.01_1 toy_figure.n.01_2)
(touching floor.n.01_1 toy_figure.n.01_3)
(touching floor.n.01_1 toy_figure.n.01_4)
(touching floor.n.01_2 toy_figure.n.01_5)
(touching floor.n.01_2 toy_figure.n.01_6)
(touching floor.n.01_2 toy_figure.n.01_7)
(touching floor.n.01_2 toy_figure.n.01_8)
(touching table.n.02_1 toy_box.n.01_2)
(touching toy_box.n.01_1 floor.n.01_1)
(touching toy_box.n.01_2 table.n.02_1)
(touching toy_figure.n.01_1 floor.n.01_1)
(touching toy_figure.n.01_2 floor.n.01_1)
(touching toy_figure.n.01_3 floor.n.01_1)
(touching toy_figure.n.01_4 floor.n.01_1)
(touching toy_figure.n.01_5 floor.n.01_2)
(touching toy_figure.n.01_6 floor.n.01_2)
(touching toy_figure.n.01_7 floor.n.01_2)
(touching toy_figure.n.01_8 floor.n.01_2)
```

## What the human demos did

200 annotated demos. Length 377.43 s (range 241.6-614.17). Skills per demo 28.0 (range 26-30). 40 distinct skill orders; the most common one covers 44% of demos.

Most common skill counts per demo (48% of demos): move to x12, pick up from x8, place in x8.

Representative demo `episode_00541330.json` (369.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the toy figure` (0.0-9.0 s)
2. `pick up the toy figure from the floors` (9.0-23.0 s)
3. `move to the toy figure` (23.0-37.0 s)
4. `pick up the toy figure from the floors` (37.0-45.0 s)
5. `move to the toy box` (45.0-56.0 s)
6. `place the toy figure in the toy box` (56.0-60.0 s)
7. `place the toy figure in the toy box` (60.0-63.0 s)
8. `move to the toy figure` (63.0-82.0 s)
9. `pick up the toy figure from the floors` (82.0-89.0 s)
10. `move to the toy figure` (89.0-97.0 s)
11. `pick up the toy figure from the floors` (97.0-104.0 s)
12. `move to the toy box` (104.0-129.0 s)
13. `place the toy figure in the toy box` (129.0-132.0 s)
14. `place the toy figure in the toy box` (132.0-136.0 s)
15. `move to the toy figure` (136.0-171.0 s)
16. `pick up the toy figure from the floors` (171.0-180.0 s)
17. `move to the toy figure` (180.0-199.0 s)
18. `pick up the toy figure from the floors` (199.0-206.0 s)
19. `move to the toy box` (206.0-238.0 s)
20. `place the toy figure in the toy box` (238.0-242.0 s)
21. `place the toy figure in the toy box` (242.0-252.0 s)
22. `move to the toy figure` (252.0-270.7 s)
23. `pick up the toy figure from the floors` (270.7-287.0 s)
24. `move to the toy figure` (287.0-300.0 s)
25. `pick up the toy figure from the floors` (300.0-309.0 s)
26. `move to the toy box` (309.0-328.0 s)
27. `place the toy figure in the toy box` (328.0-354.0 s)
28. `place the toy figure in the toy box` (354.0-369.0 s)

Mean duration per skill in this task: hand over 11.1 s, move to 18.3 s, pick up from 12.5 s, place in 7.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the toy figure from the floors` | 1598 |
| `place the toy figure in the toy box` | 1593 |
| `move to the toy figure` | 1529 |
| `move to the toy box` | 827 |
| `hand over the toy figure` | 46 |
| `pick up the toy box from the floors` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/54_putting_away_toys.json`. Planner notes: `task_docs/notes/54_putting_away_toys.md`.
