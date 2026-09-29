## Planner notes

**Tier:** C — three pick-and-places of wide objects: two pillows (0.49 x 0.33 x 0.09 m) and a tissue dispenser (0.10 x 0.19 x 0.17 m), none with an axis under 44 mm.

### Goal in plain words

Each bed must end with one pillow on it, and the tissue dispenser must rest on any stand. The pillows must go to **different** beds (`forpairs`). The stand can be any of four: the long low stand along the wall or one of the three nightstands. The chair in the task sentence is not in the goal.

### Q traps

- Three literals, each 1/3, all false at reset. Q takes the best of 8 ground options.
- `forpairs` pillow-bed needs a perfect matching. Both pillows on one bed score only 1 of the 2 pillow literals (max 2/3 with the dispenser).
- `ontop` needs the pillow's centre over the bed and nothing of the bed above it (PREDICATES §4). A headboard overhang is not verified; the middle of the mattress is safe.
- `push the chair to the desk` (in all 200 demos) earns nothing. Skip it.
- The fact page lists `stand.n.04_2..4` as "(runtime)". The instances resolve them to the three nightstands `nightstand_maeowc_0/1/2` at x -1.97, y -3.66 / -1.42 / 0.82, beside the bed heads. `stand.n.04_1` is `stand_dbskvf_0`, a 7.5 m long, 0.38 m high stand along the x 2.12 wall.

### Minimal plan

1. `move to the tissue dispenser` then `pick up the tissue dispenser from the armchair` — box lifted off the armchair. ~25 s + 41 s.
2. `move to the nightstand` then `place the tissue dispenser on the nightstand` — box standing on a stand top. ~25 s + 35 s. The long wall stand is closer (see hacks), but no demo prompt names it; closest trained wording is this one.
3. `move to the pillow` then `pick up the pillow from the floors` — pillow held. ~25 s + 41 s.
4. `move to the bed` then `place the pillow on the bed` — pillow lying on the first bed. ~25 s + 35 s.
5. Repeat 3-4 with the second pillow, placed on the **other** bed.

Budget: 643 s limit vs 429 s demo mean. Dropping the chair push saves about 55 s.

### What the demos do differently

- All 200 demos use one order: both pillows picked (one per hand), first pillow placed, chair pushed to the desk, second pillow placed, then the dispenser.
- Humans carry both pillows at once. Placing them on two different beds is required, though the prompt `place the pillow on the bed` does not say which.

### Hard parts and hacks

- Grasp widths (asset bboxes): pillow 0.49 x 0.327 x 0.089 m, lying flat on the floor; dispenser 0.10 x 0.191 x 0.168 m. Neither fits 44 mm. Expect grasp failures.
- The dispenser starts on `armchair_ybcnmu_0` at (1.63, -4.44). The long stand `stand_dbskvf_0` runs along x 2.12 from about y -4.46 to 3.08, so its end is roughly 0.5 m from the armchair (derived from poses and bbox). That is the shortest valid target; the nightstands are 3.6 m or more away.
- The pillows start anywhere on the bedroom floor, up to 6 m from the start and up to 7.7 m apart between instances.
- The beds (`bed_kddswt_0` at y -2.54, `bed_kddswt_1` at y -0.29) are 2.17 x 1.59 m, side by side with ottomans at their feet.

### Hints for the VLM

- Scene hotel_suite_large, bedroom_0. Two identical beds side by side; two identical pillows on the floor; a small tissue box on the armchair near the long wall stand.
- The long low stand under the wall TV counts as a stand; a TV above it is a separate object and does not block `ontop`.
- Done: one pillow on each bed, tissue box on a stand top.
