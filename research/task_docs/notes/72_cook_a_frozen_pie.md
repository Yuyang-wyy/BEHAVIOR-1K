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
