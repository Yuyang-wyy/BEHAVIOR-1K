## Planner notes

**Tier:** B — eight pantry items go from one countertop into kitchen cabinets, all within ~5 m. Most bodies are wider than the 44 mm span (sugar jar 0.078 m, olive-oil bottle 0.082 m body, oatmeal box 0.127 m, chips bag 0.10 m); grasps need a neck, rim or thin edge. The cabinet door must be opened first.

### Goal in plain words

Both oatmeal boxes, both chip bags, both olive-oil bottles and both sugar jars must each be inside some kitchen cabinet.
Every item picks its cabinet independently (`forall ... exists`), and all six kitchen cabinets count (`cabinet.n.01_*` covers the 3 top cabinets, the tall `bottom_cabinet_fancyy_0` and the 2 under-counter `bottom_cabinet_no_top` units). Items do not need to share a cabinet.
There is NO `not open` literal: cabinet doors may be left open.

### Q traps

- 8 literals, all False at reset. Each item is worth 1/8. 1,679,616 ground options (6 cabinets per item); Q takes the best, so the planner never needs to track which cabinet each item used.
- No cabinet needs closing. 198/200 demos close the door at the end; skip it. Closing it can also push an item back out of the volume (PREDICATES §3).
- `inside` needs the item's AABB centre in a cabinet's fillable volume (PREDICATES §3). Whether the `bottom_cabinet_no_top` units and the top cabinets have volumes in their USD is unverified; the demos only use `bottom_cabinet_fancyy_0`, so use it.
- All six cabinets start closed (every joint_pos 0 in the template and all 20 instances).
- An item left on the cabinet's open door or on top of the cabinet scores 0.

### Minimal plan

All items are on `countertop_kelzer_0`; the target cabinet `bottom_cabinet_fancyy_0` (1.97 m tall) is 1.1-5.1 m from the start.

1. `move to the bottom cabinet`, `open the door of the left_door bottom cabinet` — left door swung wide, shelves visible. ~21 s + 29 s.
2. `move to the bottle of olive oil`, `pick up the bottle of olive oil from the countertop`, twice (one per hand). ~21 s + 17 s each.
3. `move to the bottom cabinet`, `place the bottle of olive oil in the layer_2 bottom cabinet` twice. ~21 s + 17 s each.
4. Same pattern for the chips: `pick up the bag of chips from the countertop`, `place the bag of chips in the layer_3 bottom cabinet`.
5. Same for the sugar: `pick up the jar of sugar from the countertop`, `place the jar of sugar in the layer_2 bottom cabinet`.
6. Each oatmeal box, one at a time: `move to the box of oatmeal`, `tip over the box of oatmeal`, `push the box of oatmeal to the to_the_edge_of countertop`, `pick up the box of oatmeal from the countertop`, `move to the bottom cabinet`, `place the box of oatmeal in the layer_4 bottom cabinet`, `push the box of oatmeal to the center bottom cabinet`. ~21 + 8 + 12 + 17 + 21 + 17 + 12 s.
7. Stop. Do not close the door.

Done-check per item: item no longer on the countertop and visible on a shelf behind the door line.
Budget: about 580 s against a 994 s limit.

### What the demos do differently

- All 200 demos use only `bottom_cabinet_fancyy_0` and open its `left_door`.
- 198/200 close the door at the end; not needed for the goal.
- Every demo tips each oatmeal box onto its side, then pushes it to the counter edge before picking. The follow-up `push the box of oatmeal to the center bottom cabinet` shoves it deeper onto the shelf.
- The order of item types varies freely (top sequences cover only 2 demos each).

### Hard parts and hacks

- Grasp span: no item body is under 44 mm. The bottle neck is the likely grasp (width not in metadata; unverified). The sugar jar (0.078 m) may only be graspable at a lid rim, unverified.
- Oatmeal box (0.13 x 0.27 x 0.23 m): the tip-over + edge-push routine is how humans got a grip; it is in-distribution.
- Shelf heights of the tall cabinet (layers 2-4 in the prompts) are unknown; the cabinet is 1.97 m tall.
- If the door swings back while the arms are busy, it blocks the shelves. Open it wide.

### Hints for the VLM

- Target: the tall pantry-style cabinet (`bottom_cabinet_fancyy_0`, 0.65 x 1.23 x 1.97 m), the only full-height cabinet in the kitchen. The other five cabinets (three wall cabinets at 1.8 m, two under-counter runs) also count but are untested.
- All eight items start on the long kitchen countertop, which also holds the sink area. Another countertop exists; nothing is on it.
- Done: countertop clear of the eight items, all visible inside cabinets. The door can stay open.
