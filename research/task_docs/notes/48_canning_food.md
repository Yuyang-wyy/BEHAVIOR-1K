## Planner notes

**Tier:** D — two slice-then-dice transitions, two particle transfers that must fill each bowl past 20 %, and container round trips through a tall cabinet and the fridge.

### Goal in plain words

- Steak and pineapple must both be diced. **Tool:** the carving knife `carving_knife_207`, the only slicer, which starts on the cutting board.
- One bowl must be `filled` with diced steak and hold zero diced pineapple. The other bowl must be `filled` with diced pineapple and hold zero diced steak. Either bowl can take either food (4 ground options).
- Both bowls must end inside `bottom_cabinet_fancyy_0`, and the cabinet and the fridge must both be closed.

**Containers:** the two bowls `bowl_209` and `bowl_210` (`belcml`, 255 x 255 x 150 mm). There is no heat source. The board is just a work surface.

### Q traps

- 10 literals, and **6 are true at start**: both `inside bowl cabinet`, both `not contains` (the diced systems do not exist yet, so the argument is `None` and `contains` is False, §0/§13), `not open fridge`, and `not open cabinet`. Max partial Q is 4/10 = 0.4 (page is right).
- The 4 scoring literals are the two `real diced__X` and the two `filled`. Dicing both foods anywhere, even inside the fridge, is worth 0.2 with no object moved except the knife.
- **`filled` is the hard part.** It needs the particle cube volume, (2r)^3 × n, to exceed 20 % of the bowl's fillable volume (§13). Dicing samples particles on a 2r grid inside the half's volume (`DicingRule`, `transition_rules.py:1022-1032`), so the particle volume is roughly the food volume. The steak's bbox is only 1.2 L (130 x 190 x 50 mm), and the bowl is a large 255 x 150 mm bowl. Filling the steak bowl therefore needs **both** steak halves diced and nearly every piece poured in. It may be unreachable. The bowl volume and particle radius are not verified.
- **Cross-contamination.** One stray pineapple piece in the steak bowl (or the reverse) breaks that bowl's `not contains` (§13). Use a different pour target for each, and do not pour over a bowl that already holds the other food.
- For success everything must hold at the end: the bowls back in the cabinet with their pieces still in them, and both doors shut. `bottom_cabinet_fancyy` has no `openable_joint_ids`, so **all 3 of its joints** count toward `open` (`open_state.py:96` fallback, §6).

### Minimal plan

1. `move to the fridge`, `open the door of the fridge`, `pick up the steak from the high_level fridge`, `pick up the pineapple from the low_level fridge` (shelf words vary) — ~11 + 26 + 12 + 12 s.
2. `close the door of the fridge` — ~25 s.
3. `move to the cutting board`, `place the steak on the cutting board`, `place the pineapple on the countertop` — ~11 + 6 + 6 s.
4. `pick up the carving knife from the countertop` (at the start it lies on the board: `pick up the carving knife from the cutting board`) — ~12 s.
5. `chop the carving knife with the steak`, wait 2 s, `chop the carving knife with the half steak 212`, wait 2 s, `chop the carving knife with the half steak 212` — **dice both halves**. ~4 s each.
6. `place the carving knife on the countertop next to the right cutting board` — ~8 s.
7. `move to the bottom cabinet`, `open the door of the left_door bottom cabinet`, `pick up the bowl from the layer_2 bottom cabinet` — ~11 + 26 + 12 s. Leave that door open for now.
8. `move to the countertop`, `place the bowl on the countertop next to the right drop in sink` (or anywhere near the board), `pick up the cutting board from the countertop`, `pour the diced  steak into the cutting board` (sic, double space; board into bowl) — ~11 + 8 + 12 + 13 s.
9. `pick up the bowl from the countertop`, `move to the bottom cabinet`, `place the bowl in the layer_4 bottom cabinet` — ~12 + 11 + 13 s.
10. Repeat steps 3-9 for the pineapple with the second bowl, using `place the pineapple on the cutting board`, `chop the carving knife with the pineapple`, `chop the carving knife with the half pineapple 211` (twice), and `pour the diced  pineapple into the cutting board`.
11. `close the door of the left_door bottom cabinet` — every cabinet door flush. ~25 s.

The plan takes about 600-700 s against a 1149 s limit.

### What the demos do differently

- They move the board onto the sink before pouring (`place the cutting board on the drop in sink`, 771 segments). This probably keeps spilled pieces out of the bowl area; it is not required.
- They put the empty bowl in the sink as a stable pour target (`place the bowl in the drop in sink`). The sink's `particleSink` removes physical particles that reach its drain (KB `default_non_fluid_conditions: []`). Pour into the bowl, not near the drain.
- The pineapple half is often moved off the board and diced separately, with two pours. Both pineapple halves are diced.
- 69 steps and ~950 s in the representative demo, so the humans used most of the time budget.

### Hard parts and hacks

- **Grasp span.** The steak is 130 x 190 x 50 mm and the pineapple 279 x 115 x 110 mm. Neither fits the 44 mm span, and neither do their halves (steak halves ~110 x 125 x 47 mm, pineapple halves ~111 x 111 x 214 mm and 104 x 107 x 67 mm). The realistic grasp-free gain is to **dice both foods where they lie in the fridge** (0.2), then close the fridge.
- **Bowls.** The bowls (255 mm across) can only be held by the rim. They sit on cabinet shelves at z 0.55-1.55 in a tall pantry cabinet (1.97 m) next to the fridge.
- **Knife.** `usqmjc` is 318 x 72 x 16 mm, and the handle width is not verified.
- **Pour aim.** The board is a flat 350 x 250 mm plank with no rim, so pieces slide off during the carry. Carry it level and pour at close range.

### Hints for the VLM

- Kitchen of `house_single_floor`. From left to right along the y ≈ -2 wall: sink (x 5.8), dishwasher, fridge (x 7.8), then the tall pantry cabinet `bottom_cabinet_fancyy_0` at x ≈ 8.7, which also houses the wall oven. The board and knife are on `countertop_kelzer_0` on the same wall.
- The steak is a flat brown-red slab and the pineapple is a tall yellow-green fruit, both in the fridge. There are two identical bowls in the pantry cabinet.
- Done: two bowls on pantry shelves, one visibly heaped with red cubes, one with yellow cubes, and all doors flush.
