# 46 · Cook Bacon

Task name `cook_bacon`, task index 46.

> Take the tray with six slices of bacon out of the refrigerator in the kitchen, cook all six slices in the frying pan on the stove until they're cooked, and make sure the refrigerator is closed when you're done.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 256.0 s mean (7679 steps) |
| episode time limit | 384.0 s (11519 steps at 30 Hz) |
| human base travel | 20.9167 m |
| goal literals (best ground option) | 7 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.857 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114061497 |

## Planner notes

**Tier:** D — heat six bacon slices to 63 °C on the burner, after taking a tray out of the fridge and closing the fridge again.

### Goal in plain words

All six slices must be `cooked`, which means `MaxTemperature` of at least 63 °C (bacon `cook_temperature`, §15). The fridge must be closed at the end. **Heat source:** the burner `burner_mjvqii_0` (`stove.n.01`, 1980 °C). Each slice itself must be within 0.2 m of the burner's single working heat point (§2). **Container:** none is required. The frying pan is not in the goal, and heat does not pass through it (§2). It only matters as a tray the bacon can sit in over the burner.

### Q traps

- 7 literals. `not open fridge` is true at start, so it never scores. Max partial Q is 6/7 = 0.857 (page is right). Each slice is worth 1/7.
- **Close the fridge for success.** Opening it and leaving it open loses nothing in partial Q but blocks success.
- A slice more than 0.2 m from the working heat point never cooks, even if it is in the pan. Slices that slide to the far rim of a large pan, or fall on the counter, stay raw.
- Once the burner is on, the slices reach 63 °C in well under a second (§15), and cooked latches. Leaving the burner on afterwards is harmless.
- One slice (`bacon_209`) starts at 20.2 °C in some instances instead of 23 °C. It makes no practical difference.

### Minimal plan

1. `move to the fridge`, `open the door of the fridge` — ~13 s + ~41 s.
2. `pick up the tray from the middle_level fridge` — tray with six pink strips lifted level. ~23 s. The tray sits at z 0.48 in 11 instances, 0.89 in 8 and 1.29 in 1, so the shelf word may need to change to `low_level` or `high_level`.
3. `close the door of the fridge` — door flush. ~36 s. Do it now while one hand is free; it is needed for success.
4. `move to the countertop` — cooktop in view. ~13 s.
5. `place the tray on the countertop next to the right burner` — ~12 s.
6. If the pan is not already on the right zone: `pick up the frying pan from the center burner` (or `from the left burner`), then `place the frying pan on the right burner`. ~23 s + ~11 s.
7. `pick up the tray from the countertop`, then `pour the bacon and bacon and bacon and bacon and bacon and bacon into the tray` (sic; it means tray into pan) — all six strips in the pan. ~23 s + ~17 s.
8. `turn on the burner` — ~14 s. Success should fire within a second if every slice is close enough to the working zone.

The plan takes about 230 s against a 384 s limit.

Shortcut (derived, untested; saves steps 5-7): set the tray itself on the right burner zone, then `turn on the burner`. The strips lie in a cluster about 10 cm across near the tray centre. That keeps them within 0.2 m of the heat point if the tray is centred on it. There is no trained prompt; the closest is `place the frying pan on the right burner`.

### What the demos do differently

- 58 % follow the plan above exactly. The rest vary only in order.
- 158 of 200 pick the pan from the **center** burner and move it to the **right** burner, and 27 move it from the left. No demo cooks on the center zone.
- The humans pour all six strips in one tilt.

### Hard parts and hacks

- **Working burner zone.** `burner_mjvqii` has five `heatsource` points and five `togglebutton` knobs. `HeatSourceOrSink` and `ToggledOn` use only the **first** of each (`link_based_state_mixin.py:90`), and which one is first is not verified from the USD. Every demo cooks on the "right burner". With the burner at (4.17, -0.51) and yaw ≈ 0, the metadata puts heat point "0" at about (4.24, -0.26) and knob "0" at about (4.39, -0.38), which is the robot's right side when it faces the -x wall. Treat that as the likely working pair (derived).
- **Pan start.** In the test instances the pan sits on the cooktop at y -0.23 to -0.65, mostly centred, so moving it to the right zone is usually needed.
- **Grasps.** Each strip is 34 x 106 x 8 mm, so the 34 mm width fits the jaws and a strip can be picked alone. The tray is 306 x 437 x 31 mm and can be held only by its raised rim (rim wall thickness not verified).
- **Spill risk** in the pour: a strip landing outside the pan may also land outside the 0.2 m sphere. Pour low and slowly.

### Hints for the VLM

- Kitchen of `house_single_floor`. The fridge is at the right end of the sink wall (7.8, -2.0). The cooktop and pan are on the counter along the x ≈ 4.2 wall, under the range hoods, at y ≈ -0.5.
- The tray is a flat rectangle with six pink-white strips on a fridge shelf. It is the only tray in the fridge.
- The five burner rings are laid out as two on each side and one in the centre. Put the pan on a ring on the robot's right when it faces the wall.
- Done: all strips visibly browned in the pan, fridge door flush. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(cooked bacon.n.01_4)` | no | yes |
| `(cooked bacon.n.01_5)` | no | yes |
| `(cooked bacon.n.01_2)` | no | yes |
| `(cooked bacon.n.01_6)` | no | yes |
| `(cooked bacon.n.01_1)` | no | yes |
| `(cooked bacon.n.01_3)` | no | yes |
| `(not open electric_refrigerator.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?bacon.n.01 - bacon.n.01)
                (cooked ?bacon.n.01)
            )
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
| `bacon.n.01_1` | bacon_214 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.03 m (range 0.99-4.31) | yes, spread 0.35 m |
| `bacon.n.01_2` | bacon_213 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.03 m (range 0.99-4.35) | yes, spread 0.3 m |
| `bacon.n.01_3` | bacon_212 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.03 m (range 0.91-4.36) | yes, spread 0.36 m |
| `bacon.n.01_4` | bacon_211 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.08 m (range 1.07-4.24) | yes, spread 0.35 m |
| `bacon.n.01_5` | bacon_210 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.0 m (range 0.87-4.35) | yes, spread 0.33 m |
| `bacon.n.01_6` | bacon_209 | bacon / eclhdh | kitchen_0 | low (0.25-0.6 m), z 0.49 | 3.03 m (range 0.98-4.4) | yes, spread 0.38 m |
| `tray.n.01_1` | tray_208 | tray / gsxbym | kitchen_0 | low (0.25-0.6 m), z 0.48 | 3.06 m (range 1.01-4.35) | yes, spread 0.13 m |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.06 m (range 1.04-4.38) | no (fixed) |
| `stove.n.01_1` | burner_mjvqii_0 | burner / mjvqii | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 1.86 m (range 1.02-4.81) | no (fixed) |
| `frying_pan.n.01_1` | frying_pan_207 | frying_pan / mhndon | kitchen_0 | table/counter (0.6-1.1 m), z 0.93 | 1.72 m (range 0.9-4.83) | yes, spread 0.48 m |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.45 m (range 0.73-2.45) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom stove.n.01_1 kitchen)
(inside tray.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bacon.n.01_1 tray.n.01_1)
(ontop bacon.n.01_2 tray.n.01_1)
(ontop bacon.n.01_3 tray.n.01_1)
(ontop bacon.n.01_4 tray.n.01_1)
(ontop bacon.n.01_5 tray.n.01_1)
(ontop bacon.n.01_6 tray.n.01_1)
(ontop frying_pan.n.01_1 stove.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bacon.n.01_1 tray.n.01_1)
(touching bacon.n.01_2 tray.n.01_1)
(touching bacon.n.01_3 tray.n.01_1)
(touching bacon.n.01_4 tray.n.01_1)
(touching bacon.n.01_5 tray.n.01_1)
(touching bacon.n.01_6 tray.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching frying_pan.n.01_1 stove.n.01_1)
(touching stove.n.01_1 frying_pan.n.01_1)
(touching tray.n.01_1 bacon.n.01_1)
(touching tray.n.01_1 bacon.n.01_2)
(touching tray.n.01_1 bacon.n.01_3)
(touching tray.n.01_1 bacon.n.01_4)
(touching tray.n.01_1 bacon.n.01_5)
(touching tray.n.01_1 bacon.n.01_6)
```

## What the human demos did

200 annotated demos. Length 244.45 s (range 203.0-380.0). Skills per demo 14.0 (range 10-15). 8 distinct skill orders; the most common one covers 58% of demos.

Most common skill counts per demo (58% of demos): move to x4, pick up from x3, place on next to x2, close door x1, open door x1, place on x1, pour x1, turn on switch x1.

Representative demo `episode_00462020.json` (241.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-36.0 s)
2. `open the door of the fridge` (36.0-69.0 s)
3. `pick up the tray from the middle_level fridge` (69.0-99.5 s)
4. `close the door of the fridge` (99.5-138.7 s)
5. `move to the countertop` (138.7-156.7 s)
6. `place the tray on the countertop next to the right burner` (156.7-166.2 s)
7. `move to the frying pan` (166.2-168.7 s)
8. `pick up the frying pan from the center burner` (168.7-181.9 s)
9. `place the frying pan on the right burner` (181.9-193.3 s)
10. `move to the tray` (193.3-196.8 s)
11. `pick up the tray from the countertop` (196.8-206.7 s)
12. `pour the bacon and bacon and bacon and bacon and bacon and bacon into the tray` (206.7-222.6 s)
13. `place the tray on the countertop next to the right burner` (222.6-231.1 s)
14. `turn on the burner` (231.1-241.0 s)

Mean duration per skill in this task: close door 36.1 s, move to 13.3 s, open door 41.1 s, pick up from 22.5 s, place on 11.0 s, place on next to 11.6 s, pour 16.7 s, turn on switch 13.6 s, turn to 31.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the tray on the countertop next to the right burner` | 395 |
| `move to the fridge` | 200 |
| `open the door of the fridge` | 200 |
| `pick up the tray from the middle_level fridge` | 200 |
| `close the door of the fridge` | 200 |
| `move to the countertop` | 200 |
| `pour the bacon and bacon and bacon and bacon and bacon and bacon into the tray` | 200 |
| `pick up the tray from the countertop` | 199 |
| `turn on the burner` | 197 |
| `place the frying pan on the right burner` | 195 |
| `pick up the frying pan from the center burner` | 158 |
| `move to the frying pan` | 144 |
| `move to the tray` | 134 |
| `pick up the frying pan from the left burner` | 27 |
| `pick up the frying pan from the right burner` | 9 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/46_cook_bacon.json`. Planner notes: `task_docs/notes/46_cook_bacon.md`.
