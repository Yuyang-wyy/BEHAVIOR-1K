## Planner notes

**Tier:** B — two small tools go into a lidded toolbox on the garage floor, all within ~3 m. The upright pruner is an easy grasp; the flat shears are not.

### Goal in plain words

The pruner and the shears must both end inside the toolbox, the toolbox must still rest on the garage floor, and its lid must be closed.

### Q traps

- 4 literals, but `ontop toolbox floor` and `not open toolbox` are true at reset and never score. **Max partial Q = 0.5**. Each tool inside is worth 0.25, and only full success gives 1.0.
- Result on 311 (ft40k): Q = 0.00.
- Leaving the lid open, or tipping the toolbox, blocks success without costing partial Q.
- `inside` uses the AABB centre (PREDICATES §3). The pruner is 0.23 m long and the box is 0.35 m tall. Lay it down inside so the closing lid does not push it up and out.
- Close the lid last and check it is flush (5 % rule, §6). A tool handle under the lid keeps it "open".

### Minimal plan

1. `move to the toolbox` ~24 s.
2. `open the lid of the toolbox` — lid visibly up. ~56 s, the slowest skill here. It starts closed (joint_pos 0).
3. `move to the shears`, `pick up the shears from the floors` ~24 + 38 s.
4. `move to the toolbox`, `place the shears in the toolbox` ~24 + 34 s.
5. `move to the pruner`, `pick up the pruner from the floors` ~24 + 38 s.
6. `move to the toolbox`, `place the pruner in the toolbox` ~24 + 34 s.
7. `close the lid of the toolbox` — lid flush. ~38 s.

Demo mean 376 s against a 563 s limit. All objects start 0.4-7 m from the robot.

### What the demos do differently

- All 200 follow this skeleton with the shears first. The two orders on the page differ only in an extra `move to`. Tool order does not matter for the goal.
- Humans walk back to the toolbox for each tool (6 `move to` in 53 % of demos). Picking both tools and walking once saves a trip, but with two loaded hands the lid close needs a free hand.

### Hard parts and hacks

- **Pruner** (`pruner_lucqrs`, native size 0.029 × 0.067 × 0.228 m) **stands upright** on the floor in every instance: its long axis is vertical, root z 0.10. A top-down grasp across the 29 mm side fits the jaws. It has a `slicer` blade link; that is irrelevant here.
- **Shears** are forced to 0.208 × 0.08 × 0.02 m and lie flat. The only thin dimension is the 20 mm thickness, which is vertical. Top-down straddling spans 80 mm, so it needs a side pinch or a grasp through a handle loop (unverified). This is the likely failure point.
- **Toolbox** (`toolbox_redmtl`, 0.26 × 0.61 × 0.35 m) has a hinged lid. Opening it took humans ~56 s. Its yaw varies per instance, so the lid hinge side changes.
- Floor-level picks (z 0.01-0.1 m) need a deep trunk bend.

### Hints for the VLM

- house_double_floor_lower garage_0, around the car. The toolbox is a 0.6 m long box on the floor with a lid.
- The pruner stands upright like a small post, ~23 cm tall. The shears lie flat on the floor.
- Done: both tools inside the box and the lid shut flat.
