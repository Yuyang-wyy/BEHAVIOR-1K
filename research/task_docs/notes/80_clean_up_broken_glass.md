## Planner notes

**Tier:** C — three floor picks carried about 10 m to one trash can, and two of the three shards have no bbox axis under 44 mm.

### Goal in plain words

All three broken-glass pieces must end inside the single trash can in the corridor. The pieces are interchangeable and any order works. The trash can may be moved. Nothing else is checked.

### Q traps

- Three literals, each worth 1/3. None is true at reset.
- `inside` tests only the shard's AABB centre against the can's fillable volume (PREDICATES §3). A shard caught on the rim does not count.
- Knocking the can over moves its volume and can spill shards already in it. Every literal is read at the final step only.
- The can (`trash_can/cjmezk`) has a single link, so no lid to open (asset metadata).

### Minimal plan

1. `move to the broken glass` — a shard on the floor in view. ~31 s.
2. `pick up the broken glass from the floors` — shard off the floor, gripper stopped short of closed. ~28 s.
3. `move to the broken glass` then `pick up the broken glass from the floors` with the other hand — second shard held. ~31 s + 28 s.
4. `move to the trash can` — can in view at close range. ~31 s.
5. `place the broken glass in the trash can` twice — shards no longer visible in either gripper and not on the rim. ~17 s each.
6. `move to the broken glass`, `pick up the broken glass from the floors`, `move to the trash can`, `place the broken glass in the trash can` — third shard. ~107 s.

Budget: 435 s limit vs 290 s demo mean. The plan above is the demo plan (90% of demos), and the walk dominates.

### What the demos do differently

- 90% of demos use exactly this order: two shards, one trip, then the third.
- No demo moves the trash can closer.

### Hard parts and hacks

- Grasp: shard `rvpgpt` (2 of the 3 pieces) has asset bbox 0.051 x 0.122 x 0.047 m; `beltgg` is 0.066 x 0.066 x 0.044 m. No axis of `rvpgpt` is under 44 mm. The real shard may be thinner than its bbox, but that is not verified. Expect grasp retries.
- The shards lie flat on the floor (z 0.01-0.02), so each pick needs a full trunk bend.
- Distances: shards spread over the whole dining room (0.25-10 m from the start); the can stands in corridor_0, 2.8-12.2 m from the start.
- Hack (unverified): the can is 0.38 m wide with no handle, so carrying it to the shards is unlikely to work. Carry two shards per trip instead, as the demos do.
- The dining room is cluttered: 8 benches, 4 booths, 7 chairs and 6 stools. Small flat shards are easy to lose behind furniture legs.

### Hints for the VLM

- Scene restaurant_diner. The shards are small glass pieces on the dining-room floor. There is only one trash can in dining_room_0 and corridor_0 together, standing on the corridor floor.
- The shards are 5-12 cm pieces lying flat on the floor; their rendered appearance was not checked.
- Done per literal: shard not visible on the floor and not on the rim, seen inside the can from above.
