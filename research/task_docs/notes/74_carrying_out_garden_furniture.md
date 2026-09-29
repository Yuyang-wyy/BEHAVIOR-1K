## Planner notes

**Tier:** C — two large pieces of furniture (a chair 0.74 × 1.05 × 0.81 m and a wheelbarrow 1.58 × 0.76 × 0.67 m) must be moved ~10-15 m out through a sliding door.

### Goal in plain words

- The garden chair must end resting on the garden floor object `floors_pyoemr_0`, the paved area around the pool.
- The wheelbarrow must end resting on the lawn (`lawn_wwoqjw_0`).
- Both start on the living_room_0 floor.
- The sliding door is not in the goal.

### Q traps

- 2 literals, both false at reset. Each is worth 0.5.
- Result on 311 (ft40k): Q = 0.00.
- **Surface identity matters** (PREDICATES §4): `ontop` needs contact with that exact object.
  - The chair on grass, or the wheelbarrow on paving, scores 0.
  - Both surfaces are 0.28 m slabs with their tops at the same height, and their bounding boxes overlap in plan. Tell them apart by look (paving vs grass), not by height.
- The pool (`swimming_pool_vnvmkx_0`) is sunken (root z -0.96). A chair that falls in touches the pool, not the floor, and scores 0.
- The wheelbarrow rests on its wheel and legs. All of them should touch the lawn, and its centre must be over the lawn.

### Minimal plan

1. `move to the slide door` ~28 s (trained string; the demos write "slide door").
2. `open the door of the slide door` — the 4.2 m sliding door `sliding_door_lrvyvc_0` (x 12.3, y 4.12) is visibly open. It starts closed (joint_pos 0). ~28 s.
3. `move to the garden chair`, `pick up the garden chair from the floors` ~53 + 14 s. Alternative: `push the garden chair to the floors` (51 demos).
4. `move to the pool` — carry it out to the paving beside the pool. ~53 s.
5. `place the garden chair on the floors next to the pool` — chair upright on paving, not on grass, not over the pool edge. ~7 s.
6. `move to the wheelbarrow`, `pick up the wheelbarrow from the floors` ~53 + 14 s. Alternative: `push the wheelbarrow to the floors`.
7. `move to the lawn` — the demo representative took 122 s here. ~53-120 s.
8. `place the wheelbarrow on the lawn` — all wheels/legs on grass. ~9 s.

Demo mean 369 s against a 553 s limit. Base travel in the demos is 61 m.

### What the demos do differently

- 80/200 follow the plan above as written. Others insert a `push … to the floors` before the pick (51 chair and 43 wheelbarrow push segments across the demos) or a `turn to the wheelbarrow`.
- 14/200 push the chair before opening the door.
- The demos log 184 `move to the slide door` segments; the door is usually approached separately from the chair.

### Hard parts and hacks

- **Size and weight:** both objects are far larger than the gripper. A grasp must use a thin frame member of the chair or the wheelbarrow's handle; widths are unverified. Carrying a 1.6 m wheelbarrow extended can tip the robot (robot facts).
- **Pushing is a real option:** the wheelbarrow has a wheel joint, and the demos push each object part of the way in roughly a quarter of episodes. A base push through the 4.2 m doorway is plausible, but it is not verified that pushing works over the door threshold.
- Starts: the chair and wheelbarrow each move up to ~8 m between instances, but always inside living_room_0 (x 9.7-17.1, y -0.3 to 3.3). The door is at y 4.12, the garden side.
- The lawn object spans 53 × 59 m. Where the grass is actually exposed near the house is not verified; follow the demo `move to the lawn` and check for grass under the wheels.

### Hints for the VLM

- house_single_floor living_room_0 has a 4.2 m sliding door to the garden. The pool lies ~5 m beyond it (pool AABB starts at y ≈ 9.6).
- The garden chair is the outdoor chair standing on the living-room floor. The wheelbarrow is the barrow with a wheel, also on the living-room floor.
- Done: the chair standing on paving near the pool, and the wheelbarrow standing on grass.
