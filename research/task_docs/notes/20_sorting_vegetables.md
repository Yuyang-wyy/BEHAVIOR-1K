## Planner notes

**Tier:** B — 13 vegetables go from two floor baskets into bowls on one countertop, all within ~4 m. Several are wider than the 44 mm span (onion 0.07 m, sweet corn 0.057 m, broccoli 0.06 m, bok choy 0.10 m); the leeks (0.038 m) fit.

### Goal in plain words

All 3 bok choy and all 3 onions must share one mixing bowl.
Both leeks and both broccoli must share one mixing bowl.
All 3 sweet corn must share one mixing bowl.
Each of the three groups picks its bowl independently (`exists` per group), so the groups do NOT have to use different bowls. The three bowls are identical and interchangeable.

### Q traps

- 13 literals, all False at reset (every vegetable starts in a wicker basket on the floor). Each vegetable is worth 1/13.
- 27 ground options: every assignment of the three groups to the three bowls, including all three groups in one bowl. Q takes the best option, so the planner does not need to track which bowl got which group, only keep each group's members together.
- Splitting a group across two bowls loses the minority: e.g. 2 onions in bowl A and 1 in bowl B scores only the 2 in the best option.
- `inside` needs each vegetable's AABB centre in the bowl's volume (PREDICATES §3). A vegetable resting on top of a heap above the rim does not count. A bowl is 0.36 x 0.32 x 0.17 m; putting all 13 in one bowl will overflow. Use the three bowls, one group each.
- A vegetable dropped on the counter or floor scores 0.

### Minimal plan

The two baskets are on the kitchen floor, 0.7-4 m from the start; the bowls are on `countertop_kelzer_0` at 0.96 m. `wicker_basket_220` holds broccoli, leeks and onions; `wicker_basket_221` holds bok choy and sweet corn.

1. `move to the wicker basket`, `pick up the wicker basket from the floors` — basket lifted off the floor. ~13 s + 12 s.
2. `move to the mixing bowl` — base at the countertop with the bowls in view. ~13 s.
3. From basket 220: `pick up the broccoli from the wicker basket`, `place the broccoli in the mixing bowl` (x2), then `pick up the leek from the wicker basket`, `place the leek in the mixing bowl` (x2), all into the same bowl. ~12 s + 4 s each.
4. `pick up the vidalia onion from the wicker basket`, `place the vidalia onion in the mixing bowl` (x3) into a second bowl. ~16 s each.
5. `place the wicker basket on the floors`. ~18 s.
6. Repeat step 1 for the other basket. Then `pick up the bok choy from the wicker basket`, `place the bok choy in the mixing bowl` (x3) into the onion bowl.
7. `pick up the sweet corn from the wicker basket`, `place the sweet corn in the mixing bowl` (x3) into the third bowl.
8. `place the wicker basket on the floors` — optional; no literal needs it. Skip it if time is short.

Budget: about 350 s against a 595 s limit. Placing the basket back on the floor (steps 5 and 8) is only needed to free the hand for the next basket.

### What the demos do differently

- Every demo carries a basket to the counter and sorts from it while holding it. Order of baskets and bowls varies; no two demos share a non-move sequence.
- Humans always put bok choy with onions and leeks with broccoli, as the goal requires, and use three different bowls.
- Both baskets go back to the floor at the end in all demos; that is not required.

### Hard parts and hacks

- Grasp span: leeks (0.038 m) fit easily. Onions (0.07 m), corn (0.057 m round), broccoli (0.06 m) and bok choy (0.10 m) are wider than 44 mm; graspable only on a narrower part (stem, leaf tip, cob end), unverified.
- Holding a basket in one hand while picking with the other: the basket is 0.30 x 0.45 x 0.19 m with no handle link. If carrying the basket fails, walking to the basket on the floor for each vegetable costs ~13 s per extra move.
- Bowl capacity: 3 bok choy (0.17 m each) plus 3 onions in one 0.36 m bowl is tight. Place the bok choy first, flat, then the onions.

### Hints for the VLM

- The bowls are the three identical mixing bowls on the long kitchen countertop. The kitchen also has one other countertop, a sink, a microwave, an oven and a fridge; there are no other bowls or baskets.
- The baskets are woven wicker baskets on the floor. Basket 220 has the green broccoli, long leeks and pale onions; basket 221 has bok choy and yellow corn cobs.
- Done for a group: every member visibly below the rim of the same bowl.
