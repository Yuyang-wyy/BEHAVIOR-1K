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
