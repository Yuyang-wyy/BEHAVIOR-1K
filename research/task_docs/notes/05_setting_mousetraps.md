## Planner notes

**Tier:** B — plain pick-and-place of four small traps from a cabinet top to the floor; no doors, no state change. Grasp width is borderline (see Hard parts).

### Goal in plain words

- All four mousetraps must rest on the bathroom floor (`floors_tfuahz_0`, the only floor in bathroom_0).
- At least two of them must be `under` or `nextto` the bathroom sink (`furniture_sink_ojjqku_0`, the only sink in the room).
- The traps are interchangeable; any two can be the sink pair, and `under` vs `nextto` is free per trap.
- The traps start **on top of** the closed bottom cabinet (z 0.89 m), not inside it. No door needs opening, despite the instruction's "from the cabinet".

### Q traps

- 6 literals in the best option (4 `ontop floor` + 2 sink literals); none is true at reset, so every literal scores.
- The sink part is `forn (2)`: success needs **exactly** two traps under/next to the sink. A third one there blocks success (PREDICATES §0).
- Partial Q is still 6/6 = 1.0 with three or four traps at the sink, because each ground option names only two traps (PREDICATES §0-1). The overshoot only costs early termination, not score.
- A trap on the sink pedestal, the bathtub rim, the serving cart or the toilet does not count as `ontop floor`.
- A trap resting on another trap does not touch the floor, so `ontop floor` is False for it (PREDICATES §4).
- Cabinet joints start at 0 (closed) per template `joint_pos`; the goal does not check them, so bumping a door costs nothing.

### Minimal plan

Demo pattern (93% of demos): carry two traps at once, one per hand, place both at the sink, then two more at the toilet.

1. `move to the mousetrap` — done: cabinet top with traps centred in head camera, base stopped. ~24 s.
2. `pick up the mousetrap from the bottom cabinet` — done: gripper closed short of fully shut, trap lifted off the top. ~31 s.
3. `pick up the mousetrap from the bottom cabinet` (second hand) — same check on the other gripper. ~31 s.
4. `move to the furniture sink` — done: sink basin fills the view, base stopped. ~24 s.
5. `place the mousetrap on the floors next to the under furniture sink` — done: trap visible on floor below or beside the sink, gripper open. ~23 s.
6. `place the mousetrap on the floors next to the under furniture sink` (second trap). ~23 s.
7. `move to the mousetrap`, then steps 2-3 again for the last two traps. ~85 s.
8. `move to the toilet` — any floor spot at least ~0.2 m from the sink works; the toilet is the trained target. ~24 s.
9. `place the mousetrap on the floors next to the under toilet` twice. ~46 s.

Total about 330 s against a 509.8 s limit.

### What the demos do differently

- Demos put the second pair at the toilet. The goal only needs them on the floor and away from the sink; the toilet just keeps them out of the `forn (2)` count.
- The duplicated place/pick segments are the two hands; a one-handed plan doubles the move steps (~4 x 24 s extra, still inside the limit).
- 4 distinct orders across 200 demos; the rare variants place on the sink top, which the goal does not want.

### Hard parts and hacks

- Trap size is 0.108 x 0.050 x 0.018 m (asset bbox, scale 1.0). The 50 mm width is just over the ~44 mm assisted-grasp span; the 18 mm height is under it. Whether a top-down grasp registers is unverified. ft40k got Q = 0.33 on instance 311 (2 of 6 literals), so at least some traps reached the floor.
- Cheap partial Q: pushing a trap off the cabinet top onto the floor scores its `ontop floor` literal (4/6 = 0.67 for all four) without a grasp. Check it lands flat and alone.
- Picking a trap back up from the floor has no trained prompt; closest: `pick up the mousetrap from the bottom cabinet`.
- Cabinet (2.09, 2.02) to sink (-2.16, 2.22) is ~4.3 m in the template; the toilet (0.47, 3.84) lies between them.
- `nextto` threshold (derived from PREDICATES §5 with asset bboxes): gap between trap and sink AABBs must be ≤ ~0.14 m, and a horizontal ray from the trap centre (1 cm above the floor) must hit sink geometry.
- `under`: the sink root sits at z 0.63 with 0.71 m height, so the basin is raised above the floor (derived, not rendered). A trap on the floor with its centre below the basin satisfies `under`. Beside a narrow pedestal it may not (PREDICATES §9).

### Hints for the VLM

- Everything is in bathroom_0; only the bathroom is loaded.
- The four traps are small flat wooden rectangles on the top of the low bottom cabinet, all at the same height.
- The furniture sink is the only sink; the toilet, bathtub and shower are distractors for "under".
- Done for the sink pair: two traps on the tiles directly below or touching the sink base.
- Done for the others: two traps on open tiles, clearly away from the sink, not on each other.
- Do not put a third trap near the sink if full success is still possible.
