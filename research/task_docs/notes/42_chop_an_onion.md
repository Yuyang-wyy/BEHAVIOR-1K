## Planner notes

**Tier:** D — one slice-then-dice transition plus a particle transfer into a bowl and two place-in-sink moves.

### Goal in plain words

The onion must be diced: `diced__vidalia_onion` must exist. At least one diced particle must sit inside the bowl `bowl_73`. The paring knife `parer_74` and the cutting board `cutting_board_76` must both end with their AABB centres inside the drop-in sink `drop_in_sink_lkklqs_0`. **Tool:** the parer, the only slicer. The board is just a surface; the goal does not care where the cut happens.

### Q traps

- Four literals, all false at start, so max Q is 1.0.
- `real diced__vidalia_onion` needs two contacts: first the whole onion (becomes halves), then, after the 2 s re-arm, one half (§7). Dicing one half is enough; the second half is optional.
- `contains bowl diced` needs just **1 particle** in the bowl's volume (§13). A pour that drops even a few pieces in scores.
- **Sink drain.** The sink's `particleSink` is set to `default_non_fluid_conditions: []` (KB), which means it always removes physical particles, diced onion included, that reach its drain volume. Do not dice over the drain if you still need the pieces for the bowl. Losing particles probably does not undo `real`: the slot empties only on `system.clear()` (`behavior_task.py:672`). Whether the system clears when the count hits zero is not verified.
- Put the knife and the board in the sink **after** the pour. A board already in the sink cannot be used to pour.
- `inside` tests only the AABB centre (§3). A board leaning on the rim with its centre above the basin does not count.

### Minimal plan

1. `move to the cutting board`, then `pick up the cutting board from the bar`, then `place the cutting board on the bar next to the left drop in sink` — board beside the sink. ~5 s + ~19 s + ~14 s. This step is optional when the board already lies near the sink.
2. `move to the vidalia onion`, then `pick up the vidalia onion from the drop in sink` — onion lifted out of the basin. ~5 s + ~19 s.
3. `move to the cutting board`, then `place the vidalia onion on the cutting board` — ~5 s + ~13 s.
4. `pick up the parer from the bar` — ~19 s.
5. `chop the parer with the vidalia onion` — two halves visible. Lift the knife and hold it clear for more than 2 s. ~6 s.
6. `chop the parer with the half vidalia onion 75` — the half turns into small pieces. ~6 s. Skip the second half.
7. `place the parer in the drop in sink` — knife out of hand, in the basin. ~12 s. **This scores 0.25.**
8. `pick up the cutting board from the bar`, `move to the bowl`, then `pour the diced  vidalia onion into the cutting board` (sic, double space; it means pour from the board into the bowl) — pieces visible in the bowl. ~19 s + ~5 s + ~11 s.
9. `move to the drop in sink`, then `place the cutting board in the drop in sink` — board lying in the basin. ~5 s + ~12 s.

The plan takes about 210 s against a 320 s limit.

Grasp-free partial route (derived, untested; worth 0.75 at most):
- Chop the onion **where it lies in the sink**: `chop the parer with the vidalia onion`, then a half.
- Drop the parer in the sink.
- Push the board off the bar edge into the adjacent basin. No trained prompt; closest: `push the cutting board to the to_the_edge_of countertop` (seen in cook_cabbage).
- The bowl literal is lost.

### What the demos do differently

- They dice **both** halves (only one is needed).
- 173 of 200 demos first move the board next to the sink, and about 64 also move the bowl next to the board. These moves just shorten the reach for the pour and the final place.
- They hold the knife until both halves are diced, then drop it in the sink before picking up the board.

### Hard parts and hacks

- **Onion size.** The onion is 100 x 70 x 71 mm and its halves are about 97 x 68 x 41 mm. Neither fits the 44 mm span by bbox. The ft40k checkpoint still scored 0.5 on instance 311 (which two literals is not recorded). Chopping it in the sink avoids the onion grasp entirely.
- **Parer.** `lwpdhi` is 268 x 31 x 14 mm and fits the jaws.
- **Board.** It is 300 x 200 x 20 mm and lies flat, so its 20 mm edge is reachable only if it overhangs the bar edge. The pour needs a real grasp and a tilt.
- **Bowl.** `aspeds` is 225 mm across and 75 mm deep, a shallow target for the pour. Tilt slowly at close range.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. `bar_egwapq_0` is the counter along the x ≈ 8.2 wall. It has the drop-in sink at y ≈ 0.23 and top cabinets above.
- The onion starts **in the sink basin** (z 0.81), not on the counter. The board, parer and bowl are on the same bar, and their positions vary by up to about 2 m between instances.
- There is only one sink, one bowl, one knife and one board in the kitchen.
- Done: pieces in the bowl, knife and board lying in the sink. The episode ends by itself on success.
