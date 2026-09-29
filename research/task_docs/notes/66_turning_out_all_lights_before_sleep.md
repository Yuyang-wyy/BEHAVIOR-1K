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
