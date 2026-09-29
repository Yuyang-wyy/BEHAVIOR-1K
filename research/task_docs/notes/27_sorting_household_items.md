## Planner notes

**Tier:** B — six small items move from two floor hampers to a bathroom vanity and shelf, but the bathroom sliding door must be opened first and two placements (`under`, `inside` a coffee cup) are geometrically tight. Item widths vs 44 mm are unknown (no custom list).

### Goal in plain words

Both detergent bottles end up on the floor under the multi-station furniture sink and next to each other. The box of sanitary napkins sits on the bathroom shelf. The soap dispenser sits on the sink. The coffee cup stays on the sink, the toothbrush is inside the cup and the toothpaste tube is next to the cup. There is exactly one ground option: no free choice of furniture. No door or hamper state is checked.

### Q traps

- `ontop cup sink` is true at reset and never scores. Max partial Q is 7/8 = 0.875. Knocking the cup off still blocks full success.
- The cup is the anchor for two literals. Tipping it while inserting the toothbrush can lose `ontop cup sink` (blocks success) and the toothbrush literal.
- `inside toothbrush cup` tests the toothbrush's AABB centre (PREDICATES §3). A long brush leaning out of a small cup may have its centre above the rim. Push it down as far as it goes. Unverified whether the cup is deep enough.
- `nextto toothpaste cup` is a small–small pair: the gap must be about L/6, a few cm (§5). Demos drop the tube into the cup instead. Derived: inside the cup the AABBs overlap (gap 0) and the tube's horizontal rays hit the cup wall, so `nextto` holds.
- `under detergent sink` needs sink geometry directly above each bottle's centre (§9). Push each bottle fully under the basin or counter overhang. Whether the vanity has open space below is unverified.
- `nextto detergent_1 detergent_2`: bottles side by side, nearly touching. Place the second one right against the first.
- `ontop soap_dispenser sink`: keep it clear of the faucet. Any part of the sink above the dispenser's centre fails the literal (§4).
- Closed-loop on 311: zero-shot Q 0.50, fine-tuned 40k Q 0.00.

### Minimal plan

1. `move to the sliding door` — the bedroom–bathroom sliding door (closed at reset per template joint_pos). ~23 s.
2. `open the door of the sliding door` — doorway clear in RGB-D. ~49 s. Nothing requires closing it again.
3. `move to the bottle of detergent` — hamper with bottles in view. ~23 s.
4. `pick up the bottle of detergent from the hamper` (x2, one per hand) — both grippers closed short of full. ~21 s each.
5. `move to the multi station furniture sink`. ~23 s.
6. `place the bottle of detergent under the multi station furniture sink` (x2) — bottles on the floor below the vanity, touching each other. ~18 s each.
7. `move to the soap dispenser`; `pick up the soap dispenser from the hamper`. ~44 s.
8. `move to the box of sanitary napkins`; `pick up the box of sanitary napkins from the hamper`. ~44 s.
9. `move to the multi station furniture sink`. ~23 s.
10. `place the soap dispenser on the multi station furniture sink` — resting on the counter, away from the faucet. ~15 s.
11. `place the box of sanitary napkins on the shelf` — box resting on the bathroom shelf. ~15 s. The shelf is reachable from the sink spot in most demos.
12. `move to the toothbrush`; `pick up the toothbrush from the hamper`. ~44 s.
13. `move to the tube of toothpaste`; `pick up the tube of toothpaste from the hamper`. ~44 s.
14. `move to the coffee cup`. ~23 s.
15. `place the toothbrush in the coffee cup` — brush standing in the cup, cup still upright. ~18 s.
16. `place the tube of toothpaste in the coffee cup` — or, if the cup is full, no trained prompt; closest: `place the tube of toothpaste in the coffee cup`, released touching the cup's side. ~18 s.

Budget: ~515 s demo mean vs a 790 s limit.

### What the demos do differently

- All 200 demos open the sliding door first.
- 193 demos `push the hamper to the away robot` (and 48 `... near robot`) to get a better reach at the items. Not in the goal; use only if an item is out of reach.
- 7 demos pick up and re-place a hamper. Not needed.
- Some demos stand at `the shelf` for the box (12 uses of `move to the shelf`); most place it from the sink position.
- Order is always: detergents, then soap and box, then toothbrush and toothpaste.

### Hard parts and hacks

- Opening a sliding door is slow (49 s mean) and the handle width is unverified.
- Picking items out of a hamper on the floor: low reach, walls of the hamper, items can be stacked.
- Placing a bottle `under` a vanity from standing height: the arm must reach low and far forward.
- The toothbrush-in-cup step is the most likely to fail and can knock the cup off the counter. Do it last so earlier literals are safe.
- If the cup falls, `ontop cup sink` fails and success is lost, but partial Q keeps the other literals.

### Hints for the VLM

- Items start in two hampers on the bedroom_0 floor. Hamper 1 holds both detergents and the napkin box; hamper 2 holds soap, toothbrush and toothpaste.
- The bathroom is bathroom_1, behind sliding door `sliding_door_tprpvb_10` from bedroom_0. The house has many identical sliding doors; the right one leads from the bedroom into the room with the sink, toilet and bathtub.
- bathroom_1 has one multi-station furniture sink (the vanity), one shelf (z ~1.05 m, next to the sink), one coffee cup (z ~0.79 m, on the sink counter).
- Done: two bottles side by side on the floor below the vanity, box on the shelf, dispenser on the counter, brush sticking out of the upright cup, tube in or touching the cup.
