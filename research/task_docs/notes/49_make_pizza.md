## Planner notes

**Tier:** D — a cooking recipe in the oven, which first needs a slice-then-dice (onion), a slice (mushroom), two particle pours and several small placements. It is the longest recipe chain in this block.

### Goal in plain words

A `pizza` object must exist and rest on the cookie sheet `baking_sheet_79`. It can only come from a `CookingObjectRule` recipe in `heat_cook.json`. The full `pizza` recipe needs tomato sauce, marjoram and 7 pepperoni, none of which exist in this scene, so it is never active. The recipe that can fire is **`simple_pizza`**. It needs all of the following:

- The dough is in or `ontop` the cookie sheet. This is already true at start.
- At least **1** `pepperoni` is `ontop` the dough.
- At least **1** `half__mushroom` is `ontop` the dough.
- The dough is `covered` by `grated_cheese`, meaning at least 1 particle touches it (§12, `covered.py` `PHYSICAL_PARTICLE_THRESHOLD` = 1).
- The dough is `covered` by `diced__vidalia_onion`, at least 1 particle touching.
- **Container:** the cookie sheet. **Heat source:** the oven `oven_ffitak_0`, which must heat the sheet. That means the sheet is Inside the oven, the oven is toggled on, and the oven is fully closed (§2).

With `timesteps` null the recipe fires on the first step these all hold (`CookingRule`, `transition_rules.py:2323-2349`). The pizza spawns `OnTop` the sheet (`_spawn_object_in_container`, `transition_rules.py:1783`), so both goal literals flip together and the episode ends.

**Tool:** the carving knife `carving_knife_77`, for the onion and the mushrooms.

### Q traps

- Two literals, both flipping on one step. Q is 0 or 1.
- The toppings need only one of each: 1 pepperoni, 1 mushroom half, one particle of cheese, one piece of onion. The four pepperoni and two mushrooms in the instruction are not required.
- **The knife destroys things.** `pizza_dough`, `pepperoni` and `mushroom` are all `sliceable`, and `half__mushroom` and `half__vidalia_onion` are `diceable` (KB). A knife touching the dough removes it for good, and then no pizza is possible. A second touch on a mushroom half dices it (§7). Do all cutting on the board, away from the dough, and put the knife down before topping.
- **Order on the dough:** place the pepperoni and the mushroom half **before** pouring the cheese and onion. `ontop` needs the piece to touch the dough itself (§4). A pepperoni lying on a heap of cheese does not count.
- **Oven "open" means any joint.** `oven/ffitak` has no `openable_joint_ids`, so all 3 joints count: the door and two rack joints (`open_state.py:96` fallback). A rack left pulled out more than 5 % keeps the oven "open", and it does not heat.
- Extra objects on the sheet do not block the recipe (`ignore_nonrecipe_objects` is True).

### Minimal plan

1. `pick up the carving knife from the bar` — ~12 s. The onion already sits on the chopping board.
2. `chop the carving knife with the vidalia onion`, wait 2 s, then `chop the carving knife with the half vidalia onion 80` — at least one pile of onion pieces. ~4 s each.
3. `move to the fridge`, `open the door of the right_door fridge`, `pick up the tupperware from the layer_4 fridge` (the mushroom box), `pick up the tupperware from the layer_5 fridge` (cheese or pepperoni; check what is inside) — ~7 + 24 + 12 + 12 s. The contents vary by layer and instance, so pick by appearance.
4. `move to the chopping board`, `pour the mushroom and mushroom into the tupperware` (sic; tupperware onto board) — ~7 + 8 s.
5. `chop the carving knife with the mushroom` — one cut only, then **put the knife down**: `place the carving knife on the bar`. ~4 + 7 s.
6. Place one mushroom half and one pepperoni on the dough. No trained prompt; closest: `place the vidalia onion on the chopping board` shape. ~12 s each. Get the pepperoni by pouring its tupperware onto the board or dough: `pour the pepperoni and pepperoni and pepperoni and pepperoni into the tupperware` (sic).
7. `pick up the chopping board from the bar`, move over the dough, `pour the diced  vidalia onion into the chopping board` (sic) — some onion pieces on the dough. ~12 + 8 s.
8. With the cheese tupperware: `pour the grated cheese into the tupperware` (sic; tupperware onto dough) — cheese on the dough. ~8 s.
9. `move to the oven`, `open the door of the oven` — ~7 + 24 s.
10. `pick up the baking sheet from the bar`, `move to the oven`, `place the baking sheet in the high_level oven` — ~12 + 7 + 13 s. Carry it level. If the rack is pulled first (`pull tray the high_level oven`), push it back with `push tray the high_level oven`.
11. `close the door of the oven`, `turn on the oven` — ~17 + 7 s. Success fires on the next step.

The plan takes about 400 s against a 959 s limit.

### What the demos do differently

- They gather everything in the bowl: onion, mushroom halves and pepperoni are poured into `bowl_76`, then the bowl is poured over the dough. This takes more pours than needed.
- They move the baking sheet next to the oven early (`place the baking sheet on the bar next to the left oven`), which shortens the final carry.
- They pull the rack out, place the sheet, then push the rack back. After `turn on the oven` they open the door again (not needed; the pizza is already made).
- They halve both mushrooms and dice both onion halves (only one of each is needed).

### Hard parts and hacks

- **Grasps that fit the jaws.** Pepperoni is a 30 mm disc 5 mm thick, and a top-down pinch across its diameter works. The mushroom is a 30 mm cube, and its halves are 30 x 29 x 14 mm. The knife `fqqbop` is 323 x 39 x 24 mm.
- **Grasps that do not fit.** The onion is 100 x 70 x 71 mm but never needs moving. The tupperwares (219 mm) can only be held by the rim. The **cookie sheet** is 270 x 300 x 30 mm and lies flat, so only its edge can be pinched. It must be carried level with the dough on it, which is the riskiest step.
- **Fridge.** `fridge_petcxr` has two doors. The tupperwares are at z 0.77-1.86, so the top one needs the trunk raised.
- **Oven.** It is low (the root sits at z 0.54), under the cooktop, on the far counter from the dough. The robot must lower the trunk to slide the sheet in.
- The oven has two `togglebutton` links, and only the first one toggles (`link_based_state_mixin.py:90`). Which one is first is not verified.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. The dough on the cookie sheet, the chopping board with the onion, the knife and the bowl are on `bar_egwapq_0` along the x ≈ 8.2 wall, near the sink. The oven is under the cooktop at (6.91, -0.65) on the other counter. The two-door fridge is at (5.2, -0.57).
- The three tupperwares are in the fridge: one holds grated cheese (white shreds), one two small mushrooms, one four pepperoni discs.
- Done: the episode ends by itself on success. Nothing visible changes until the oven is closed and on.
