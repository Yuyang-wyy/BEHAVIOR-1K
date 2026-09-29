## Planner notes

**Tier:** B — three soda cans into one open-top trash can, all on the floor. No doors, no state changes.

### Goal in plain words

All three cans of soda must end with their AABB centres inside the trash can's volume. The cans are interchangeable. There is exactly one trash can (kitchen) and it is the only valid container. The goal has no room literal, so the trash can may be carried into the living room and left there. Nothing must be closed or put back.

### Q traps

- 3 literals, none true at start (cans on the living-room floor, trash can in the kitchen in all 20 instances). Max Q = 1.0.
- Success is checked every step. The episode ends the moment the third can is inside, so the demo's final `place the trash can on the floors` is never needed.
- Partial Q reads only the final state. Tipping the trash can (held or on the floor) can spill cans already scored.
- A can resting on the rim is not inside (centre test, PREDICATES §3). Re-check after each release.
- A held trash can still counts as the container. Cans inside a held, upright bin score.

### Minimal plan

Demo order (100% of 200 demos). It is also the order zs_pt50 used to succeed on 311 (Q 1.0, 5493 of 7901 steps).

1. `move to the trash can` — base stopped, bin centred in the head camera. ~14 s.
2. `pick up the trash can from the floors` — bin lifted clear of the floor in one gripper, upright. ~16 s.
3. `move to the can of soda` — a can visible near the free gripper. ~14 s.
4. `pick up the can of soda from the floors` — can off the floor in the free gripper. ~16 s.
5. `place the can of soda in the trash can` — can no longer in the gripper; depth shows it below the bin rim. ~8 s.
6. Repeat 3-5 for the other two cans. ~2 x 38 s.
7. Skip `place the trash can on the floors` unless the episode is still running; if used, keep the bin upright. ~12 s.

Budget ~155 s against a 263 s limit (7901 steps).

Alternative if carrying the bin fails: leave it on the kitchen floor and ferry cans. Can-to-bin distance is 1.7-6.5 m (median ~3.4 m) across instances, so three single-can trips roughly double travel. Carrying one can per hand halves it.

### What the demos do differently

- Every demo picks up the trash can first and carries it to the cans (200/200). The goal does not need this, but it is the in-distribution order and saves trips.
- Every demo ends by putting the bin down (198/200). Not needed.
- 5 demos contain `place the can of soda in the floors` and 4 contain `pick up the can of soda from the trash can`: recovery from a miss. Do not send these.

### Hard parts and hacks

- Can size: 75 x 75 x 135 mm (itolcg) and 76 x 76 x 127 mm (lugwcz), upright on the floor (z 0.06-0.07), from asset metadata bbox_size at scale 1.0. No dimension fits the 44 mm assisted-grasp span. Yet zs_pt50 binned all three on 311, so the cans can be held; how (friction without assisted-grasp registration) is unverified.
- Trash can wkxtxh: 230 x 230 x 279 mm body. It is grasped by the rim wall in the demos; rim thickness is unverified.
- Floor pickups need a low trunk pose. A knocked-over can rolls; re-locate it before re-grasping.
- Cans are spread up to 3.9 m apart in the living room. Plan the visiting order by nearest can.
- Closed-loop on 311: zs_pt50 1.0, ft24k 0.67, pt0 0.67, ft40k 0.0, ft10k 0.0. The zero-shot checkpoint beats the fine-tunes here; one rollout each, so treat as weak evidence.

### Hints for the VLM

- Cans of soda: small upright cylinders on the living-room floor, 3 of them (two itolcg, one lugwcz, different labels). No other cans in the loaded rooms.
- Trash can: one ~23 cm wide, ~28 cm tall open bin on the kitchen floor. Its position moves up to 6.3 m between instances; search the kitchen floor first.
- The robot starts in the kitchen (BDDL `ontop agent floor_2`; not checked against instance robot poses).
- Done per can: the can is not in the gripper, not on the floor, and not visible above the rim; depth inside the bin shows it.
- Done overall: episode ends by itself on success. If it has not, count cans on the floor.
