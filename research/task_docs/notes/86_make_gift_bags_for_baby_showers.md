## Planner notes

**Tier:** C — the die (33 mm) and wafer (33 x 199 x 18 mm) fit the jaws, but it is container-in-container work: the wafers start inside closed cabinet drawers and the filled paper bags must be carried to the coffee table.

### Goal in plain words

Both paper bags must rest on the coffee table. Each bag must hold one toy die and one wafer. Which die and which wafer go into which bag is free (two independent `forpairs`, 4 ground options). The cabinet drawers may be left open: there is no `not open` literal.

### Q traps

- Six literals, each 1/6, all false at reset.
- Each `forpairs` needs one item per bag. Two dice in one bag, or two wafers in one bag, score only one of that pair.
- `ontop sack coffee_table` is read at the end. A bag that tips over on the table still touches it, but its items may fall out and lose `inside`.
- Whether the paper bag asset has a fillable volume is not verified (not readable from metadata).
- The wafers start inside `bottom_cabinet_jhymlr_0`, whose six openable links are all closed at reset (joint_pos 0 in all 20 instances). Which drawer holds a wafer varies by instance: the wafers lie near the cabinet front at z 0.61, anywhere along its 1.65 m width. Two wafers can share one drawer (instance 311: same x-y, stacked).
- The two dice start on top of the same cabinet (z 0.77).

### Minimal plan

1. `move to the paper bag` then `pick up the paper bag from the breakfast table` — one bag in each hand (repeat the pick). ~12 s + 2 x 17 s.
2. `move to the coffee table` then `place the paper bag on the coffee table` twice — both bags standing on the coffee table. ~12 s + 2 x 14 s.
3. `move to the bottom cabinet` then `open the drawer of the bottom cabinet` — drawer out, wafer visible. ~12 s + 14 s.
4. `pick up the wafer from the bottom cabinet` and `pick up the toy dice from the bottom cabinet` — one item per hand. ~17 s each.
5. `move to the paper bag`, `place the wafer in the paper bag`, `place the toy dice in the paper bag` — both into the same bag. ~12 s + 2 x 12 s.
6. Repeat 3-5 for the second wafer and die, into the other bag. Open another drawer if the second wafer is not in the first.

Budget: 483 s limit vs 322 s demo mean. Placing the empty bags first (steps 1-2) is not the demo order but avoids carrying loaded bags.

### What the demos do differently

- 94 distinct orders; the most common covers only 4.5%. The usual pattern fills the bags on the breakfast table and carries both full bags to the coffee table at the end.
- Demos close the drawer after each wafer (314 closes over 200 demos). Not needed.
- `move to the wafer` (275) and `move to the toy dice` (154) are alternative approach prompts.

### Hard parts and hacks

- Finding the wafer: it is hidden in one of six closed drawers or doors. The planner may need to open more than one; each open costs ~14 s.
- The bag (asset bbox 0.101 x 0.150 x 0.240 m) must be held by its thin paper wall at the rim. Not verified.
- Distances: breakfast table `breakfast_table_skczfi_0` at (1.47, 0.41); cabinet at (1.66, -1.50), facing -x; coffee table at (-0.48, -1.22). The bags move about 2.5 m.
- Alternative (untested): dropping a wafer into a bag already on the low coffee table (top about 0.39 m, bag rim about 0.63 m) is a lower reach than the breakfast table.

### Hints for the VLM

- Scene Rs_int, living_room_0. Two small paper bags stand on the breakfast table near the kitchen side. The dice sit on top of the long living-room bottom cabinet; the wafers are inside it.
- A second breakfast table stands at (0.17, -3.77); it holds no task objects.
- Done: two bags upright on the coffee table, each holding one die and one wafer.
