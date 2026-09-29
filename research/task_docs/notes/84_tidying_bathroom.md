## Planner notes

**Tier:** C — four independent pick-and-places, but only the cork (18 mm) fits the 44 mm jaws. The toilet roll, tissue dispenser and bar soap are all wider than 44 mm on every axis, and the toilet is behind a closed WC door.

### Goal in plain words

Four things must hold at the end: the bar soap rests on the soap dish, the tissue dispenser rests on the wall-mounted sink (the vanity counter, "countertop" in the demos), the toilet roll rests on the toilet, and the cork is inside the trash can. The soap dish itself is not in the goal and can stay where it starts, on the sink counter.

### Q traps

- Four literals, each 1/4, all false at reset. They are independent, so each one banks 0.25.
- The soap dish, bar soap and cork all start on the sink counter. Moving the soap dish (all 200 demos pick it up and re-place it) earns nothing.
- `ontop` fails when any part of the target object is directly above the placed object's centre (PREDICATES §4). On the sink, avoid the basin under the faucet; use the flat counter. The mirror above is a separate object and does not matter.
- On the toilet: one toilet joint starts at 0.524 rad (joint_pos in all 20 instances). Which part that is (seat or lid) is not verified. If a raised lid overhangs the seat, a roll on the seat fails; the tank top or a closed lid is safer (derived).
- Placing the bar soap can tip the light soap dish (0.032 m tall) off the counter. Re-check both at the end.
- The cork (0.018 x 0.018 x 0.034 m) is tiny. It must drop past the trash can's rim (can `dnvpag`, single link, no lid).

### Minimal plan

1. `move to the cork` then `pick up the cork from the countertop` — cork in hand. ~19 s + 26 s.
2. `move to the trash can` then `place the cork in the trash can` — cork gone from the gripper, not on the rim. ~19 s + 24 s.
3. `move to the bar soap` then `pick up the bar soap from the countertop`, then `place the bar soap on the soap dish` — soap sitting in the dish. ~19 + 26 + 23 s.
4. `move to the tissue dispenser`, `pick up the tissue dispenser from the floors`, `move to the countertop`, `place the tissue dispenser on the countertop` — box standing on the counter away from the basin. ~87 s.
5. `move to the door` then `open the door of the door` — WC door swung open. ~19 s + 16 s.
6. `move to the toilet tissue`, `pick up the toilet tissue from the floors`, `move to the toilet`, `place the toilet tissue on the toilet` — roll resting on the toilet. ~87 s.

Budget: 650 s limit vs 433 s demo mean. The plan puts the one easy grasp (cork) first.

### What the demos do differently

- 15 skill orders; the most common covers 30%. All 200 demos open the WC door and pick up and re-place the soap dish on the counter (not needed).
- `pick up the cork from the countertop` (189) is more common than `... from the wall mounted sink` (11). Use the countertop wording.
- The representative demo carries the roll and the dispenser together, one per hand, and opens the door with the roll still held.

### Hard parts and hacks

- Grasp widths (asset bboxes): toilet roll 0.094 x 0.092 x 0.115 m; dispenser 0.111 x 0.232 x 0.120 m; bar soap 0.113 x 0.089 x 0.061 m. None has an axis of 44 mm or less. Expect these grasps to fail; the cork is the only safe point.
- The toilet (`toilet_aapttl_0`, at (-1.33, 5.47)) sits behind `door_ydokma_0` at (-1.14, 4.96), closed at reset. A second door, `door_uptpdr_0`, is also closed and is not on the demo route.
- Opening the door needs its handle; handle width is not verified.

### Hints for the VLM

- Scene hotel_suite_large, bathroom_0. The long wall-mounted sink (2.57 m vanity with a mirror above) holds the soap dish, bar soap and cork at the start.
- The roll and the dispenser start on the floor anywhere in the bathroom, 0.6-3.4 m from the start. The trash can also moves between instances.
- Six shelves are in the bathroom; none is a target.
- Done: cork in the can; soap in the dish; dispenser on the vanity counter; roll on the toilet.
