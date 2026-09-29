## Planner notes

**Tier:** D — one tool pick (the broom), then a particle-removal state change over the whole garage floor.

### Goal in plain words

- Every dust particle and every sand particle on the garage floor (`floors_nbxnpk_0`) must be gone. Two literals, 0.5 each.
- Nothing else matters: the bucket is a distractor and does not need to be used or moved.
- One particle left keeps its literal False (PREDICATES §12). Dust and sand score independently, so clearing all dust but missing one sand grain gives Q = 0.5.

### Q traps

- Particle counts per public instance: dust 8-16, sand 7-15, 18-29 in total (read from the 20 `-tro_state.json` files).
- Particles are spread over the whole garage floor, about 6.7 m x 5.4 m around the floor origin (-5.37, 5.51). The farthest particle is 4.1-7.1 m from the start pose.
- No particle lies under the car's footprint in any instance (car `car_ssxsje_0` at (-4.43, 6.89), 5.05 x 2.15 m, checked against all 445 particles). You never need to reach under the car.
- The broom removes both systems: dust "always", sand "always" by the default condition (PREDICATES §12 table). No water or toggle needed.
- The 200-per-system removal limit is far above 29, so saturation is not a risk.

### Minimal plan

1. `move to the broom` — done: broom lying on the floor centred in view, base stopped. ~14 s.
2. `pick up the broom from the floors` — done: broom lifted, gripper closed short of fully closed. ~24 s (demo mean; slowest pick of the task).
3. `move to the dirt` — ~14 s.
4. `sweep the dirt` — done: no visible dust or sand spots on the floor in a full turn of the head camera. ~95 s demo mean.
5. If spots remain, repeat `move to the dirt` then `sweep the dirt` (2/200 demos did a second pass).

Demo mean 149 s vs limit 223.7 s: ~75 s slack for one extra pass.

### What the demos do differently

- 193/200 demos use exactly the 4 steps above. 3 demos use `move to the broom` / `sweep the broom` as the sweep prompt instead.
- The trained sweep prompt here is `sweep the dirt` (199 uses), not the tool-first `sweep the broom` form that other tasks use.
- 188 of 202 sweep segments are labelled `navigation`: the humans drive the base while sweeping rather than sweeping from one spot.

### Hard parts and hacks

- Removal rule (verified in `object_states/particle_modifier.py:525-531, 983-988`): the broom has no `particleremover` meta link (asset `broom/tpyvbt` metadata lists only `base_link`), so the remover box is the **whole broom's world AABB grown by 2 cm**. No overlap or contact check applies to the broom's remover.
- Derived hack: a particle is deleted whenever it falls inside that box. Particles sit at floor level (world z ~0.0). Holding the broom low and near horizontal makes a box roughly 1.35 m long and ~0.45 m wide that reaches the floor. A code skill can drive the base in straight lanes ~0.4 m apart across the free floor with the broom held that way; no particle perception needed. Not tried in simulation.
- The boustrophedon covers about 25 m² of free floor (garage minus the car); at 0.4 m lanes that is ~60 m of base travel, likely too slow inside 224 s. Wider effective lanes need the broom held diagonal across the direction of travel. Unverified timing.
- Visual dust and sand particles are small; whether they are visible in the RGB camera at 1-2 m is unverified. Do not rely on seeing the last grain.
- Broom pick: the broom is rescaled to 1.35 x 0.45 x 0.15 m. The handle width against the 44 mm rule is unverified; 200/200 demos picked it single-armed.
- Failure mode for the VLA: sweeping one area (where the dirt is most visible) and stopping. Force at least two passes that cover the far walls.

### Hints for the VLM

- The garage is garage_0; in all 20 instances the robot starts on the garage floor (x -7.8 to -2.3, y 3.0 to 6.9). The large car occupies one side; the garage door is one wall.
- The broom lies on the floor 1.1-5.8 m from the start. The bucket (`bucket_59`) also sits on the floor; ignore it.
- Dust and sand are flat spots on the concrete floor; sand and dust are separate systems and both must go.
- Done: no spots left anywhere on the garage floor, including near walls and around the car's far side.
