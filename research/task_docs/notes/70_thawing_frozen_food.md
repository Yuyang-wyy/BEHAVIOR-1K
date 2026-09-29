## Planner notes

**Tier:** D — a thaw state change via a running microwave, on top of two plate pick-and-places out of a French-door fridge.

### Goal in plain words

- The chicken breast must be not frozen, lying on a plate that is inside the closed microwave, with the microwave on.
- The bread slice must be not frozen, lying on the other plate, which rests on the bar (`bar_byvbuc_0`, the counter carrying the microwave and the cooktop).
- The fridge must be closed at the end.
- Either plate can serve either food (4 ground options), but each food starts on its own plate, so carry each plate with its food.

### Q traps

- 9 literals. `not open microwave` and `not open fridge` are true at reset, so they never score; max partial Q = 7/9 = 0.778.
- Result on 311 (ft40k): Q = 0.33, i.e. 3 of 7 scorable.
- **Thawing is nearly free** (PREDICATES §16):
  - At reset the foods are at -44 to -10 °C, depending on the instance, and the plates are at -2 °C.
  - Once the fridge door is open, the fridge stops cooling. At room temperature a food passes 0 °C in ~18-55 s (derived from §2).
  - So the bread thaws on the bar on its own. The chicken thaws in ~4 s once the microwave runs.
- `frozen` is not latched. A food put back in a closed fridge refreezes.
- **Microwave order:** plate in → door fully closed → press. It is a `requires_closed` toggleable, so a press with the door open does nothing, and opening the door later turns it off (§11).
- **Bread plate location:** the bar top is crowded.
  - The microwave takes x 5.86-6.38; the cooktop `burner_mdanhg` takes x ~6.5-7.3; the bar runs x 5.67-7.83.
  - A plate on the cooktop touches the burner, not the bar, so `ontop plate bar` is False (§4, derived).
  - The clear stretch is x ~7.3-7.8, past the cooktop.
- A second bar (`bar_egwapq_0`, at x 7.8-8.5 forming an L) is a distractor. A plate on it does not count.

### Minimal plan

1. `move to the fridge` ~12 s.
2. `open the door of the fridge` — it has two doors (French). Open the side the plates are behind; both start closed. ~30 s.
3. `pick up the plate from the fridge` — take the plate with the bread slice first. Shelf order varies: in 9/20 instances the bread is on the higher shelf. The plates sit at 0.72, 0.98, 1.22, 1.33 or 1.67 m. ~24 s.
4. `move to the bar`, `place the plate on the bar` — on the clear end past the cooktop. ~12 + 11 s.
5. `move to the fridge`, `pick up the plate from the fridge` — the plate with the chicken. ~12 + 24 s.
6. `close the door of the fridge` ~16 s (with the other hand, or after `hand over the plate` ~13 s).
7. `move to the microwave` ~12 s. `open the door of the microwave` ~30 s.
8. `place the plate in the microwave` — plate flat inside, chicken still on it. ~15 s.
9. `close the door of the microwave` — the door is flush. ~16 s.
10. `turn on the microwave` — the button marker turns green. ~10 s.

About 230 s against a 411 s limit.

### What the demos do differently

- 100/200 carry the bread plate first, then hold the chicken plate while closing the fridge, using `hand over the plate` twice to free a hand.
- 82/200 close and reopen the fridge between the two plates. This is not needed.
- All 200 thaw the bread by leaving it out; none microwave it.

### Hard parts and hacks

- **Plates:** forced to 0.248 × 0.248 × 0.016 m, lying flat on fridge shelves at 0.72-1.67 m. The grasp must pinch the 16 mm rim from the side. In 10/20 instances one plate is on the 1.67 m shelf.
- Food slides: the chicken (0.135 × 0.105 × 0.04 m) and the bread (0.15 × 0.15 × 0.02 m) sit loose on the plates. Tilting the plate drops them, and the `ontop food plate` literals are lost.
- **Microwave:** outer box 0.34 deep × 0.52 wide × 0.26 m high (`microwave_hjjxmi`), on the bar top at ~0.88 m. The plate just fits; all 200 demos do it.
  - Button: a ~21 mm sphere on the front panel, beside the door.
- Hack for the bread: opening the fridge alone thaws everything within a minute. Its bread literals then only need the plate on the bar.

### Hints for the VLM

- Kitchen, house_double_floor_lower. The fridge is a tall two-door unit (`fridge_petcxr`, x 5.2). The bar continues on its +x side, which is on the left when facing the fridge front: first the microwave, then a cooktop under a range hood, then free counter.
- Frozen food looks no different from thawed food in RGB. Rely on time out of the fridge, not appearance.
- Done: microwave closed with the chicken plate inside and its marker green; bread plate on the free bar end; fridge doors shut.
