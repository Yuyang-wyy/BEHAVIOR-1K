## Planner notes

**Tier:** B — six hardbacks (0.018-0.031 m thick) go from four low bookcases into one storage box, all in one room. The thickness fits the 44 mm span, but only once a book overhangs its shelf edge (a push first, as every demo does). ft40k and zs_pt50 both scored 0 on instance 311.

### Goal in plain words

All six books must be inside the storage box (`storage_box_49`).
Book order and position inside the box are free, and the box can be anywhere.
Nothing else matters: the bookcases need no tidying and the box need not return to the floor.

### Q traps

- 6 literals, all False at reset (each book starts inside a bookcase, the box on the floor). Each book is worth 1/6.
- `inside` needs each book's AABB centre in the box's volume (PREDICATES §3). The box is shallow (0.48 x 0.50 x 0.12 m). A book leaning on the rim with its centre above the rim does not count. Lay books flat in the box.
- Stacked books are fine as long as each centre stays below the top of the box volume; six flat books of up to 0.031 m make a ~0.16 m stack, taller than the 0.12 m box. Lay them in two or more piles side by side (the box floor fits about four 0.25 x 0.19 m books).
- If the box is carried to the sofa and later tips or slides, books spill out and lose their literals.

### Minimal plan

All objects are in living_room_0 (the only room loaded). Bookcases are 0.85-7 m from the start; the box 1.5-6.6 m.

1. Optional: `move to the storage box`, `pick up the storage box from the floors`, `move to the sofa`, `place the storage box on the sofa` — box sitting level on the sofa seat. ~34 + 18 + 34 + 21 s. All 200 demos do this to raise the box; it is not required by the goal. Skip it if the arm can reach into a floor-level box.
2. `move to the hardback` — book visible on a bookcase shelf. ~34 s.
3. `push the hardback to the to_the_edge_of bookcase` — book overhangs the shelf front edge. ~27 s.
4. `pick up the hardback from the 2X1 bookcase` (shelf label as seen: `2X1`, `2X2`, `3X1`, `3X2`) — book lifted clear. ~18 s.
5. Repeat 2-4 for a second book with the other hand.
6. `move to the storage box`, `place the hardback in the storage box` twice — books lying flat inside, grippers open. ~34 s + 18 s each.
7. Repeat steps 2-6 two more times.

Done-check per book: book no longer on its shelf, visible lying inside the box walls.
Budget: about 700 s with step 1, 600 s without, against a 1211 s limit.

### What the demos do differently

- 199/200 demos move the box onto the sofa first.
- All 200 demos push every book to the shelf edge before picking; 1200 push segments in total. Keep this.
- Books are collected two per trip (one per hand) in all demos, in varied bookcase orders.

### Hard parts and hacks

- Books lie flat on low shelves (z 0.40-0.76 m). The grasp across the 0.02-0.03 m thickness is only possible at the shelf edge, hence the push. Per project memory, a book flat on a surface is one of the hardest grasps for the R1Pro.
- The box has no handle link (0.48 x 0.50 x 0.12 m); step 1 needs a grasp across a wall, unverified.
- The four bookcases are identical and low (1.05 m). Keep track of which books are done; the demo's shelf words (`2X1`, `3X2`) are shelf-grid positions.

### Hints for the VLM

- Four identical short bookcases (0.76 m wide, 1.05 m tall) stand in the living room; bookcases 1 and 2 hold two books each, 3 and 4 hold one each. There are no other books in the room.
- The storage box is the only box: a wide, shallow open box on the floor.
- The room also has a sofa, an armchair, a coffee table, a desk and a staircase with railings. Keep the base away from the stairs.
- Done: all four bookcases empty of hardbacks, six books inside the box.
