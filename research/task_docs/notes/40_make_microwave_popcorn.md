## Planner notes

**Tier:** D — one heating transition (`popcorn` to `cooked__popcorn`) on top of moving a 203 x 278 x 180 mm popcorn bag, which is wider than the 44 mm jaw span in every direction.

### Goal in plain words

Some popcorn in the bag must become `cooked__popcorn` while it is still inside the bag's volume. `CookingPhysicalParticleRule` (`transition_rules.py:1908`) replaces every popcorn particle inside a **heatable, fillable, non-fixed container** with cooked popcorn once the container is `Heated`, meaning its own temperature is at least 40 °C. The bag is that container: `popcorn__bag.n.01` is `fillable` and `heatable` in the KB. Both goal literals flip on the same step, so this task is all or nothing. The microwave is not in the goal. Any heat source that warms the bag to 40 °C works.

### Q traps

- Two literals, both false at start, both flip together. Q is 0 or 1.
- **Microwave path.** The bag's AABB centre must be inside the microwave's volume. The door must be fully closed, within 5 % (§6). The microwave must be toggled on *after* closing, because opening forces it off (§11). The bag reaches 40 °C in about 2.6 s (PREDICATES §7).
- **Burner path (derived, untested).** The burner `burner_mdanhg_0` sits on the same bar as the bag, at x 6.91 against the bag's x ≈ 7.55. Its heat point is a 1980 °C source that affects anything within 0.2 m (§2), and it heats the bag to 40 °C in a few steps. The bag is `flammable` (ignition 250 °C), but success ends the episode at 40 °C, long before that.
- Tipping the bag can spill popcorn outside its volume. Uncooked spilled popcorn does not count. Keep the bag upright.

### Minimal plan

Demo path (in distribution):

1. `move to the microwave` — microwave front fills the view. ~12 s.
2. `open the door of the microwave` — door swung open, cavity visible. ~17 s.
3. `move to the popcorn bag` — bag on the bar in view. ~12 s.
4. `pick up the popcorn bag from the bar` — bag lifted clear of the bar. ~13 s.
5. `move to the microwave` — ~12 s.
6. `place the popcorn bag in the microwave` — bag inside the cavity, hand withdrawn. ~14 s.
7. `close the door of the microwave` — door flush with the body. ~8 s.
8. `turn on the microwave` — press the button once. Success should fire within about 3 s. ~9 s.

The plan takes about 100 s against a 162 s limit, which leaves little slack for retries.

Grasp-free fallback (no trained prompt; closest: `push the ... to the ...` shapes from other tasks): push the bag along the bar top onto or beside the cooktop, then send `turn on the burner` (trained in cook_cabbage and cook_bacon). This is worth trying only if the bag grasp fails. See the burner caveat below.

### What the demos do differently

- All 200 demos follow the same 8 steps: open the door first, then fetch the bag. That order is right. Opening first leaves a free hand for the door.
- No demo uses the cooktop.

### Hard parts and hacks

- **Bag size.** The bag is 203 x 278 x 180 mm (asset bbox × template scale). No dimension fits the 44 mm span. A grasp may register only on a thin feature such as a folded top edge (unverified). The ft40k checkpoint scored 0 on instance 311.
- **Microwave door.** Opening the `hjjxmi` door needs a handle or an edge the jaws can close on. Its width is not verified.
- **Fit.** The microwave is 343 x 517 x 264 mm outside, and the bag is 180 mm tall. It fits, but only if the bag goes in upright.
- **Burner caveat.** `burner_mdanhg` has 5 `heatsource` and 5 `togglebutton` meta links. `HeatSourceOrSink` and `ToggledOn` each use only the first matching link (`LinkBasedStateMixin.link`, `object_states/link_based_state_mixin.py`), so only one zone heats and only one knob works. Which ones is not verified. In the single-floor house, demos always use the "right burner" (see cook_cabbage and cook_bacon).
- The bag stays at z 0.98 on `bar_byvbuc_0`, with x 7.45-7.66 across all 20 instances. The microwave is at (6.12, -0.70) on the same bar.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. `bar_byvbuc_0` is the counter run along the y ≈ -0.7 wall. In order of increasing x it holds the two-door fridge (x 5.2, just past the bar end), the microwave (x 6.1), the range with its cooktop over the oven (x 6.9), and the popcorn bag (x ≈ 7.55).
- There is only one microwave and only one popcorn bag.
- Done: the episode ends by itself on success. If it does not end within about 5 s of pressing the button, check that the door is flush and that the bag is inside, then press once more.
