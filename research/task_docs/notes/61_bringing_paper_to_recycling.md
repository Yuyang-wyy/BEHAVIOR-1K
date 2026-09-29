## Planner notes

**Tier:** C — two flat or bulky paper items carried 7-22 m through a closed door to a lidded bin in the garden, with a two-handed lid opening.

### Goal in plain words

- The paper bag (`sack.n.01_1`, a `paper_bag`) and the newspaper must both end with their centres inside the recycling bin.
- The recycling bin's lid must be closed at the end.
- One ground option, 3 literals. There is one recycling bin in the scene and no trash can, so there is no choice of container.
- Doors along the way are not in the goal; leaving them open costs nothing.

### Q traps

- `not open recycling_bin` is true at reset and never scores. Verified: the lid joint is ~0 (closed) in the template and in all 20 instance files. Max partial Q is therefore 2/3; full success needs the lid shut again.
- The lid must be within 5% of its range from closed (PREDICATES §6). A lid resting on a newspaper edge that sticks up stays "open" and costs the success.
- Close the lid only after both items are in. Opening the lid again does not remove credit, but it wastes ~30 s.
- `inside` checks the item's AABB centre in the bin volume (PREDICATES §3). An item that lands on the closed lid, or drapes over the rim, does not count.
- Partial Q reads the final state only. Items set on the garden floor near the bin score nothing.

### Minimal plan

1. `move to the newspaper` — newspaper on the kitchen bar in view; ~19 s.
2. `pick up the newspaper from the bar` — newspaper lifted clear of the bar; ~15 s.
3. `move to the paper bag` — ~19 s.
4. `pick up the paper bag from the floors` — bag off the floor in the other gripper; ~15 s.
5. `move to the door` — base stopped at the closed door to the garden; ~19 s (route length varies, see hints).
6. `open the door of the door` — door visibly swung open; ~11 s.
7. `move to the floors` — base in the garden near the bin; ~19 s or more (humans take ~45 s here).
8. `place the paper bag on the floors` — ~15 s.
9. `place the newspaper on the floors next to the paper bag` — both hands free; ~13 s.
10. `move to the recycling bin` — ~19 s.
11. `open the lid of the recycling bin` — lid visibly raised and staying up; ~30 s.
12. `move to the paper bag`, `pick up the paper bag from the floors` — ~34 s.
13. `move to the newspaper`, `pick up the newspaper from the floors` — ~34 s.
14. `move to the recycling bin`, `place the paper bag in the recycling bin` — bag no longer visible above the rim; ~32 s.
15. `place the newspaper in the recycling bin` — ~13 s.
16. `move to the recycling bin`, `close the lid of the recycling bin` — lid flat on the bin; ~28 s.

Demo mean is 374 s against a 560.7 s limit. Dropping the demo's `close the door of the door` (~23 s) is safe for the goal.

### What the demos do differently

- Every demo opens and then closes a door on the way out (`close the door of the door`, 22.7 s mean, mostly labelled as navigation). Only opening it is needed to pass; closing it is optional. Whether the "close" segment also covers driving through the doorway is unverified.
- Every demo sets both items on the garden floor before opening the lid; the lid opening is labelled bimanual ("coordinated") in all 200 demos.
- Humans carry both items in one trip, one per hand. Keep that: a second round trip costs 15-45 s of driving each way.

### Hard parts and hacks

- **Distance.** The bin is in garden_0, 6.7-21.6 m from the start (301-310: 16.6, 14.7, 14.0, 21.6, 6.7, 13.6, 21.3, 12.4, 18.0, 10.2 m). Instances 304 and 307 are the longest.
- **Doors.** All garden doors start closed (joint_pos 0 in the template): kitchen-garden door_vudhlc_2 at (7.71, 3.43), corridor-garden door_vudhlc_1 at (0.11, -1.19) and door_vudhlc_0 at (0.12, 7.76), living_room-garden door_vudhlc_3 at (4.7, 7.67). The bin is always at x -16 to 0, y -3 to 2. The door humans use is not recorded; door_vudhlc_1 opens nearest the bin (unverified as the demo route).
- **Opening a door while both hands hold paper** is what the demos do. If the VLA drops items here, set them down first.
- **Newspaper grasp.** Forced size 0.41 x 0.31 x 0.03 m, lying flat on the bar top (z ~0.9). The only dimension under 44 mm is the vertical 30 mm, so a jaw must get under an edge. Fallback: `push the newspaper to the bar` is a trained sentence in task 52 (slide it to overhang the edge); it has no demo in this task.
- **Paper bag grasp.** Forced size 0.15 x 0.225 x 0.36 m; only the thin wall at the rim fits the jaw (unverified).
- **Lid.** Bin asset `recycling_bin/pdmzhv` is 0.57 x 0.43 x 0.82 m. Lid opening averages 30 s and is bimanual in demos. The lid must stay up by itself while the items go in (unverified). Closing is a push and needs no grasp.
- Both closed-loop runs on 311 scored Q 0.00.

### Hints for the VLM

- Start in kitchen_0. The newspaper is always on the bar `bar_egwapq_0` (the kitchen has two bars; the newspaper's bar is at x ~8). The paper bag stands on the kitchen floor, 0.7-4.9 m from the start.
- The recycling bin is the only bin in the loaded rooms. It stands on a garden_0 floor patch (z 0.4 root), 0.57 x 0.43 x 0.82 m, with a lid.
- The garden is large (6 floor patches, 26 trees, 55 bushes); bring the bin into view before driving far.
- Done: neither item visible outside the bin, and the lid lying flat on the bin.
