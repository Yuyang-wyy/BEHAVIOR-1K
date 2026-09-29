# 66 · Turning Out All Lights Before Sleep

Task name `turning_out_all_lights_before_sleep`, task index 66.

> Turn off all of the lights and light switches before sleep.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | corridor, dining_room, kitchen, living_room, utility_room |
| rooms loaded | corridor_0, utility_room_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 333.5 s mean (10006 steps) |
| episode time limit | 500.3 s (15009 steps at 30 Hz) |
| human base travel | 40.2489 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.40; ft40k@local Q=0.40 |
| demo video | https://www.youtube.com/embed/AN8l_cduvqU |

## Planner notes

**Tier:** A — every literal is `not toggled_on`; a 5-step fingertip touch on each button, no grasp.

### Goal in plain words

Five objects start switched on and must end switched off: three wall switches and two table lamps. They sit in four places: the utility room (switch and lamp), the living_room_0 coffee table (lamp), the kitchen (switch) and the dining room (switch). Other lamps and switches in the house start off and are not in the goal; switching one on is harmless but wastes time. Doors are not in the goal.

### Q traps

- Each object flips on the step its 5-step touch counter reaches 5 (PREDICATES §11). **A second, separate touch turns it back on.** Two presses on the same object score 0 for it.
- All 5 start on in all 20 public instances (`ToggledOn: true` in every `-tro_state.json`), so each press scores 0.2.
- Q reads the final state only. A lamp bumped again on the way out is lost.
- The kitchen and dining switches each have an identical, OFF twin beside them. Pressing the twin does nothing for the goal:
  - kitchen: goal switch `electric_switch_gashan_8` at y 1.15; twin `gashan_9` 8.4 cm away at y 1.06, on the microwave side.
  - dining: goal switch `gashan_7` at y 2.32; twin `gashan_6` 12 cm away at y 2.44, on the door side.
- Result on 311 (ft40k): Q = 0.40, i.e. 2 of 5. Which two is not recorded.

### Minimal plan

Order below follows every demo: the utility room first, then the far rooms. Positions are world metres from the template; they are fixed in all 20 instances except the lamps, which shift a few dm.

1. `move to the sliding door` — base stopped facing the closed sliding door to the utility room (`sliding_door_tprpvb_7`, x 23.2, y 2.33). ~28 s.
2. `open the door of the sliding door` — doorway visibly clear. ~34 s. It starts closed (joint_pos 0) and the utility switch faces into the utility room, so it cannot be pressed from the corridor.
3. `move to the table lamp` — utility-room lamp on the countertop, x ~24.4. ~28 s.
4. `turn off the table lamp` — toggle marker on the lamp turns red. ~13 s.
5. `move to the electric switch` — the switch is on the utility-room face of the wall, 6 cm east of the door opening, at 1.44 m. ~28 s.
6. `turn off the electric switch` — marker red. ~13 s.
7. Skip `close the door of the sliding door` (194/200 demos do it; not in the goal).
8. `move to the table lamp` — living_room_0 coffee table, x ~12.6, y ~0.6. ~28-50 s.
9. `turn off the table lamp` — marker red. ~13 s.
10. `move to the electric switch` — dining switch, x 4.66, y 2.32, 1.44 m, beside the dining/living_room_1 door. ~28-45 s.
11. `turn off the electric switch` — marker red. ~13 s.
12. `move to the electric switch` — kitchen switch, x 3.89, y 1.15, 0.94 m. ~5-10 s.
13. `turn off the electric switch` — marker red. ~13 s.

Demo total ~330 s. Limit 500 s. There is no trained prompt that names a specific lamp or switch; the planner must steer `move to` by what is in view.

### What the demos do differently

- 147/200 follow the order above exactly. 39/200 run `open the door of the sliding door` twice in a row. That fits robots starting in the south corridor stub behind a second closed sliding door (`tprpvb_12`, y 2.41). In 7/20 public instances the robot starts at y < 2.4. This is derived from the wall boxes in the template, not checked in sim.
- 194/200 close the utility door again. The goal does not need it.
- Humans press each object exactly once.

### Hard parts and hacks

- Button spheres (from `misc/metadata.json` `togglebutton`): switch ~23 mm, lamp ~29 mm. Both are larger than the radio's ~11 mm. The finger must also touch the object itself.
- Switch heights: 1.44 m (utility, dining) and 0.94 m (kitchen). Every demo reaches all three on the same R1Pro, so reach is proven.
- **Kitchen switch is the awkward one.** It is mounted on the +x face of a short wall stub at countertop level (counter top ~0.89 m). The counter is 0.86 m deep (x 3.75-4.61), so the arm reaches ~0.7 m over it. The microwave (y 0.54-1.04, top ~1.19 m) sits right beside the path.
- Utility lamp button: ~1.34 m high on a 0.93 m counter, with the lamp 0.25 m in from the counter edge. The coffee-table lamp button is at ~0.68 m. The lamp shades are 0.46 m wide; whether a shade blocks a straight approach is unverified.
- Failure modes: a double press, which turns the object back on; pressing the twin switch; a slow brush that counts as two contacts.
- Cheap check: `ToggledOn` draws a visible marker sphere, **green when on and red when off** (`object_states/toggle.py:127`, `visible = True` at `:171`). Read it from RGB after every press. It is legal RGB, but it is a sim artefact, not a real light cue.

### Hints for the VLM

- Utility room: through the sliding door at the east end of the corridor. The lamp stands on a long countertop along the far (east) wall. The switch is on the wall right beside the door, at shoulder height, facing into the room.
- Living room lamp: the only lamp on the low square coffee table (0.97 m square, top ~0.27 m) in living_room_0.
- Dining switch: on the wall next to the dining/living_room_1 hinged door. Pick the switch farther from the door.
- Kitchen switch: just above the countertop at the end of the counter run, next to the microwave. Pick the switch farther from the microwave.
- At start the goal switch shows a green marker and its twin a red one. Done means all five markers are red.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not toggled_on switch.n.01_1))` | no | yes |
| `(not toggled_on switch.n.01_3))` | no | yes |
| `(not toggled_on switch.n.01_2))` | no | yes |
| `(not toggled_on table_lamp.n.01_2))` | no | yes |
| `(not toggled_on table_lamp.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?switch.n.01 - switch.n.01)
                (not 
                    (toggled_on ?switch.n.01)
                )
            )
            (forall
                (?table_lamp.n.01 - table_lamp.n.01)
                (not
                    (toggled_on ?table_lamp.n.01)
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
| `switch.n.01_1` | electric_switch_gashan_8 | electric_switch / gashan | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 16.15 m (range 15.06-22.57) | no (fixed) |
| `switch.n.01_2` | electric_switch_gashan_21 | electric_switch / gashan | utility_room_0 | high (1.1-1.6 m), z 1.44 | 4.53 m (range 2.8-16.54) | no (fixed) |
| `switch.n.01_3` | electric_switch_gashan_7 | electric_switch / gashan | dining_room_0 | high (1.1-1.6 m), z 1.44 | 15.21 m (range 14.48-21.19) | no (fixed) |
| `floor.n.01_1` | floors_wkdxrr_0 | floors / wkdxrr | corridor_0 | floor, z -0.14 | 5.79 m (range 1.19-9.98) | no (fixed) |
| `table_lamp.n.01_1` | table_lamp_429 | table_lamp / ehjsdz | living_room_0 | table/counter (0.6-1.1 m), z 0.75 | 7.78 m (range 6.21-18.71) | yes, spread 0.79 m |
| `table_lamp.n.01_2` | table_lamp_428 | table_lamp / ehjsdz | utility_room_0 | high (1.1-1.6 m), z 1.41 | 5.93 m (range 4.13-19.88) | yes, spread 3.82 m |
| `countertop.n.01_1` | countertop_ikwqer_0 | countertop / ikwqer | utility_room_0 | table/counter (0.6-1.1 m), z 0.91 | 6.32 m (range 4.13-18.96) | no (fixed) |
| `coffee_table.n.01_1` | coffee_table_rlsebe_0 | coffee_table / rlsebe | living_room_0 | floor, z 0.15 | 7.9 m (range 6.41-18.56) | no |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "corridor",
  "utility_room",
  "childs_room",
  "dining_room",
  "bedroom",
  "kitchen",
  "living_room",
  "bathroom"
 ],
 "house_single_floor": {
  "whitelist": {
   "table_lamp.n.01": {
    "table_lamp": {
     "ehjsdz": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom coffee_table.n.01_1 living_room)
(inroom countertop.n.01_1 utility_room)
(inroom floor.n.01_1 corridor)
(inroom switch.n.01_1 kitchen)
(inroom switch.n.01_2 utility_room)
(inroom switch.n.01_3 dining_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop table_lamp.n.01_1 coffee_table.n.01_1)
(ontop table_lamp.n.01_2 countertop.n.01_1)
(toggled_on switch.n.01_1)
(toggled_on switch.n.01_2)
(toggled_on switch.n.01_3)
(toggled_on table_lamp.n.01_1)
(toggled_on table_lamp.n.01_2)
(touching agent.n.01_1 floor.n.01_1)
(touching coffee_table.n.01_1 table_lamp.n.01_1)
(touching countertop.n.01_1 table_lamp.n.01_2)
(touching floor.n.01_1 agent.n.01_1)
(touching table_lamp.n.01_1 coffee_table.n.01_1)
(touching table_lamp.n.01_2 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 328.37 s (range 244.97-462.97). Skills per demo 14.0 (range 12-16). 9 distinct skill orders; the most common one covers 74% of demos.

Most common skill counts per demo (74% of demos): move to x7, turn off switch x5, close door x1, open door x1.

Representative demo `episode_00662790.json` (326.5 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the sliding door` (0.0-69.0 s)
2. `open the door of the sliding door` (69.0-100.1 s)
3. `move to the table lamp` (100.1-121.0 s)
4. `turn off the table lamp` (121.0-131.2 s)
5. `move to the electric switch` (131.2-144.0 s)
6. `turn off the electric switch` (144.0-149.0 s)
7. `move to the sliding door` (149.0-171.0 s)
8. `close the door of the sliding door` (171.0-189.6 s)
9. `move to the table lamp` (189.6-240.8 s)
10. `turn off the table lamp` (240.8-263.0 s)
11. `move to the electric switch` (263.0-307.0 s)
12. `turn off the electric switch` (307.0-314.0 s)
13. `move to the electric switch` (314.0-319.0 s)
14. `turn off the electric switch` (319.0-326.0 s)

Mean duration per skill in this task: close door 27.5 s, move to 27.6 s, open door 33.5 s, turn off switch 13.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the electric switch` | 596 |
| `turn off the electric switch` | 595 |
| `move to the sliding door` | 446 |
| `turn off the table lamp` | 400 |
| `move to the table lamp` | 399 |
| `open the door of the sliding door` | 248 |
| `close the door of the sliding door` | 195 |
| `close the door of the electric switch` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/66_turning_out_all_lights_before_sleep.json`. Planner notes: `task_docs/notes/66_turning_out_all_lights_before_sleep.md`.
