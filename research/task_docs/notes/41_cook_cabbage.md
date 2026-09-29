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
