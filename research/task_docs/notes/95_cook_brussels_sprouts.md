## Planner notes

**Tier:** D. It needs a fridge door, slicing 4 sprouts into 8 halves, moving all 8 into the oven, closing the oven, turning it on, and re-closing the fridge. It is one of the longest chains in the benchmark (human mean 522 s, about 48 skills).

### Goal in plain words

- All 8 halves must exist (each of the 4 whole sprouts sliced once), be cooked, and be inside the oven (`oven_amblrk_0`).
- The fridge `fridge_jtqazu_0` (the one holding the tupperware) and the oven must both be closed at the end.
- The baking sheet and the cutting board are not in the goal. They are only convenient.
- The second kitchen fridge (`fridge_jtqazu_1`) and the freezer are irrelevant.

### Q traps

- There are 26 literals. The two `not open` literals are true at reset and never score, so the best partial Q is 24/26 = 0.923.
  - Each sliced-and-placed half is worth 3 literals: `real`, `cooked`, `inside`.
  - An unsliced sprout leaves 2 slots empty, which is 6 literals lost.
- **Dicing destroys halves.** `half__brussels_sprouts` is diceable (PREDICATES §7). If the knife still touches a half 2 s after a cut, it re-arms and dices it. That half's `real` becomes False for good. Lift the knife clear immediately after each cut.
- **Heat reaches only food inside the oven** (§2, §15). The halves' own AABB centres must be in the oven's volume, with the door fully shut (within 5%) and the oven on. The oven has two joints (`door_leaf1`, `door_leaf2`), and both must be shut for `not open`.
- Cooking is quick once running: cook temperature 58 °C, oven steady state ~212 °C, so a few seconds (§15). `cooked` latches, so success fires as soon as all 8 are hot **and** both doors are closed. The oven is left on; the goal allows it.
- **Fridge left open blocks success** but costs no partial Q. Close it right after taking the tupperware.
- The oven starts off (`ToggledOn` false). Pressing the button while the door is open does not stick, because the oven's state `requires_closed`. Close the door first, then press.

### Minimal plan

1. `move to the electric refrigerator`. About 15 s.
2. `open the door of the electric refrigerator`. About 25 s.
3. `pick up the tupperware from the electric refrigerator`. About 9 s.
4. `close the door of the electric refrigerator`. Done when the door is flush. About 19 s.
5. `move to the commercial kitchen table`, then `place the tupperware on the commercial kitchen table`. About 21 s.
6. `pick up the tupperware from the commercial kitchen table`, then `pour the brussels sprouts and brussels sprouts and brussels sprouts and brussels sprouts into the tupperware`. The wording is the demos'; it means tip them out. Pour onto the **baking sheet** rather than the cutting board. About 19 s. See the hack below.
7. `move to the carving knife`, then `pick up the carving knife from the cutting board`. About 24 s.
8. `chop the carving knife with the brussels sprouts`, 4 times, once per sprout. Done when two halves are visible where the sprout was. Lift the knife away at once. About 6 s each.
9. `place the carving knife on the cutting board`. About 6 s.
10. `move to the oven`, then `open the door of the oven`. About 40 s.
11. `move to the baking sheet`, then `pick up the baking sheet from the commercial kitchen table`. About 24 s.
12. `move to the oven`, then `place the baking sheet in the oven`. Done when the sheet is inside, past the door plane. About 34 s.
13. `close the door of the oven`, then `turn on the oven`. About 29 s.

- Totals: about 290 s against a 783.1 s limit.

### What the demos do differently

- The demos slice on the cutting board, then move 8 halves one by one to the baking sheet. That is 1538 `place the half brussels sprouts on the baking sheet` segments over 200 demos, 150-200 s per demo.
- Slicing on the sheet avoids this. The halves spawn at the sprout's part poses (§7), so they land on whatever the sprout sat on. This is derived from source, not tested.
- The demos also move the cutting board and the baking sheet next to each other, which is not needed.
- About 162 distinct skill orders were seen, so there is no canonical order.

### Hard parts and hacks

- **Slice where you bake.** Pour or place the whole sprouts on the baking sheet and cut them there. No cutting board is needed, because the slicer ability is on the knife (§7).
- **Grasp sizes (asset bbox):**
  - Sprout 0.064 x 0.050 x 0.056 m: wider than 44 mm on every axis.
  - Half 0.050 x 0.052 x 0.032 m: thin only on its cut face.
  - Knife 0.277 x 0.037 x 0.024 m: graspable.
  - Baking sheet 0.249 x 0.416 x 0.023 m: flat; only a rim or edge grasp.
  - Tupperware 0.219 x 0.219 x 0.136 m.
- **Carrying the loaded sheet** risks spilling halves. A half that falls on the oven door or the floor loses `inside` (and possibly `cooked`).
- **Which oven compartment** has a fillable volume is not verified. The asset has two door leaves. Use the one the demos use (`open the door of the oven`).
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The scene is a restaurant kitchen: two identical fridges, one freezer, one oven, one stove, a deep fryer, flat-top grills and two commercial kitchen tables.
- The tupperware is in `fridge_jtqazu_0`. Check both fridges if unsure, but close whichever you open.
- The knife, the cutting board and the baking sheet start on a commercial kitchen table. The knife rests on the board.
- Done: 8 half sprouts are visible on the sheet inside the oven, both oven leaves and the fridge are shut, and the oven's toggle marker is green.
