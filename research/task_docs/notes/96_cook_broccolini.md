## Planner notes

**Tier:** D. It needs cooking on top of pick-and-place. The demo shortcut makes it short: pour the whole plate into the pan, move the pan to the stove, turn the stove on. That is 9 skills and about 150 s.

### Goal in plain words

- All 3 broccolini and both garlic cloves must be resting on the frying pan and be cooked.
- The frying pan must be on the stove (`stove_ykretu_0`).
- The goal does not require the stove to stay on or be switched off.
- The plate is only the starting support.

### Q traps

- There are 11 literals and all score (0/11 true at reset). ft40k got 2/11 = 0.18 on instance 311. Which two is not recorded here.
- **Heat reaches the food, not the pan** (PREDICATES §2). Each food item's collision shape must be within 0.2 m of the stove's heat-source point.
- **Only one burner heats and only one knob toggles (derived from source).** The stove asset has 6 `heatsource` and 6 `togglebutton` meta links. `LinkBasedStateMixin.link` returns only the **first** link found (`link_based_state_mixin.py`, `next(iter(self.links.values()))`), and both `ToggledOn` and `HeatSourceOrSink` use that one. Which burner and knob come first is unverified.
  - The demos all end with `turn on the stove` after `place the frying pan on the stove`, so copying the demo placement is the safest bet.
- **Height (rough, derived).** From the asset metadata, the heat point sits about 0.16 m below the cooktop surface. Food in a pan is then only just inside the 0.2 m sphere, and only near the burner centre. Keep the pan centred on the active burner and the food spread flat in the pan, not piled at the rim.
- **`ontop X pan`** needs the item touching the pan, with the pan under its centre (§4). An item on top of another item (a clove on a broccolini) does not count. It needs direct contact with the pan.
- `cooked` latches (§15). Once 58 °C is reached, an item stays cooked even if the pan is later moved. It still has to be on the pan at the end.

### Minimal plan

1. `move to the plate`. Done when the plate with 5 items is centred on the commercial kitchen table. About 24 s.
2. `pick up the plate from the commercial kitchen table`. Done when the plate is lifted level with the items still on it. About 15 s.
3. `move to the frying pan`. About 24 s.
4. `pour the broccolini`. This is the demos' exact wording. Done when all 3 broccolini and 2 cloves are visible inside the pan. About 7 s.
5. `place the plate on the commercial kitchen table`. About 9 s.
6. `pick up the frying pan from the commercial kitchen table`. Grasp the pan's handle. About 15 s.
7. `move to the stove`. Keep the pan level and low. About 24 s.
8. `place the frying pan on the stove`. Done when the pan is resting flat on a burner. About 9 s.
9. `turn on the stove`. Done when a knob's toggle marker turns green. The episode should end within a second if all items are within range. About 17 s.

- Totals: about 145 s against a 230.9 s limit.

### What the demos do differently

- The demos match this plan (the modal order covers 57%).
- Every demo pours once (`pour the broccolini` appears 200 times in 200 demos). The other 5 orders differ only in extra `move to` steps.
- Nothing in the demos is superfluous except possibly putting the plate back, which frees the hand for the pan.

### Hard parts and hacks

- **Pouring 5 small items** (broccolini 0.088 x 0.044 x 0.041 m; clove 0.016 x 0.027 x 0.006 m) from a 0.30 m plate into a 0.28 m-wide pan. Cloves are light and scatter. Check all 5 are in the pan before lifting it. A stray clove costs 2 literals.
- **Carrying the loaded pan** (0.49 m including the handle) 1.5-4.6 m to the stove. Tilting or jerking spills items. Drive slowly with the pan low.
- If the stove is on and the episode does not end, some item is out of range or off the pan. Items are hard to re-grasp inside a hot pan. Try nudging the pan so it is centred on the burner whose marker is lit (unverified that the marker shows which burner heats).
- The plate is 0.297 x 0.297 x 0.018 m, so only a rim grasp works.

### Hints for the VLM

- The scene is a restaurant kitchen. The only stove is the 6-burner range (0.71 x 0.90 x 1.03 m). Flat-top grills, a deep fryer and an oven are distractors. Do not put the pan on a grill.
- The plate with its 5 items and the frying pan both start on a commercial kitchen table. The robot starts 1.4-4.7 m away.
- Done: the pan rests on the stove top with 3 broccolini and 2 cloves inside it, and a stove knob marker is green.
