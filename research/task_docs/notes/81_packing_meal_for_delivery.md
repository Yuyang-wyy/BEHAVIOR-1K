## Planner notes

**Tier:** C — container-in-container: three burgers into three paper bags, then the bags onto the floor of an open storage box. The burgers (50 mm thick) and bag bodies exceed the 44 mm jaw span.

### Goal in plain words

Each wrapped hamburger must be inside a different paper bag, and all three bags must rest on the storage box. Which burger goes in which bag is free (`forpairs`, 6 ground options). The tray is not in the goal. Everything starts on one commercial kitchen table.

### Q traps

- Six literals, each 1/6. None is true at reset.
- `forpairs` needs one burger per bag. Two burgers in one bag score only one of those two `inside` literals.
- `ontop sack storage_box` needs the bag to touch the box and the ray down from the bag's centre to hit the box (PREDICATES §4). The storage box has no lid object in the scene (template checked), so a bag standing on the box floor works. A bag leaning on the rim with its centre outside the box does not.
- Box fit (derived from bboxes): the box is 0.50 x 0.51 x 0.21 m (forced size); each bag is 0.137 x 0.291 x 0.508 m. Three bags fit side by side only with their thin sides together (3 x 0.137 = 0.41 m). The interior is smaller than the outer bbox; the exact inner size is not verified.
- The bags are 0.51 m tall and the box only 0.21 m, so a bag can tip out of the box. A tipped bag can also drop its burger. Re-check all six literals at the end.
- Whether the paper bag asset has a fillable volume is not verified (not readable from metadata).

### Minimal plan

1. `move to the paper bag` — bags on the table in view. ~15 s.
2. `pick up the paper bag from the commercial kitchen table` — one bag held by its rim. ~14 s.
3. `move to the wrapped hamburger` — tray with burgers in view. ~15 s.
4. `pick up the wrapped hamburger from the tray` — burger in the free hand. ~14 s.
5. `place the wrapped hamburger in the paper bag` — burger gone into the held bag. ~16 s.
6. `move to the storage box` then `place the paper bag in the storage box` — bag standing upright in the box. ~15 s + 16 s.
7. Repeat 1-6 twice, standing each new bag beside the previous ones.

Budget: 443 s limit vs 295 s demo mean. About 90 s per bag cycle.

### What the demos do differently

- 42% follow the order above: bag in one hand, burger dropped into it, bag into box.
- The demo string `place the paper bag in the storage box` is the trained wording, although the goal predicate is `ontop`.
- All objects stay within about 2.5 m of each other on one table. Most `move to` steps are short turns.

### Hard parts and hacks

- Burger (asset bbox 0.092 x 0.102 x 0.050 m) has no axis under 44 mm. It lies flat on a tray, so the grasp may fail outright.
- The bag must be held by its thin paper wall at the rim; the body is 137 mm across (asset bbox). This grasp is not verified.
- Alternative order (untested): stand all three bags in the box first, then drop one burger into each bag there. This avoids carrying a loaded bag, but the bag opening is then about 1.4 m high on a 0.87 m table (derived).
- Partial-credit route: bags into the box alone give 3/6 even if no burger can be grasped.

### Hints for the VLM

- Scene restaurant_diner, kitchen_0. The target table is `commercial_kitchen_table_vxvtec_0`; a second commercial kitchen table stands at the other end of the kitchen (about 4.5 m away) and is empty of task objects.
- Three identical tall (0.51 m) paper bags, a tray with three wrapped burgers, and an open storage box, all on one table.
- Done: three bags standing inside the open box, each with one burger at its bottom.
