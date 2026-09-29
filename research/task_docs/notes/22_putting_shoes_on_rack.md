## Planner notes

**Tier:** B — four shoes go from the corridor floor onto one hall tree in the same corridor, short moves. No shoe dimension is under the 44 mm span across the body (gym shoes 0.31 x 0.11 x 0.14 m, sandals 0.26 x 0.11 x 0.12 m); the grasp must go on a rim, heel or strap (unverified).

### Goal in plain words

Both sandals and both gym shoes must touch the hall tree `hall_tree_daxzaw_0` and must not touch the corridor floor.
The two gym shoes must be next to each other, and the two sandals must be next to each other.
Shoes of the same kind are interchangeable within the pair; any shelf or hook of that hall tree works.

### Q traps

- The four `not touching <shoe> floor` literals start False: `:init` puts every shoe `ontop` the floor, and `ontop` requires contact (PREDICATES §4); the instances confirm the shoes rest on the floor (z 0.04-0.05). All 10 literals can score, so max partial Q is 1.0.
- Consequence: lifting a shoe off the floor scores 1/10 at once, even while it is still held. zs_pt50's 0.5 on instance 311 fits this.
- `nextto` between shoes of a pair needs an AABB gap under ~6-8 cm (L/6 = 0.058-0.081 m across instances, PREDICATES §5). Two shoes on the same shelf, placed side by side, pass. Shoes on different shelves at different heights fail. Both pairs are far apart at reset in all 20 instances (nearest 0.20 m in 301 and 312).
- A shoe resting partly on the floor, or leaning on the hall tree with the toe on the floor, fails `not touching floor` (PREDICATES §8).
- The corridor has two hall trees. The goal names `hall_tree_daxzaw_0` (at about x -1.19, y -0.21); the other, `hall_tree_upkvgr_0`, is 5.6 m further along the corridor. Shoes on the wrong one score only the `not touching floor` literals.
- `touching` is instantaneous contact. A shoe hovering a few mm over a shelf, or jittering, can flicker off.

### Minimal plan

Everything is in corridor_0; shoes are 0.7-6.7 m from the start, the hall tree 1.5-6.8 m.

1. `move to the sandal`, `pick up the sandal from the floors` — sandal off the floor (scores 1/10). ~19 s + 20 s.
2. `move to the sandal`, `pick up the sandal from the floors` with the other hand. ~19 s + 20 s. (The demos mix one sandal and one gym shoe per trip; carrying a matched pair makes the `nextto` placement easier.)
3. `move to the hall tree`. ~19 s.
4. `place the sandal in the high_level hall tree` twice, the second right beside the first on the same shelf. ~14 s each.
5. Repeat 1-4 for the gym shoes with `move to the gym shoe`, `pick up the gym shoe from the floors`, `place the gym shoe in the high_level hall tree`.

Done-check per shoe: shoe resting on the hall tree shelf, no part on the floor, gripper open. Done for a pair: the two shoes side by side with a gap under ~5 cm.
Budget: about 230 s against a 386 s limit.

### What the demos do differently

- Demos carry one sandal and one gym shoe per trip in about half the orders; many orders appear (top sequence only 6/200).
- Every demo uses the prompt `place the ... in the high_level hall tree`, i.e. the upper shelf.
- A few demos re-pick a shoe from the hall tree to fix its placement.

### Hard parts and hacks

- Grasp: no shoe body fits the 44 mm span. A gym shoe's collar/heel counter or a sandal strap is the likely grasp target; unverified that the assisted grasp registers there.
- Placing on a high shelf: the robot must reach up with a load; keep the base close to avoid tipping.
- The `nextto` pairs are the literals most likely to be lost. Place the second shoe of a pair directly against the first.
- Cheapest partial Q: lift and hold shoes. Each shoe off the floor is 1/10 even if never placed.

### Hints for the VLM

- The corridor is a long narrow hall (2.6 x 9 m) with two hall trees, a standing mirror and four doors. The target `hall_tree_daxzaw_0` stands at about (x -1.19, y -0.21), 1.5-6.8 m from the start; the other hall tree (different model) is 5.6 m along the corridor. Which looks like which is unverified; identify it at reset.
- Gym shoes are sneakers (two different models); sandals are open shoes (two different models).
- Done: four shoes on the target hall tree, sandals together, gym shoes together, corridor floor clear.
