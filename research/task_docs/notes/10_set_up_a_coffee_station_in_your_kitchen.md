## Planner notes

**Tier:** B — five small pick-and-place moves around a fixed coffee maker; the high shelf bottle and tight `nextto` gaps are the hard parts.

### Goal in plain words

The coffee maker stays on the countertop. The bottle of coffee, the saucer and the electric kettle each end next to the coffee maker. The coffee cup ends on the saucer. The paper coffee filter ends on top of the coffee maker. Sides (left/right/front) are free, and `nextto` does not require the countertop. Do not knock the coffee maker off the counter.

### Q traps

- `ontop coffee_maker countertop` is true at reset: it never scores but must stay true. Max partial Q is 5/6 = 0.833.
- The page's "true at start" column is incomplete. The five movable items spawn at random along the counter. An AABB estimate from the 20 instance poses (asset bboxes, `nextto` gap limit ~0.08-0.12 m) says:
  - kettle already within the gap in 303, 305, 309, 315, 316 (and near in 313, 320);
  - saucer already within the gap in 311 and 315.
  - The ray half of `nextto` is unverified, so treat these as "probably true at reset, will not score". If so, leave the item where it is: moving it earns nothing and risks losing success.
- `ontop paper_coffee_filter coffee_maker` fails if any part of the coffee maker is directly above the filter's centre (PREDICATES §4). The demos say `place the paper coffee filter in the coffee maker`; if that slot sits under a lid or hood of the maker, the literal is False. Maker geometry is unverified; resting the filter on the maker's topmost surface is the safe choice.
- The coffee maker asset has no fillable meta link, so "in" is not a checked relation anyway; only `ontop` counts.
- Cup on saucer: the cup must touch the saucer and its centre must be over the saucer (14.4 cm disc). Place the saucer first, cup last, or the cup rides along and may slide off.
- Gap limits are tight (derived, §5): saucer ~7.4 cm, bottle ~7.5 cm, kettle ~9.4 cm from the maker's AABB. "Next to" means almost touching.
- Saucer is 11 mm tall: its horizontal rays sit ~5 mm above the counter and must hit the maker's base. Unverified that the base is solid there.

### Minimal plan

1. `move to the paper coffee filter` ~9 s; `pick up the paper coffee filter from the countertop` ~15 s — filter off the counter.
2. `move to the coffee maker` ~9 s; `place the paper coffee filter in the coffee maker` ~19 s — filter visible on the maker's top, no maker part above it.
3. `move to the bottle of coffee`; `pick up the bottle of coffee from the shelf` ~15 s — bottle lifted off the wall shelf at ~1.6 m.
4. `move to the coffee maker`; `place the bottle of coffee on the countertop next to the left coffee maker` ~12 s — bottle upright, gap to maker a few cm.
5. Skip if the saucer already touches the maker. `move to the saucer`; `pick up the saucer from the countertop`; `move to the coffee maker`; `place the saucer on the countertop next to the right coffee maker` ~12 s.
6. Skip if the kettle already touches the maker. `move to the electric kettle`; `pick up the electric kettle from the countertop`; `move to the coffee maker`; `place the electric kettle on the countertop next to the right coffee maker` ~12 s. Use the side the saucer did not take.
7. `move to the coffee cup`; `pick up the coffee cup from the countertop`; `move to the saucer`; `place the coffee cup on the saucer` ~12 s — cup resting centred on the saucer.
- Total ~170 s against a 313 s limit (demo mean 209 s).

### What the demos do differently

- Order varies a lot (84 distinct orders, the modal one 11%); the modal one is the order above.
- Humans always carry the saucer and kettle, even when they start next to the maker (175/200 demos pick up each). Skipping these is safe only if the item already touches the maker.
- A few demos push the saucer along the counter (`push the saucer to the to_the_edge_of countertop`, 7); not needed.
- Left/right choice is split; any side works for the goal.

### Hard parts and hacks

- Bottle of coffee: 0.078 x 0.078 x 0.168 m after scale 0.62, so its body exceeds the 44 mm span; the cap or neck may be narrower (unverified). It sits on wall shelf `shelf_pfusrd_1` at ~1.6 m; reaching needs the trunk raised, and tipping risk grows with the arm extended high.
- Coffee maker is 0.30 x 0.30 x 0.43 m, top at ~1.3 m. In instances 301, 305, 309, 313 it stands almost directly under the bottle's shelf, so the filter placement has little headroom.
- Filter 0.14 x 0.13 x 0.10 m; grasp the paper rim. Cup 0.10 x 0.09 x 0.07 m; use the handle. Saucer 0.144 m disc, 11 mm thick; grasp the rim edge. Kettle 0.23 x 0.17 x 0.27 m; use the handle.
- Pushing the saucer or kettle the last few cm against the maker (`push the saucer to the to_the_edge_of coffee maker`, 1 demo) is a cheap way to close the gap.
- A bump can shove the maker toward the counter edge; `ontop` then fails if it falls.

### Hints for the VLM

- All items are on the kitchen_0 countertop except the bottle, which is on the wall shelf above it. The kitchen has two countertops and two wall shelves; the items are on `countertop_kelzer_0`.
- Coffee maker: the only one, ~43 cm tall box. Kettle: the only kettle. The water glass in the kitchen is a distractor for the cup.
- Done for each `nextto`: the item stands on the counter with no visible gap (a few cm at most) beside the maker.
- Done for the filter: it rests on the maker's top, visible from the side, not hidden inside.
- Done for the cup: cup centred on the saucer, and the saucer next to the maker.
