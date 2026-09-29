## Planner notes

**Tier:** C — the eggs are ~15 cm wide, far past the 44 mm grasp span, and the basket can be up to 44 m from the start; long outdoor navigation with no global pose.

### Goal in plain words

- All three Easter eggs must be out of the wicker basket and resting on the main lawn (`lawn_aztwla_0`).
- All three must be `nextto` the **same** tree; any of the 26 garden trees works.
- The eggs are interchangeable. The basket can go anywhere; its position is not checked.
- Eggs on a paver, the driveway, or one of the three other lawn patches (`lawn_srfikq_0`, `lawn_tiqndr_0`, `lawn_zjtrpt_0`) do not count as `ontop lawn.n.01_1`.

### Q traps

- 9 literals in the best option: 3 `nextto tree`, 3 `not inside basket`, 3 `ontop lawn`. None is true at reset, so all nine score.
- `not inside basket` is the cheapest: any egg out of the basket volume scores it, even if held (PREDICATES §3).
- An egg lying out of the basket on the lawn scores 2 of its 3 literals anywhere. That is 6/9 = 0.67 with no tree at all.
- An egg resting on the basket, on another egg or against a root/bush it sits on does not touch the lawn, so `ontop` fails.
- Splitting eggs between two trees loses the `nextto` literals of the minority tree; pick one tree and stick to it.

### Minimal plan

Most common demo order (53%): carry the basket to a tree, then shuttle the eggs.

1. `move to the wicker basket` — done: basket centred in view, base stopped. Budget 28 s mean, but up to ~80 s on far instances.
2. `pick up the wicker basket from the lawn` — done: basket lifted, gripper stopped on the handle. ~21 s.
3. `move to the tree` — pick the nearest tree; one is always 0.8-5.6 m from the basket across the 20 public instances. ~28 s.
4. `place the wicker basket on the lawn` — done: basket upright on grass beside the trunk. ~10 s.
5. `pick up the easter egg from the wicker basket` — done: egg above the rim. ~21 s.
6. `place the easter egg on the lawn next to the in_front_of tree` — done: egg on grass close to the trunk, gripper open. ~19 s.
7. Repeat 5-6 twice (use `move to the wicker basket` if the base must reposition). ~80 s.

Roughly 230 s plus navigation against a 381 s limit. On far instances the drive dominates.

### What the demos do differently

- 26 distinct skill orders. 45% leave the basket in place and walk each egg to the tree instead of carrying the basket; that costs extra walking.
- Two demos put the basket "on the tree"; irrelevant to the goal.
- Humans pick the tree nearest the basket. Copy that.

### Hard parts and hacks

- Egg size: asset bbox 0.057 x 0.043 x 0.043 m times instance scale (2.73, 3.37, 3.00) gives about 0.16 x 0.14 x 0.13 m. No dimension is under 44 mm, so a normal assisted grasp should not register. Yet zs_pt50 reached full success on instance 311 (n=1); how it moved the eggs is unverified.
- Basket is 0.39 x 0.41 x 0.43 m (scale 1.0); the demos grasp it, presumably by the handle (handle width unverified).
- Hack worth testing (unverified): carry the basket next to a trunk and tip it (`tip over the <obj>` exists in the vocabulary, but no demo in this task uses it; no trained prompt here). Spilled eggs that roll onto the lawn near the trunk could score all nine literals without any egg grasp.
- `nextto` on a tree (PREDICATES §5): the tree AABB includes the canopy, so an egg under the canopy has AABB gap 0. The binding test is the ray check: one of the egg's 16 horizontal rays, cast at ~7 cm height, must hit tree geometry within 5 m. At that height only the trunk exists, and rays are 22.5° apart. Place eggs within a few tens of cm of the trunk. Trunk width is unverified.
- Robot start to basket: 3.6-44 m (median ~15 m) over the public instances; the basket position changes per instance (spread 47 m), trees are fixed.
- Eggs are round and may roll after release; re-check they rest on grass.

### Hints for the VLM

- Everything happens outdoors in garden_0; the robot starts on the lawn.
- The wicker basket is a brown woven basket, about knee height, sitting on grass with the three large eggs inside.
- Trees: 26 in the garden, five models. Any trunk works; bushes (many `bush_*` objects), garden lights, fence posts and the swing set are not trees.
- Stay on grass: avoid the pavers, driveway and playground surface near the house.
- Done per egg: egg lying on grass, touching or within a hand's width of the trunk, basket no longer around it.
- Done overall: three eggs clustered at one trunk, basket empty.
