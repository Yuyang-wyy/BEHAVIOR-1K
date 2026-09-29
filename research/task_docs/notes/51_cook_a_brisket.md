## Planner notes

**Tier:** D — heat one brisket to 63 °C, then place it on a board. The pan literal is already true and only has to be kept.

### Goal in plain words

The brisket must be `cooked`, meaning `MaxTemperature` of at least 63 °C (brisket `cook_temperature`, §15; latched). It must end resting on the chopping board `chopping_board_80`. The frying pan must still be on `bar_egwapq_0` (the BDDL `countertop`) at the end. **Heat source:** any active one works; the goal does not name one. There are three in the scene:

- the burner `burner_mdanhg_0` (1980 °C, within 0.2 m of its working point);
- the microwave `microwave_hjjxmi_0` (closed, on, brisket inside);
- the oven `oven_ffitak_0` (closed including racks, on, brisket inside).

**Container:** none is needed. The pan is optional, because heat does not pass through it (§2).

### Q traps

- 3 literals. `ontop frying_pan countertop` is true at start, so it never scores. Max partial Q is 2/3 = 0.667 (page is right).
- **Two bars.** The BDDL `countertop` is `bar_egwapq_0`, the counter along the x ≈ 8.2 wall with the sink, where the pan and board start. The cooktop is on the other counter, `bar_byvbuc_0`, which the prompts also call "bar". If the pan is used, it must go back onto `bar_egwapq_0`, not onto the cooktop counter. Otherwise success is lost.
- **Simplest: do not touch the pan at all.** Cook the brisket without it and the pan literal stays true.
- `ontop brisket board` needs the brisket's centre over the board and touching it (§4). A brisket resting half on the pan rim or on the bar fails.
- Brisket starts at -2.2 °C. The microwave takes about 11 s to reach 63 °C (derived from §2: T_ss ≈ 87 °C, time constant 8.3 s). A burner takes well under 1 s.

### Minimal plan

This is the microwave route. It is derived, and it keeps the pan untouched.

1. `move to the fridge`, `open the door of the fridge` — ~12 s + ~39 s. The fridge has two doors, so open the one in front of the brisket.
2. `pick up the brisket from the fridge` — ~20 s. The fridge is not in the goal, so leave it open.
3. `move to the microwave`, then `open the door of the microwave`, then place the brisket in it. There is no trained prompt for this task; closest: `place the popcorn bag in the microwave` (make_microwave_popcorn). Then `close the door of the microwave` and `turn on the microwave`, and wait about 12 s. Times: ~12 + 17 + 14 + 8 + 9 s.
4. `open the door of the microwave`, pick the brisket out — ~17 + 20 s.
5. `move to the chopping board`, then place the brisket on the board. No trained prompt; closest: `place the brisket in the frying pan`. ~12 + 10 s.

The plan takes about 230 s against a 367 s limit.

Demo route (in distribution; the pan must be returned to the right bar):
1. `move to the frying pan`, `pick up the frying pan from the bar`.
2. `move to the burner`, `place the frying pan on the burner`.
3. `move to the fridge`, `open the door of the fridge`, `pick up the brisket from the fridge`, `close the door of the fridge`.
4. `move to the frying pan`, `place the brisket in the frying pan`, `turn on the burner`.
5. `pick up the frying pan from the burner`, `move to the chopping board`, `pour the brisket into the frying pan` (sic; pan onto board).
6. `place the frying pan on the bar`, on `bar_egwapq_0`.

Mean total about 240 s.

### What the demos do differently

- All 200 use the pan on the burner. They turn the burner on and off within about 10 s, then tip the brisket from the pan onto the board.
- 136 demos pass the brisket between hands (`hand over the brisket`) to free a hand for the fridge door. 30 demos push the brisket (`push the brisket to the fridge`).
- `turn off the burner` is not needed for the goal.

### Hard parts and hacks

- **Brisket grasp.** The brisket is forced to 150 x 100 x 20 mm (`task_custom_lists.json`) and lies flat. The 20 mm thickness can only be straddled from the side, so a top-down grasp does not fit the 44 mm span. Shelf height varies from z 0.72 to 1.67. The ft40k checkpoint scored 0 on instance 311. The demos' pour from the pan onto the board sidesteps the second grasp. The pan (`jpzusm`, 465 x 286 x 57 mm) has a handle.
- **Burner route caveat.** `burner_mdanhg` has 5 heat points and 5 knobs, and only the first of each works (`link_based_state_mixin.py:90`). Which one is first is not verified.
- **Microwave.** It sits right next to the fridge (x 6.12 against 5.2) at z 1.01, so it is the shortest heat source from the fridge. The door must be flush before pressing (§11).
- The oven works too, but it is low (root at z 0.54). All 3 of its joints count for "open" (no `openable_joint_ids`). Avoid it.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. The two-door fridge is at (5.2, -0.57). Along the y ≈ -0.7 wall come the microwave (6.1) and the cooktop over the oven (6.9) on `bar_byvbuc_0`. The pan and the chopping board are on `bar_egwapq_0` along the x ≈ 8.2 wall, next to the sink.
- The brisket is a flat brown slab on a fridge shelf. The board is a light wooden rectangle, 25 x 37 cm.
- Done: the brisket lies on the board, the pan is still on the sink-side bar, and the brisket was hot at some point. The episode ends by itself on success.
