# 41 · Cook Cabbage

Task name `cook_cabbage`, task index 41.

> From the kitchen refrigerator, take the cabbage and the chili, dice them on the chopping board with the knife, cook the diced cabbage and diced chili in the frying pan on the stove, and leave the cooked, diced cabbage and cooked, diced chili in the frying pan.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 471.5 s mean (14144 steps) |
| episode time limit | 707.2 s (21217 steps at 30 Hz) |
| human base travel | 39.3143 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060935 |

## Planner notes

**Tier:** D — two slice-then-dice transitions plus particle cooking in a pan on the burner. On top of that, both vegetables are wider than the 44 mm jaw span.

### Goal in plain words

The pan (`frying_pan_208`) must end up holding at least one particle of `cooked__diced__head_cabbage` and one of `cooked__diced__chili`. **Heat source:** the burner `burner_mjvqii_0` (`stove.n.01`, 1980 °C, 0.2 m sphere, must be toggled on). **Tool:** the carving knife `carving_knife_209`. **Container:** the frying pan. Diced particles in the pan turn cooked as soon as the pan is `Heated`, meaning its own temperature is at least 40 °C (`CookingPhysicalParticleRule`, `transition_rules.py:1908-2020`; recipes `diced__head_cabbage.n.01-cooking` and `diced__chili.n.01-cooking` in `substance_cooking.json`). Dicing a half that is already cooked makes `cooked__diced__X` directly (`DicingRule`, `transition_rules.py:1022-1032`). The chopping board, the plate and the fridge door are not in the goal.

### Q traps

- Four literals, all false at start, so max Q is 1.0. Each vegetable is worth 0.5: its `real` and its `contains` literal.
- `real diced__X` needs **two** knife contacts: whole to halves, then half to particles. The knife must re-arm between them by staying off every sliceable for 2 s (§7).
- **One half per vegetable is enough.** The goal checks only that the particle system exists and that at least 1 particle is in the pan (`contains` threshold is 1, §13). Dicing the second halves adds nothing.
- Particles diced on the board and then poured must land inside the pan's volume. Particles that miss score nothing, but `real` still holds once the system exists.
- The pan heats only when it sits within 0.2 m of the one working heat point. Heat does not pass through the pan into the food; the pan itself must be `Heated` (§2).
- `real cooked__diced__X` stays False if the diced particles are never in a hot pan. Raw `diced__X` does not count.

### Minimal plan

The plan dices directly into the pan (derived; no demo does this), which avoids both pours.

1. `move to the burner` — cooktop in view. The pan `frying_pan_208` is on the countertop next to it. ~8 s.
2. `pick up the frying pan from the countertop` — pan lifted by its handle. ~19 s.
3. `place the frying pan on the right burner` — pan resting on the right zone. ~12 s.
4. `turn on the burner` — ~15 s. No image cue. Assume the knob the demos use is the working one.
5. `move to the fridge`, `open the door of the fridge` — door swung open. ~8 s + ~38 s.
6. `pick up the head cabbage from the high_level fridge` (use the shelf word that fits: `low_level`, `middle_level` or `high_level`) — cabbage lifted. ~19 s. Leave the fridge open, since the goal does not need it closed.
7. `pick up the chili from the low_level fridge` with the other hand (use the shelf word that fits) — ~19 s.
8. `move to the burner`. Place both vegetables in the pan. No trained prompt; closest: `place the head cabbage on the cutting board`, `place the chili on the plate`. ~12 s each.
9. `pick up the carving knife from the countertop` — ~19 s.
10. `chop the carving knife with the head cabbage` — two halves appear. Lift the knife, wait more than 2 s, then `chop the carving knife with the half head cabbage 212` — the half vanishes into small pieces. ~6 s each.
11. `chop the carving knife with the chili`, wait 2 s, then `chop the carving knife with the half chili 211` — ~6 s each. Success fires once cooked particles of both are in the pan.

The plan takes about 250 s against a 707 s limit. If dicing in the pan fails (for example, the halves roll off), fall back to the demo route: dice on the cutting board, then `pick up the cutting board from the countertop` and `pour the diced  head cabbage into the cutting board` (sic, double space, board to pan).

### What the demos do differently

- They take both vegetables out, close the fridge (not needed, ~35 s), dice everything on the board, and dice **both** halves of each vegetable (only one is needed).
- 148 of 200 demos push the board to the counter edge (`push the cutting board to the to_the_edge_of countertop`) so they can pick it up. They then pour from the board into the pan twice.
- All 200 demos place the pan on the **right** burner and press the burner last.

### Hard parts and hacks

- **Grasp span.** The head cabbage is 143 x 148 x 140 mm, and its halves are about 148 x 142 x 70 mm (asset `object_parts`). The chili is scaled to 235 x 120 x 38 mm and lies flat, so a top-down grasp cannot straddle it. Neither fits the 44 mm jaw span by bbox. A grasp is realistically unlikely. The ft40k checkpoint scored 0 on instance 311.
- **Which burner zone works.** `burner_mjvqii` has 5 `heatsource` and 5 `togglebutton` meta links. `HeatSourceOrSink` and `ToggledOn` each use only the first link (`LinkBasedStateMixin.link`). Which one is not verified. The demos always use the right burner.
- **Knife.** `carving_knife_209` (`awvoox`) is 226 x 30 x 17 mm and fits the jaws. Any link touching a sliceable counts (§7). Keep the knife clear of the other vegetable while holding it.
- **Vegetables start chilled** (-3.6 °C) and at shelf heights z 0.49-1.35. Cabbage cooks at the default 70 °C, but only cooking of the diced particles matters here.

### Hints for the VLM

- Kitchen of `house_single_floor`. The fridge is at the right end of the sink wall (7.8, -2.0). The burner and the pan are on the counter run along the x ≈ 4.2 wall, under range hoods, at y ≈ -0.5. The microwave is further along that run at y ≈ 0.8.
- The cabbage is a green ball. The chili is a long red pod. Each is the only one in the scene.
- There is only one frying pan and one knife in the kitchen.
- Done: small cooked pieces of both colours inside the pan on the lit burner. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real cooked__diced__head_cabbage.n.01_1)` | no | yes |
| `(real cooked__diced__chili.n.01_1)` | no | yes |
| `(contains frying_pan.n.01_1 cooked__diced__head_cabbage.n.01_1)` | no | yes |
| `(contains frying_pan.n.01_1 cooked__diced__chili.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?cooked__diced__head_cabbage.n.01_1)
            (real ?cooked__diced__chili.n.01_1)
            (contains ?frying_pan.n.01_1 ?cooked__diced__head_cabbage.n.01_1)
            (contains ?frying_pan.n.01_1 ?cooked__diced__chili.n.01_1) 
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `head_cabbage.n.02_1` | head_cabbage_212 | head_cabbage / tqohvs | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 2.64 m (range 1.13-4.63) | yes, spread 0.41 m |
| `cooked__diced__chili.n.01_1` | particle system | cooked__diced__chili | - | - | - | - |
| `cooked__diced__head_cabbage.n.01_1` | particle system | cooked__diced__head_cabbage | - | - | - | - |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.69 m (range 1.12-4.55) | no (fixed) |
| `chili.n.02_1` | chili_211 | chili / xhbpqh | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 2.62 m (range 0.96-4.51) | yes, spread 0.31 m |
| `chopping_board.n.01_1` | cutting_board_210 | cutting_board / tcdrzs | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.64 m (range 0.75-4.75) | yes, spread 1.63 m |
| `carving_knife.n.01_1` | carving_knife_209 | carving_knife / awvoox | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 1.77 m (range 1.07-4.73) | yes, spread 3.09 m |
| `frying_pan.n.01_1` | frying_pan_208 | frying_pan / cprjvq | kitchen_0 | table/counter (0.6-1.1 m), z 0.92 | 1.67 m (range 1.12-4.54) | yes, spread 0.64 m |
| `plate.n.04_1` | plate_207 | plate / zpddxu | kitchen_0 | table/counter (0.6-1.1 m), z 0.9 | 1.92 m (range 1.08-4.66) | yes, spread 2.42 m |
| `stove.n.01_1` | burner_mjvqii_0 | burner / mjvqii | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 1.7 m (range 1.01-4.63) | no (fixed) |
| `countertop.n.01_1` | countertop_kelker_0 | countertop / kelker | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 1.69 m (range 1.0-4.62) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.36 m (range 0.75-2.45) | no (fixed) |

Initial conditions from `:init`:

```lisp
(future cooked__diced__chili.n.01_1)
(future cooked__diced__head_cabbage.n.01_1)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom stove.n.01_1 kitchen)
(inside chili.n.02_1 electric_refrigerator.n.01_1)
(inside head_cabbage.n.02_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop carving_knife.n.01_1 countertop.n.01_1)
(ontop chopping_board.n.01_1 countertop.n.01_1)
(ontop frying_pan.n.01_1 countertop.n.01_1)
(ontop plate.n.04_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching carving_knife.n.01_1 countertop.n.01_1)
(touching chopping_board.n.01_1 countertop.n.01_1)
(touching countertop.n.01_1 carving_knife.n.01_1)
(touching countertop.n.01_1 chopping_board.n.01_1)
(touching countertop.n.01_1 frying_pan.n.01_1)
(touching countertop.n.01_1 plate.n.04_1)
(touching floor.n.01_1 agent.n.01_1)
(touching frying_pan.n.01_1 countertop.n.01_1)
(touching plate.n.04_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 480.85 s (range 253.93-654.0). Skills per demo 36.0 (range 30-47). 134 distinct skill orders; the most common one covers 11% of demos.

Most common skill counts per demo (15% of demos): move to x8, pick up from x8, place on x7, chop x6, pour x2, close door x1, open door x1, place on next to x1, push to x1, turn on switch x1.

Representative demo `episode_00412280.json` (494.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.5-34.6 s)
2. `open the door of the fridge` (34.6-66.4 s)
3. `pick up the chili from the low_level fridge` (66.4-113.8 s)
4. `pick up the head cabbage from the high_level fridge` (113.8-136.3 s)
5. `close the door of the fridge` (136.3-165.9 s)
6. `move to the cutting board` (165.9-175.6 s)
7. `place the head cabbage on the cutting board` (175.6-197.2 s)
8. `move to the plate` (197.2-201.8 s)
9. `place the chili on the plate` (201.8-218.1 s)
10. `pick up the frying pan from the countertop` (218.1-235.7 s)
11. `move to the burner` (235.7-245.9 s)
12. `place the frying pan on the right burner` (245.9-259.9 s)
13. `move to the carving knife` (259.9-265.7 s)
14. `pick up the carving knife from the countertop` (265.7-290.7 s)
15. `move to the head cabbage` (290.7-298.3 s)
16. `chop the carving knife with the head cabbage` (298.3-304.1 s)
17. `chop the carving knife with the half head cabbage 212` (304.1-307.9 s)
18. `chop the carving knife with the half head cabbage 212` (307.9-313.2 s)
19. `place the carving knife on the countertop next to the right cutting board` (313.2-318.8 s)
20. `push the cutting board to the to_the_edge_of countertop` (318.8-339.2 s)
21. `pick up the cutting board from the countertop` (339.2-362.2 s)
22. `pour the diced  head cabbage into the cutting board` (362.2-370.0 s)
23. `place the cutting board on the to_the_edge_of countertop` (370.0-384.8 s)
24. `move to the chili` (384.8-386.8 s)
25. `pick up the chili from the plate` (386.8-398.4 s)
26. `move to the cutting board` (398.4-405.4 s)
27. `place the chili on the cutting board` (405.4-413.5 s)
28. `pick up the carving knife from the countertop` (413.5-427.1 s)
29. `chop the carving knife with the chili` (427.1-438.5 s)
30. `chop the carving knife with the half chili 211` (438.5-442.7 s)
31. `chop the carving knife with the half chili 211` (442.7-445.3 s)
32. `place the carving knife on the countertop` (445.3-451.7 s)
33. `pick up the cutting board from the countertop` (451.7-467.5 s)
34. `pour the diced  chili into the cutting board` (467.5-472.4 s)
35. `place the cutting board on the countertop` (472.4-482.4 s)
36. `turn on the burner` (482.6-494.8 s)

Mean duration per skill in this task: chop 5.7 s, close door 34.6 s, move to 8.0 s, open door 37.6 s, pick up from 18.7 s, place on 12.0 s, place on next to 7.0 s, pour 9.2 s, push to 18.7 s, turn on switch 14.6 s, turn to 24.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the cutting board` | 464 |
| `pick up the carving knife from the countertop` | 403 |
| `pick up the cutting board from the countertop` | 400 |
| `chop the carving knife with the half head cabbage 212` | 396 |
| `chop the carving knife with the half chili 211` | 394 |
| `move to the burner` | 219 |
| `move to the chili` | 208 |
| `place the cutting board on the countertop` | 201 |
| `open the door of the fridge` | 200 |
| `close the door of the fridge` | 200 |
| `place the head cabbage on the cutting board` | 200 |
| `place the chili on the plate` | 200 |
| `pick up the frying pan from the countertop` | 200 |
| `place the frying pan on the right burner` | 200 |
| `chop the carving knife with the head cabbage` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/41_cook_cabbage.json`. Planner notes: `task_docs/notes/41_cook_cabbage.md`.
