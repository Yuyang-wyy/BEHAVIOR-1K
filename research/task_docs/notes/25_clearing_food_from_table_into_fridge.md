## Planner notes

**Tier:** C — container-in-container: the food goes into tupperware, then both tupperware go into the fridge. The half chicken (0.14 m smallest side) and tupperware (0.22 x 0.22 x 0.14 m) are wider than the 44 mm span; the half pie is 0.037 m thick lying flat on a plate.

### Goal in plain words

The half apple pie must be inside a tupperware, and the half chicken must be inside a tupperware (the same one or different ones; 4 ground options).
Both tupperware containers must be inside the kitchen fridge, and the fridge must be closed at the end.
The plates stay where they are; they have no goal.

### Q traps

- 5 literals. `not open fridge` is already true at reset (fridge joint_pos [0, 0] in all 20 instances), so it never scores. Max partial Q is 0.8; full success still needs the fridge closed.
- Both tupperware must be in the fridge, even an empty one (`forall` over tupperware). If only one tupperware is used for food, the other still has to go in.
- `inside food tupperware` is checked wherever the tupperware is. Food that slides out while the tupperware is carried or tilted into the fridge loses the literal. Place the tupperware level on a shelf.
- The fridge is side-by-side (`left_door`, `right_door`). `not open` fails if either door is past 5 % (PREDICATES §6). Close every door touched, last.
- The tupperware asset has no lid joint (no joint_pos in the template), so there is no lid to close.

### Minimal plan

All in kitchen_0. Food on plates on the breakfast table (1.4-3.4 m from start); tupperware on `bar_egwapq_0` (1.8-7 m); fridge 2-5 m.

1. `move to the tupperware`, `pick up the tupperware from the bar` twice (one per hand). ~22 s + 15 s each.
2. `move to the breakfast table`, `place the tupperware on the breakfast table` twice — both tupperware standing open on the table next to the plates. ~22 s + 7 s each.
3. `move to the half chicken`, `pick up the half chicken from the plate`, `move to the tupperware`, `place the half chicken in the tupperware`. ~22 + 15 + 22 + 14 s. Scores 1/5.
4. `move to the half apple pie`, `push the half apple pie to the to_the_edge_of plate`, `pick up the half apple pie from the plate`, `move to the tupperware`, `place the half apple pie in the tupperware`. ~22 + 23 + 15 + 22 + 14 s. Scores 1/5.
5. `move to the fridge`, `open the door of the right_door fridge` — right door wide open. ~22 s + 24 s.
6. `move to the tupperware`, `pick up the tupperware from the breakfast table` twice — keep them level. ~22 s + 15 s each.
7. `move to the fridge`, `place the tupperware in the layer_4 fridge`, `place the tupperware in the layer_5 fridge`. ~22 s + 14 s each. Each scores 1/5.
8. `close the door of the right_door fridge` — door flush. ~16 s. Success ends the episode.

Budget: about 430 s against a 653 s limit. Opening the fridge before step 1 (while the hands are empty) is an alternative the demos do not use.

### What the demos do differently

- All 200 demos bring both tupperware to the breakfast table first, then load the food there. 148 put the chicken and pie in different tupperware, 52 in the other pairing; none put both in one.
- All 200 push the half pie to the plate edge before picking it; keep that for the thin pie.
- An alternative the goal allows: carry the food to the tupperware on the bar instead. It saves no time because the tupperware must be carried to the fridge anyway.

### Hard parts and hacks

- Half chicken: 0.20 x 0.14 x 0.14 m, no dimension under 44 mm; unverified where a grasp would register (leg bone?).
- Half pie: 0.09 x 0.17 x 0.037 m, flat on a plate. The 0.037 m thickness fits the span only once the pie overhangs the plate edge.
- Tupperware: 0.22 m square, 0.14 m tall, no handle. The grasp must go across a wall. Carrying a loaded one level into a fridge shelf is the riskiest step.
- The fridge door handle width is unknown.

### Hints for the VLM

- The kitchen has one fridge (tall, two vertical doors), one breakfast table with four chairs, two bars (the tupperware sit on `bar_egwapq_0`), a dishwasher, an oven and a microwave.
- The two plates on the breakfast table hold the half chicken and the half apple pie. The two tupperware are identical clear containers.
- Done: breakfast-table plates empty, both tupperware on fridge shelves with food visible inside, both fridge doors flush.
