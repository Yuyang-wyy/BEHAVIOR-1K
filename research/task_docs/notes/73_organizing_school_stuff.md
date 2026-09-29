## Planner notes

**Tier:** C — five items go into a tote bag that must sit on the bed, and three of them (folder, notebook, calculator) are flat and wider than the 44 mm jaw span.

### Goal in plain words

The folder, notebook, pencil, pen and calculator must all end inside the tote, and the tote must rest on the bed. The instruction says to keep the folder and notebook "next to" the tote, but the BDDL wants all five **inside** it; the BDDL is what scores. The nightstands and floor are only start locations.

### Q traps

- 6 literals, all false at reset. Each is worth 1/6.
- Result on 311 (ft40k): Q = 0.00.
- `inside` tests each item's AABB centre against the tote's volume (PREDICATES §3). A long item poking out still counts if its centre is inside.
- `ontop tote bed` needs the tote touching the bed with the bed below its centre. If the tote tips over on the mattress, items can spill, and `inside` is lost for each one.
- Order choice:
  - **Tote on the bed first** (all demos): items then go in at bed height, ~0.5 m.
  - Filling on the floor, then lifting a loaded tote, risks spilling everything at once.

### Minimal plan

1. `move to the tote`, `pick up the tote from the floors` ~17 + 25 s.
2. `move to the bed`, `place the tote on the bed` — upright, near the bed edge closest to the items. ~17 + 22 s.
3. `move to the calculator`, `pick up the calculator from the floors` ~17 + 25 s (the demo representative took 35 s).
4. `move to the tote`, `place the calculator in the tote` ~17 + 16 s.
5. `move to the pencil`, `pick up the pencil from the bed`, `move to the tote`, `place the pencil in the tote`.
6. `move to the pen`, `pick up the pen from the floors`, `move to the tote`, `place the pen in the tote`.
7. `move to the folder`, `push the folder to the bed` — slide it until an edge overhangs the mattress edge. ~23 s. Then `pick up the folder from the bed`, `move to the tote`, `place the folder in the tote`.
8. `move to the notebook`, `push the notebook to the bed`, `pick up the notebook from the bed`, `move to the tote`, `place the notebook in the tote`.

Demo mean 486 s against a 730 s limit. All items and the tote are within ~3.3 m of the start, so walking is short; the time goes into grasps.

### What the demos do differently

- 184/200 follow exactly this order. 11/200 swap the pen and the pencil.
- "push … to the bed" is the demos' trick for flat items: shove them to the mattress edge so a finger gets under the overhang. All 200 do it for both the folder and the notebook.

### Hard parts and hacks

- Sizes (forced where `task_custom_lists` sets them):
  - pen 0.17 × 0.015 × 0.015 m and pencil 0.19 × 0.015 × 0.015 m: easy top-down grasps.
  - calculator 0.15 × 0.118 × 0.024 m, flat **on the floor**: no edge to push it over, so it needs a side pinch on 24 mm. The hardest grasp here.
  - notebook 0.15 × 0.12 × 0.027 m and folder 0.29 × 0.20 × 0.033 m, flat on the bed: use the push-to-edge trick.
  - tote 0.34 × 0.24 × 0.47 m: grasp a handle or the rim; handle width unverified.
- The folder (0.29 × 0.20 m) must enter the tote opening (0.34 × 0.24 m outer) nearly edge-on.
- Calculator has a toggle button. Touching it may switch it on; that is harmless, as it is not in the goal.
- Starts vary per instance: the pen and calculator lie on the floor anywhere in bedroom_0 (spread ~5 m), and the pencil, notebook and folder on the bed.

### Hints for the VLM

- house_single_floor bedroom_0: one double bed (2.1 × 1.8 m, mattress ~0.48 m), two nightstands, a bench and a wall TV.
- The tote is the bag standing on the floor, ~0.47 m tall.
- Pen and pencil are thin sticks, ~17-19 cm long. The calculator is a small 15 × 12 cm slab lying on the floor. The folder and notebook are flat on the bed cover.
- Done: the tote upright on the mattress with all five items below its rim.
