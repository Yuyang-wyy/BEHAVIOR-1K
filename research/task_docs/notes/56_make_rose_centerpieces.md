## Planner notes

**Tier:** C — roses are thin-stemmed and should fit the jaw, but the vase (forced size 0.32 x 0.32 x 0.35 m) must also be carried, and nothing on it is verified to be <= 44 mm.

### Goal in plain words

- All three roses must end with their AABB centre inside the vase's volume, and the vase must rest on the coffee table.
- The task sentence says "four roses"; the BDDL and all 20 instances have **three** (`rose_78/79/80`). Do not search for a fourth.
- There is exactly one vase, one coffee table and one bottom cabinet in living_room_0 (template `init_info`), so there are no choices and no same-category distractors.
- Nothing must be closed or turned off. No literal is true at reset, so max partial Q is 1.0 (each literal = 0.25).

### Q traps

- `ontop vase coffee_table` needs the vase's centre x-y over the table top and the vase touching it; an edge overhang fails (PREDICATES §4).
- Carrying a filled vase can spill roses. A rose that falls out loses its `inside` literal; only the final state counts (§1).
- A rose lying across the rim scores nothing: `inside` tests only the rose's AABB centre (§3). The rose is 0.27 m long, so it must go in stem-down, not lie on top.
- **Measured 2026-09-23 (instance 311, `BEHAVIOR-1K/scripts/aspire_radio/rose_inside_probe.py`): the vase's fill volume is small and deep.** It spans only z 0.56-0.69 m with the vase on the table, which is 8 cm below the rim, and about 0.19 m across. A rose is about 0.25 m long. A rose standing upright on the cavity floor has its AABB centre only 7 mm under the volume top, so it passes by a hair. A rose that lands on another rose's stem sits higher and fails. Dropping three roses in from above failed at least one rose in 6 of 6 trials. Placing each rose so its lower end reaches the cavity floor, leaning 20-40 deg against a different side, passed all three in 3 of 3 trials. The opposite end-down orientation failed the third rose every time (which end is the bloom is unverified).
- The ft40k rollout on 311 (Q 0.75) fits this exactly. The video shows the vase on the table and all three roses visibly in it, and the episode then idled until the time limit. So one rose's centre sat above the volume.
- Planner consequence: after each `place the rose in the vase`, the rose must go down to the bottom, not rest on the others. Spread the roses to different sides of the vase, and push a high-standing rose down before moving on.

### Minimal plan

All demos (199/200) fill the vase on the cabinet first, then carry it. Follow that order; it keeps prompts in distribution.

1. `move to the rose` — done: roses and vase on the low cabinet centred in the head camera, base stopped. ~10 s.
2. `pick up the rose from the bottom cabinet` — done: gripper closed short of fully closed, one rose gone from the cabinet top. ~14 s.
3. `move to the vase` — ~10 s (often not needed: vase is on the same cabinet).
4. `place the rose in the vase` — done: gripper open, rose visible standing in the vase, stem hidden. ~11 s.
5. Repeat 1-4 for the other two roses. Demos often pick two roses (one per hand) before placing both.
6. `pick up the vase from the bottom cabinet` — done: vase lifted clear of the cabinet top, roses still in it. ~8 s.
7. `move to the coffee table` — ~14 s.
8. `place the vase on the coffee table` — done: vase upright on the table, gripper open, three roses still visible in it. ~10 s.

Total demo mean 151 s vs a 226.6 s limit: about 75 s of slack for retries.

### What the demos do differently

- 45% of demos use exactly 6 moves, 4 picks, 3 place-ins, 1 place-on. Only 18 distinct orders exist.
- 198 of 200 demos pick two roses (one per hand) before placing both in succession.
- `hand over the rose` appears 3 times in 200 demos; not needed.
- No demo moves the empty vase to the coffee table first (0/200). That alternative avoids carrying a full vase but has no in-distribution precedent for placing roses into a vase on the coffee table.

### Hard parts and hacks

- Vase pick-up: all 200 demo vase picks are single-arm (`uncoordinated`, mean 7.9 s), but the vase is 0.32 m across. Whether the jaw registers on its rim/neck under the 44 mm rule is unverified; this is the most likely failure.
- If the vase grasp fails, securing the three roses still gives Q = 0.75. Put the roses in first so a failed vase move costs only 0.25.
- Do not tilt the vase in transit; roses can slide out. Keep the carry low and slow.
- Rose insertion: lower the rose head-up, stem into the opening. A rose dropped from above may land on the rim.
- Cheap check: after step 8, count three rose heads above the vase opening in RGB.

### Hints for the VLM

- All objects are in living_room_0. Roses (0.27 x 0.13 x 0.08 m) and the vase start together on the low bottom cabinet (roses at z ~0.46 m).
- The coffee table is the low table ~1.2-1.9 m from the start pose; it is the only coffee table.
- The bottom cabinet in the living room is the only one there; a second bottom cabinet is in bathroom_0, a different room.
- Done for each rose: the rose stands in the vase opening, not resting on the rim or the cabinet.
- Done for the vase: upright on the coffee table top, fully on the surface, gripper released.
