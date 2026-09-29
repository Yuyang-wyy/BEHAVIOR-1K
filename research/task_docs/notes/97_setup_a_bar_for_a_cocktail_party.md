## Planner notes

**Tier:** C. It moves 12 objects from the bottom cabinet to the bar and has 20 literals, including exact `nextto` pairings and a tray-to-bucket pour. Cans (0.081 m) and wineglasses (0.117 m bowls) are wider than the 44 mm jaws, so the grasp is unverified. Partial Q is easy to collect, though: ft40k already got 0.50 on instance 311.

### Goal in plain words

- **On the bar** (`bar_xxftww_0`): the wine bottle, all 3 soda cans, both wineglasses, the corkscrew, and the ice bucket.
- **Pairings:**
  - every can is next to some other can;
  - wineglass 1 is next to wineglass 2;
  - at least one wineglass is next to the bottle;
  - the corkscrew is next to the bottle.
- **All 6 ice cubes inside the ice bucket.**
- The tray and the fridge are not in the goal. The tray may stay on the cabinet.

### Q traps

- There are 20 literals and all score (0/20 true at reset). Q is the max over 54 ground options.
- Many ground options pair a can with itself (`nextto can_1 can_1`). Those literals can never be true, because a can is never in its own adjacency list (PREDICATES §2 and §5). The page shows the best option without them; each can needs a different partner.
  - Cluster all three in a row: the middle can serves both neighbours.
- **nextto gaps are tight (derived from §5 with the asset sizes):**

  | pair | allowed AABB gap |
  | --- | --- |
  | can-can | ≤ ~3.2 cm |
  | wineglass-wineglass | ≤ ~4.2 cm |
  | wineglass-bottle | ≤ ~4.1 cm |
  | corkscrew-bottle | ≤ ~3.2 cm |

  Place them almost touching.
- **Wineglass rays (derived, unverified):** the horizontal rays leave from each glass's AABB centre height, which may be at the thin stem. Rays could slip past the partner's stem. Put the bowls nearly touching.
- `ontop X bar` fails if the item's centre overhangs the bar edge (§4). Place well onto the counter.
- **Ice cubes:** each needs its centre in the bucket's volume. The bucket is rescaled to 0.204 x 0.246 x 0.234 m (`task_custom_lists.json`). Cubes spilled while carrying the bucket are lost.
- Knocking over a placed glass or can loses both its `ontop` and its pairing literals.

### Minimal plan

Group by trip, two items per trip, one per hand.

1. `move to the wineglass`, then `pick up the wineglass from the bottom cabinet` twice. About 45 s.
2. `move to the bar`, then `place the wineglass on the bar`, then `place the wineglass on the bar next to the wineglass`. About 41 s.
3. `move to the wine bottle`, then `pick up the wine bottle from the bottom cabinet`, then `pick up the corkscrew from the bottom cabinet`. About 46 s.
4. `move to the bar`, then `place the wine bottle on the bar` right beside one wineglass, then `place the corkscrew on the bar next to the wine bottle`. About 41 s.
5. `move to the can of soda`, then `pick up the can of soda from the bottom cabinet` twice, then `move to the bar`, then `place the can of soda on the bar` and `place the can of soda on the bar next to the can of soda`. About 85 s.
6. Third can: same pick, then `move to the bar`, then `place the can of soda on the bar next to the can of soda`. About 45 s.
7. `move to the tray`, then `pick up the tray from the bottom cabinet`, then `pour the ice bucket into the tray`. The demo wording actually means tipping the tray into the bucket on the cabinet. Done when no cube remains on the tray. About 45 s.
8. `place the tray on the bottom cabinet`, then `pick up the ice bucket from the bottom cabinet`, then `move to the bar`, then `place the ice bucket on the bar`. Carry it level. About 55 s.

- Totals: about 400 s against a 670.9 s limit.

### What the demos do differently

- The 8 most common orders (148 of 200 demos) all do the ice last: tray pour on the cabinet, then carry the bucket. The other items come in varying two-at-a-time orders (29 orders in total).
- They seldom re-adjust pairings. A planner should re-check each `nextto` gap by depth before moving on.
- Alternative for the ice: carry the empty bucket to the bar first, then carry the tray and pour there. This avoids a loaded-bucket carry, but has no trained prompt beyond the same `pour` sentence and is unverified.

### Hard parts and hacks

- **Grasp sizes (asset bbox; bucket and tray rescaled):**
  - can 0.081 m diameter;
  - wineglass bowl 0.117 m (stem thinner);
  - wine bottle 0.067 m (neck thinner);
  - corkscrew 0.112 x 0.088 x 0.021 m;
  - tray 0.165 x 0.24 x 0.045 m;
  - ice cube ~0.02 m.
- Picking the 6 cubes singly is hopeless in time. The pour is the only practical route.
- The bar top is ~1.1 m high (bar bbox height 1.097 m). Placing near the far side needs reach. Keep items near the bar's front edge, but with centres over the top.
- The bottom cabinet (olgoza) is closed at reset. Nothing needs to go inside it.

### Hints for the VLM

- Everything starts on the single bottom cabinet in bar_0: 3 cans, 2 wineglasses, the bottle, the corkscrew, and the tray with 6 cubes. The ice bucket is on the cabinet too.
- The target "bar" is the large counter (2.28 x 5.76 m bbox) in the same room. It also borders the dining room. A beer tap is in the room, but whether it stands on the bar is unverified.
- The fridge in the bar room is irrelevant.
- Done: 3 cans in a touching cluster on the bar; two glasses touching each other, with one also touching the bottle; the corkscrew against the bottle; the bucket on the bar with no cubes left on the tray.
