## Planner notes

**Tier:** C — eight pick-and-places across two rooms, with plates on a 1.53 m cabinet shelf behind two doors, cupcakes in a closed fridge, and cupcakes wider than the jaw span.

### Goal in plain words

Both plates must rest on the breakfast table in `dining_room_0`. Each plate needs its own cupcake on it, and its own fork and its own table knife `nextto` it (a perfect matching, so which fork goes with which plate is free). Nothing is said about closing the top cabinet or the fridge, so leaving them open costs nothing. Cutlery only needs to be beside a plate on the table, not on it.

### Q traps

- All 8 literals start false; max partial Q is 1.0 (page is right).
- Cupcake literals need their plate but not the table: a cupcake on a plate counts even if that plate is not yet on the table. Still, carrying a loaded plate is risky; place plates first.
- `nextto` for fork/knife vs plate: L/6 is about 3.4 cm (fork 0.20 x 0.03 x 0.02 m, knife 0.24 x 0.02 x 0.01 m, plate 0.17 x 0.17 x 0.02 m). The cutlery must lie almost touching the plate rim. A fork 10 cm away scores nothing.
- Cutlery must sit on the table at plate height. On a chair or the floor beside the table, the height gap kills `nextto` (PREDICATES §5).
- `forpairs` needs one distinct fork and one distinct knife per plate. Two forks beside plate A and none beside plate B scores only one fork literal.
- Knocking a plate while laying cutlery can shift the cupcake off it or push the plate away from placed cutlery; lay cutlery on the far side from the approach.
- Both top-cabinet doors start closed (joint_pos 0.0; 0.02 on one door in instance 312, still inside the 5 % band) and the fridge is closed in all 20 instances. They are not in the goal.

### Minimal plan

1. `move to the top cabinet` — the middle of three identical wall cabinets is in view. ~26 s.
2. `open the door of the top cabinet` (twice, one per door) — both doors swung open, plates visible on the shelf. ~22 s each.
3. `push the plate to the top cabinet`, then `pick up the plate from the top cabinet`; repeat for the second plate with the other hand — each plate lifted clear of the shelf. ~11 s + ~18 s each.
4. Skip `close the door of the top cabinet` (not in the goal; saves ~31 s).
5. `move to the breakfast table` — table top fills the lower image. ~26 s.
6. `place the plate on the breakfast table` twice — both plates flat on the table, at least ~0.4 m apart, hands empty. ~9 s each.
7. `move to the electric refrigerator`, `open the door of the electric refrigerator` — door open. ~26 s + ~22 s.
8. `pick up the cupcake from the electric refrigerator` twice, one per hand — both grippers holding. ~18 s each.
9. Skip `place the cupcake on the bar` and `close the door of the electric refrigerator` (they exist only to free a hand for closing; saves ~40 s).
10. `move to the breakfast table`, then `place the cupcake on the plate` twice — one cupcake centred on each plate. ~26 s + ~9 s each.
11. `move to the sink`, `pick up the tablefork from the sink`, `pick up the table knife from the sink` — one item per hand. ~26 s + ~18 s each.
12. `move to the breakfast table`, `place the tablefork on the breakfast table`, `place the table knife on the breakfast table` — both lying against the rim of the same plate, one each side. ~26 s + ~9 s each.
13. Repeat steps 11-12 for the second fork and knife at the other plate.

About 520 s against an 890 s limit, versus 594 s for the demo.

### What the demos do differently

- 197/200 close both cabinet doors and the fridge; the goal does not need it.
- 196/200 park one cupcake on the kitchen bar (`place the cupcake on the bar`) to free a hand for the fridge door, then pick it up again.
- Cutlery prompts say `place the tablefork on the breakfast table`, not "next to the plate". The planner must steer placement to the rim; there is no trained `place ... next to the plate` sentence for this task. Closest: `place the tablefork on the breakfast table`.
- 22 demos pick the first plate without the `push the plate to the top cabinet` step.

### Hard parts and hacks

- Plates: 170 x 170 x 19 mm, flat on a shelf at z 1.53 m. The only graspable part is the 19 mm rim, and a finger must get under it. That is why demos push each plate to the shelf edge first so the rim overhangs. High reach plus a loaded extended arm risks tipping.
- Cupcakes: asset bbox 96 x 97 x 56 mm, wider than the 44 mm jaw span on every axis. Demos pick them 400 times, so some narrower sub-part (likely the frosting top) must register; which one is unverified. Expect cupcake grasps to be the most failure-prone step.
- Cupcake shelf varies: z 0.50, 0.91 or 1.31 across instances, sometimes the two on different shelves.
- Cutlery: fork 28 mm and knife 22 mm wide, easy for the jaws. In 6 of 20 instances (303, 310, 313, 314, 315, 318) one or two forks or knives lie in the sink basin (z 0.74) rather than on the deck (z 0.90), which needs a deeper reach.
- Nextto precision is the main Q risk: ~3 cm tolerance. After release, check in depth that the cutlery touches or nearly touches the plate edge; re-push it with `push the tablefork to the plate` (no trained prompt; closest `push the plate to the top cabinet`) if not.
- Base travel is ~5 m each way between kitchen (y ≈ -2 to 0) and table (7.3, 3.5). Four round trips dominate the time; carry two items per trip always.

### Hints for the VLM

- Plates are in the middle one of three identical top cabinets (`top_cabinet_lkxmne_1`) on the kitchen wall at x ≈ 4.0; the others are at y -1.6 and +0.65 and are empty distractors.
- Cupcakes are in the single fridge at the end of the counter (x 7.8). Forks and knives lie on or in the only kitchen sink (drop-in sink, x 5.8).
- The breakfast table (1.16 x 2.9 m, top 0.78 m) is the only table in `dining_room_0`, surrounded by 6 chairs. The low coffee tables are in other rooms; do not use them.
- The kitchen bar (x 7.3, y 0.2) is a handy staging surface but is not part of the goal.
- Done: two plates on the table, each with a cupcake on top and a fork and knife lying right against its rim.
