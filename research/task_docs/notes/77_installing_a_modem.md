## Planner notes

**Tier:** B — one pick-and-place of a small modem onto the TV console, plus an ~11 mm button press, all within 120 s.

### Goal in plain words

The modem must end switched on, resting on the same cabinet as the TV, and next to the TV. The TV already stands on the long living-room TV console (`bottom_cabinet_jhymlr_0` = `cabinet.n.01_1`), so the modem goes on that console beside the TV. The other cabinet option (`bottom_cabinet_bamfsz_1`) would need the TV moved and is not realistic.

### Q traps

- **Fact-page error:** `(ontop television_receiver.n.01_1 cabinet.n.01_1)` is marked "not true at start", but it **is true at reset**. The `:init` block simply does not mention the TV, which is a scene object.
  - Evidence from the template: the TV's AABB is x 1.48-1.60, y -1.95 to -1.25, bottom z 0.757. It sits inside the console's footprint (x 1.28-1.85, y -2.32 to -0.67), whose top is at z 0.754. Positions are identical in all 20 instances.
  - So that literal never scores, and **max partial Q in the best option is 3/4 = 0.75**, not 1.0.
- Result on 311: Q = 0.25 for ft24k and ft40k, i.e. one of the three scorable literals. zs_pt50 and ft10k scored 0.
- `nextto modem TV` (PREDICATES §5): with these sizes L/6 ≈ 0.09 m. The modem must stand **within ~9 cm of the TV's AABB**, on the console top.
- `toggled_on` flips once per separate 5-step touch (§11). A second brush turns it off again. It stays on when the modem is moved, so pressing before or after placing both work.
- Do not knock the TV: the literal is already true, so knocking it off only blocks success.

### Minimal plan

1. `move to the modem` — the coffee table, 0.8-2.5 m from the start. ~16 s.
2. `pick up the modem from the coffee table` ~19 s (27 s in the representative demo).
3. `move to the cabinet` — the TV console. Not the small cabinet near the coffee table. ~16 s.
4. `place the modem on the cabinet` — upright, on the console top, touching or within a few cm of the TV's side. ~10 s.
5. `turn on the modem` — the button marker turns from red to green. ~14 s.

About 75 s against a **120.6 s limit**. A failed grasp retry uses up most of the slack.

### What the demos do differently

- 141/200 follow this plan exactly. 59/200 add `hand over the modem`.
- Every demo presses the button after placing.

### Hard parts and hacks

- **Modem grasp:** `modem_axqxsv` is 0.184 × 0.049 × 0.204 m and stands upright on the coffee table. Its thinnest side, 49 mm, is **just over the 44 mm span**. A grasp may need the top edge, if it tapers (unverified), or a slightly different axis. This is probably why the checkpoints stall at Q ≤ 0.25.
- **Button:** `togglebutton` sphere ~11 mm, the same scale as the radio. Its offset is (0.066, -0.0015, -0.033) m in the modem frame, near one end and below mid-height. Which face it shows depends on how the modem is placed; the red/green marker (`toggle.py:127`) makes it findable in RGB.
- **Console space:** the free top on either side of the TV is 0.37 m (y < -1.95) and 0.58 m (y > -1.25). The side at y > -1.25 is the roomier one.
- Cheap order option: press the button while the modem still stands on the coffee table, at a stable low height (0.40-0.60 m). Then pick and place. This removes the risk of knocking the placed modem away from the TV while pressing.

### Hints for the VLM

- Rs_int living_room_0. The modem is the small upright box on the low coffee table.
- The TV console is the long low cabinet (1.65 m) with the TV standing on it. A second, small cabinet near the coffee table is the wrong one.
- Done: the modem standing on the console right beside the TV, its button marker green.
