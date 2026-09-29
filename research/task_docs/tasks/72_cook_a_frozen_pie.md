# 72 · Cook A Frozen Pie

Task name `cook_a_frozen_pie`, task index 72.

> Take the frozen apple pie from the refrigerator, put it in the oven, and heat it until it is hot and no longer frozen.

## At a glance

| item | value |
| --- | --- |
| scene | `restaurant_diner` |
| rooms in the goal | kitchen |
| rooms loaded | kitchen_0 |
| human demo length | 288.9 s mean (8667 steps) |
| episode time limit | 433.4 s (13001 steps at 30 Hz) |
| human base travel | 18.9939 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/H4z3xTJn058 |

## Planner notes

**Tier:** D — a cooking state change (oven) on top of fridge → tray → oven pick-and-place with flat, hard-to-grip objects.

### Goal in plain words

The apple pie must be cooked (its maximum temperature has ever reached 80 °C) and must be resting on the tray. Both must hold at the same moment, and the episode then ends with success. Where the tray is does not matter, and neither the fridge nor the oven needs closing at the end.

### Q traps

- 2 literals, both false at reset. Each is worth 0.5.
- Result on 311 (ft40k): Q = 0.00.
- `cooked` latches (PREDICATES §15). Once the pie hits 80 °C, it stays cooked even if it later leaves the oven.
- The oven heats only while it is on, **closed** (all door leaves within 5 %), and the pie's AABB centre is inside the oven cavity volume (§2).
  - The oven has two door leaves; either leaf ajar means no heat.
- Timing (derived, §15): the pie starts at -47 to -13 °C per instance. It reaches 80 °C in ~5-6 s once the oven is on and closed.
- `ontop pie tray` needs the pie's centre over the tray and touching it. The tray is forced to 0.20 × 0.30 m and the pie is 0.17 m across, so there is ~1.5 cm margin on the short side. A pie that slides when the tray is carried loses the literal.

### Minimal plan

1. `move to the electric refrigerator` ~17 s. There are **two identical fridges side by side**. The pie is in `fridge_jtqazu_1` at x -6.72, the +x one: on the right when facing the pair.
2. `open the door of the electric refrigerator` — single door. ~38 s.
3. `pick up the apple pie from the electric refrigerator` — shelf height varies: 0.40, 0.86, 1.16 or 1.46 m. ~28 s.
4. `hand over the apple pie` is optional; the demos do it to free a hand for the fridge door. Closing the fridge is not needed; skip `close the door of the electric refrigerator`.
5. `move to the tray` ~17 s. The tray is fixed on the commercial kitchen table at (-9.2, 0.89), ~2.5 m from the fridge.
6. `place the apple pie on the tray` — pie flat and centred on the tray. ~13 s.
7. `pick up the tray from the commercial kitchen table` — lift level. ~28 s.
8. `move to the oven` ~17 s. The oven is at (-11.14, -1.56) and faces +x.
9. `open the door of the oven` ~38 s.
10. `place the tray in the oven` — the tray is fully inside the cavity. ~22 s.
11. `close the door of the oven` — both leaves flush. ~20 s.
12. `turn on the oven` — the button marker on the front panel (~1.28 m high, right side) turns green. Success fires a few seconds later. ~13 s.

About 260 s against a 433 s limit.

### What the demos do differently

- 200/200 follow this order and close the fridge after taking the pie. That close is not in the goal.
- All 200 cook in the oven. None use the stove or the flat-top grills.

### Hard parts and hacks

- **Pie grasp:** 0.173 × 0.171 × 0.037 m disc lying flat. A top-down grasp spans 171 mm, so only a side pinch across the 37 mm thickness can work (r1pro-grasp-span). Expect this to be the main VLA failure.
- **Tray grasp:** 0.20 × 0.30 × 0.02 m flat tray. Same issue: pinch the 20 mm edge.
- **Oven:** `oven_amblrk`, 1.67 m tall, with two door leaves. The button is a ~28 mm sphere. Whether one open leaf gives enough room for the 0.3 m tray is unverified.
- Alternative (unverified, untrained):
  - The stove `stove_ykretu` (x -11.17, y -4.53) has 6 burners, each with a `heatsource` link at ~0.87 m, and 6 knobs. Per PREDICATES §2, `stove.n.01` heats anything within 0.2 m of a heat-source point while on, with no closing needed.
  - Pie-on-tray set on a burner and one knob press might replace steps 8-11. How the 6 knobs map to the single ToggledOn state is not verified, and no demo prompt exists for it.
- Do not use the chest freezer (`freezer_gyupcj`) or the other fridge. They hold nothing for this task.

### Hints for the VLM

- restaurant_diner kitchen_0 (the only loaded room). Two tall steel fridges stand side by side; the pie is behind the door of the +x one.
- The tray is a small flat tray on the commercial kitchen table (`nisnrl`) near the fridges.
- The oven is the tall unit along the -x wall, next to the deep fryer and flat-top grills.
- Done: the pie sits on the tray, and the oven has been closed and on for a few seconds. The episode ends by itself.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop apple_pie.n.01_1 tray.n.01_1)` | no | yes |
| `(cooked apple_pie.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (ontop apple_pie.n.01_1 tray.n.01_1)
            (cooked ?apple_pie.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `apple_pie.n.01_1` | apple_pie_75 | apple_pie / rpdhbr | kitchen_0 | table/counter (0.6-1.1 m), z 0.87 | 5.48 m (range 1.86-7.87) | yes, spread 0.74 m |
| `tray.n.01_1` | tray_74 | tray / mhhoga | kitchen_0 | table/counter (0.6-1.1 m), z 0.88 | - | no |
| `oven.n.01_1` | oven_amblrk_0 | oven / amblrk | kitchen_0 | table/counter (0.6-1.1 m), z 0.97 | 5.04 m (range 1.39-6.03) | no (fixed) |
| `electric_refrigerator.n.01_1` | fridge_jtqazu_1 | fridge / jtqazu | kitchen_0 | table/counter (0.6-1.1 m), z 1.08 | 5.61 m (range 1.93-7.68) | no (fixed) |
| `countertop.n.01_1` | commercial_kitchen_table_nisnrl_0 | commercial_kitchen_table / nisnrl | kitchen_0 | table/counter (0.6-1.1 m), z 0.62 | - | no |
| `floor.n.01_1` | floors_vikfyd_0 | floors / vikfyd | kitchen_0 | floor, z 0.0 | 2.74 m (range 1.79-3.54) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "restaurant_diner": {
  "whitelist": {
   "apple_pie.n.01": {
    "apple_pie": {
     "rpdhbr": null
    }
   },
   "tray.n.01": {
    "tray": {
     "mhhoga": [
      0.2,
      0.3,
      0.02
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(frozen apple_pie.n.01_1)
(inroom countertop.n.01_1 kitchen)
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom oven.n.01_1 kitchen)
(inside apple_pie.n.01_1 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(ontop tray.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 tray.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching tray.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 297.75 s (range 152.4-387.53). Skills per demo 13.0 (range 13-14). 2 distinct skill orders; the most common one covers 87% of demos.

Most common skill counts per demo (87% of demos): move to x3, close door x2, open door x2, pick up from x2, hand over x1, place in x1, place on x1, turn on switch x1.

Representative demo `episode_00722680.json` (297.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the electric refrigerator` (0.0-8.0 s)
2. `open the door of the electric refrigerator` (8.0-46.0 s)
3. `pick up the apple pie from the electric refrigerator` (46.0-73.0 s)
4. `hand over the apple pie` (73.0-83.0 s)
5. `close the door of the electric refrigerator` (83.0-105.0 s)
6. `move to the tray` (105.0-117.0 s)
7. `place the apple pie on the tray` (117.0-132.0 s)
8. `pick up the tray from the commercial kitchen table` (132.0-160.0 s)
9. `move to the oven` (160.0-179.0 s)
10. `open the door of the oven` (179.0-223.0 s)
11. `place the tray in the oven` (223.0-255.0 s)
12. `close the door of the oven` (255.0-283.0 s)
13. `turn on the oven` (283.0-297.0 s)

Mean duration per skill in this task: close door 20.0 s, hand over 14.2 s, move to 16.9 s, open door 37.8 s, pick up from 27.9 s, place in 22.3 s, place on 13.3 s, turn on switch 12.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the tray` | 226 |
| `move to the electric refrigerator` | 200 |
| `open the door of the electric refrigerator` | 200 |
| `pick up the apple pie from the electric refrigerator` | 200 |
| `hand over the apple pie` | 200 |
| `close the door of the electric refrigerator` | 200 |
| `place the apple pie on the tray` | 200 |
| `pick up the tray from the commercial kitchen table` | 200 |
| `move to the oven` | 200 |
| `open the door of the oven` | 200 |
| `place the tray in the oven` | 200 |
| `close the door of the oven` | 200 |
| `turn on the oven` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/72_cook_a_frozen_pie.json`. Planner notes: `task_docs/notes/72_cook_a_frozen_pie.md`.
