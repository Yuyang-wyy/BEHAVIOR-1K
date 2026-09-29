## Planner notes

**Tier:** D — heat both hot dogs to 60 °C, plus two picks from the fridge and two places into the microwave.

### Goal in plain words

Both hot dogs must reach `cooked`, i.e. `MaxTemperature` of at least 60 °C (hotdog `cook_temperature`, §15). Cooked latches, so they may cool off afterwards. **Heat source:** the demos use the microwave `microwave_abzvij_0` (100 °C, rate 0.1). It heats only when it is closed, toggled on, and the hot dog's centre is inside it (§2). The burner `burner_mjvqii_0` also works: a 1980 °C source that heats anything within 0.2 m of its active point. No container is needed. The fridge and the microwave state are not in the goal.

### Q traps

- Two literals, both false at start (hot dogs start at -2.2 °C). Max Q is 1.0, and each hot dog is worth 0.5.
- **Microwave order:** put the hot dogs in, close the door flush (within 5 %), and only then press start. Opening the door turns the microwave off, and a press while the door is open does nothing (§11).
- Heating time in the microwave, from -2.2 °C to 60 °C, is about 10 s (derived from §2: T_ss ≈ 87 °C, time constant 8.3 s). Opening before that loses the heat, but `MaxTemperature` keeps the progress.
- Both hot dogs can go in together, so one heating cycle does both. Cooking them one at a time needs a second open, place, close and press.
- A hot dog on the floor of the cavity but with its centre outside the microwave's volume (half out of the door) does not heat.

### Minimal plan

1. `move to the fridge`, `open the door of the fridge` — ~24 s + ~35 s.
2. `pick up the hotdog from the middle_level fridge` (use the shelf word that fits: `low_level`, `middle_level` or `high_level`) — ~26 s.
3. Pick the second hot dog with the other hand, using the same prompt shape. ~26 s.
4. Skip `close the door of the fridge` (not in the goal; saves ~23 s).
5. `move to the microwave` — ~24 s.
6. `place the hotdog on the countertop` — frees a hand for the door. ~12 s.
7. `open the door of the microwave` — ~35 s.
8. `place the hotdog in the microwave` — ~17 s.
9. `pick up the hotdog from the countertop`, then `place the hotdog in the microwave` — ~26 s + ~17 s.
10. `close the door of the microwave` — door flush. ~23 s.
11. `turn on the microwave` — ~11 s. Wait about 12 s. Success ends the episode.

The plan takes about 275 s against a 457 s limit.

Alternative, no door (derived, untested): `move to the burner`, place both hot dogs on the right burner (no trained prompt; closest: `place the hotdog on the countertop`), then `turn on the burner`. They would cook in well under a second. This saves steps 6-11, about 140 s, but it depends on the working burner zone (see below).

### What the demos do differently

- All demos close the fridge right after taking the hot dogs out (~23 s, not needed).
- All demos set one hot dog on the countertop to free a hand for the microwave door, then load them one by one. That is the right trick with two hands full.
- No demo uses the burner.

### Hard parts and hacks

- **Grasp span.** A hot dog is 76 x 158 x 54 mm by bbox, so no axis is under 44 mm. The ft40k checkpoint still cooked one hot dog on instance 311 (Q 0.5). A grasp is therefore possible, probably on the narrow sausage end sticking out of the bun (unverified).
- **Shelf height** varies: z 0.50, 0.91 or 1.32.
- **Microwave door.** Opening it needs a graspable handle or edge (width not verified). Closing can be a push.
- **Burner caveat.** `burner_mjvqii` has 5 heat points and 5 knobs, but only the first of each is used (`link_based_state_mixin.py:90`). The demos in cook_cabbage and cook_bacon always cook on the "right burner".

### Hints for the VLM

- Kitchen of `house_single_floor`. The fridge is at (7.8, -2.0) on the sink wall. The microwave `abzvij` sits on the counter along the x ≈ 4.2 wall, at y ≈ 0.8, 1.04 m up. The burner is on the same counter at y ≈ -0.5.
- There is only one microwave and one pair of hot dogs (sausage in a bun) in the fridge.
- Done: both hot dogs inside the closed, running microwave for about 10 s. The episode ends by itself on success.
