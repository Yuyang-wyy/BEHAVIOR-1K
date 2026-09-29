## Planner notes

**Tier:** C — container-in-container work: tacos are poured from plates into a tupperware, and the tupperware goes into the fridge. The tacos themselves cannot be grasped.

### Goal in plain words

Both tacos end inside the tupperware, and the tupperware ends inside the fridge. Both plates end resting on the kitchen's drop-in sink. The fridge must be closed at the end. The bottom cabinet the tupperware comes from is not in the goal.

### Q traps

- 6 literals. `not open fridge` is true at reset, so it never scores but blocks success. Max partial Q = 5/6 = 0.833.
- Result on 311 (ft40k): Q = 0.50, i.e. 3 of 6.
- **Close the fridge last**, after checking the tupperware is still inside. `inside` tests the AABB centre only; the door can shove the box out when it closes (PREDICATES §3).
- **Plates on the sink:** the sink asset has a faucet (`fluidsource`), and the faucet spout sits ~0.26 m above the basin near the drain.
  - If a plate's centre lies under the faucet, the up-ray hits the sink itself and `ontop` is False (PREDICATES §4, derived). Keep each plate's centre off the drain/spout line.
- **Two plates in one sink:** each plate is 0.35 × 0.41 m and the sink is 0.54 × 0.77 m overall, so the second plate will likely overlap the first.
  - `ontop` needs the plate itself to touch the sink. A plate resting only on the other plate fails (PREDICATES §4). Make sure it also rests on the basin or rim.
- A taco that bounces out of the tupperware during the carry scores 0 for that taco. Carry the tupperware level.

### Minimal plan

1. `move to the bottom cabinet no top` ~9 s.
2. `open the door of the bottom cabinet no top` — the door is open and the tupperware is visible. ~26 s. The cabinet has 4 doors; which one hides the tupperware varies (tupperware x 5.1-6.4).
3. `pick up the tupperware from the bottom cabinet no top` ~9 s.
4. `place the tupperware on the countertop` — next to the plates. ~8 s.
5. Skip `close the door of the bottom cabinet no top`; it is not in the goal. Close it only if it blocks the base.
6. `pick up the plate from the countertop` — lift a plate with its taco. ~9 s.
7. `pour the taco into the plate` (trained wording; it means tipping the plate over the tupperware) — the taco is visibly inside the box. ~6 s.
8. `place the plate on the sink` — the plate lies in or on the sink, off the spout line. ~8 s.
9. `move to the plate`, `pick up the plate from the countertop`, `move to the tupperware`, `pour the taco into the plate`, `place the plate in the sink` — the same steps for plate 2. ~40 s.
10. `move to the tupperware`, `pick up the tupperware from the countertop` ~12 s.
11. `move to the fridge` ~9 s. `open the door of the fridge` — single door. ~26 s.
12. `place the tupperware in the fridge` — the box is on a shelf, fully past the door line. ~9 s.
13. `close the door of the fridge` — the door is flush (within 5 % of closed). ~13 s.

About 200 s against a 335 s limit.

### What the demos do differently

- All demos close the cabinet door after taking the tupperware out (not needed).
- Plates go on the sink right after pouring. The demos place the second plate with `place the plate in the sink`, and both strings appear 200 times each.
- The tacos are never picked by hand; every demo pours from the plate.

### Hard parts and hacks

- **Tacos cannot be grasped:** 0.164 × 0.063 × 0.059 m. Both short axes exceed 44 mm. Pouring from the plate is the only route.
- **Plates:** 0.35 × 0.41 × 0.036 m, lying flat on the counter. A grasp must pinch the rim from the side. That is hard for the VLA; expect regrasps.
- **Tupperware:** 0.22 × 0.22 × 0.14 m, grasped by the wall/rim. It starts at 0.56 m inside a low cabinet (door closed).
- **Fridge:** `fridge_dszchb`, one door, fixed at x 7.82. The plates start on the countertop on both sides of the sink, 1-2 m away.
- Pouring over a 22 cm box from a 41 cm plate: a taco can land on the rim. Check it is below the rim before moving on.

### Hints for the VLM

- Kitchen, house_single_floor. The long countertop (`countertop_kelzer`) holds the sink in its middle and the two plates with tacos, one on each side of the sink (x ~5.1-5.3 and ~7.2-7.3).
- The tupperware is hidden in the low cabinet under that counter. It is not visible until a door opens.
- The fridge stands at the +x end of the same counter run (x 7.8), next to the plate on that side.
- Done: the sink holds two plates; the fridge interior holds the tupperware with two tacos in it; the fridge door is shut.
