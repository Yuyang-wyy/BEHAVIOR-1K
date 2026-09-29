## Planner notes

**Tier:** D — freeze two pies in the fridge, after four container moves: pie into tupperware, tupperware into fridge. The pies are too wide for the jaws.

### Goal in plain words

- Each apple pie must be inside its own tupperware, and it does not matter which pie goes in which (`forpairs`, 2 ground options).
- Both tupperwares must be inside the fridge `fridge_dszchb_0`.
- Both pies must be `frozen` at the final step, meaning their **current** temperature is at most 0 °C. This is not latched (§16).
- The fridge must be closed.

**Cold source:** the fridge only (-18 °C, rate 0.1, needs closed + Inside; T_ss ≈ -11.2 °C). **Containers:** the two tupperwares from the bottom cabinet. The plates and the cabinet doors are not in the goal.

### Q traps

- 7 literals. `not open fridge` is true at start, so it never scores. Max partial Q is 6/7 = 0.857 (page is right).
- **Frozen needs the door shut.** The fridge cools only while it is closed within 5 % (§2, §6). An open door means no cooling. A pie taken out, or a door left ajar, warms back above 0 °C within about 20 s (§16).
- Pies start at 1.3 °C in all 20 instances, so they are not frozen at reset. By the time they are loaded they will have warmed toward 23 °C. From there, freezing takes about 9 s with the door closed (§16). Success fires on the first step when everything holds, so after closing the fridge just wait about 10-15 s.
- `inside pie tupperware` checks only the pie's AABB centre in the tupperware volume (§3). A pie resting tilted on the rim does not count.
- Cold reaches a pie in a tupperware as long as the pie's own centre is inside the fridge volume (§2). Door bins are not verified to have volume, so use the shelves.

### Minimal plan

This order loads the empty tupperwares into the fridge first, then the pies straight into them. It avoids carrying a loaded tupperware. The order is derived, not demo order.

1. `move to the bottom cabinet no top`, then `open the door of the second_right_door bottom cabinet no top` (the door name varies: `first_left_door`, `second_left_door`, `second_right_door` or `first_right_door`) — the tupperware is visible on a shelf. ~11 s + ~32 s.
2. `pick up the tupperware from the high_level bottom cabinet no top` — ~18 s. Leave the cabinet door open, since it is not in the goal (saves ~17 s per door).
3. Repeat steps 1-2 for the second tupperware, with the other hand. It may be behind another door.
4. `move to the fridge`, `open the door of the fridge` — ~11 s + ~32 s.
5. `place the tupperware in the middle_level fridge`, then `place the tupperware in the high_level fridge` — both on shelves, open side up. ~9 s each.
6. `move to the plate`, `pick up the apple pie from the plate` — ~11 s + ~18 s. Pick the second pie with the other hand.
7. `move to the fridge`, `place the apple pie in the tupperware` twice — each pie flat inside a tupperware. ~9 s each. Closest trained prompt: the demo places pies into tupperwares on the countertop.
8. `close the door of the fridge` — door flush. ~17 s. Wait about 15 s for the pies to freeze.

The plan takes about 280 s against a 623 s limit. Demo order also works: pies into tupperwares on the countertop, then `pick up the tupperware from the countertop` and `place the tupperware in the high_level fridge`.

### What the demos do differently

- They open and **close** the cabinet door for each tupperware (~30 s each round). Closing is not needed.
- They set the tupperwares on the countertop, load the pies there, then carry the loaded tupperwares to the fridge.
- Which cabinet door hides a tupperware varies by instance. The demos name all four doors about equally often.

### Hard parts and hacks

- **Pie grasp.** Each pie is 173 x 171 x 37 mm and lies flat on a plate. The 37 mm thickness can only be straddled from the side, which a top-down grasp cannot do. The pie is realistically not graspable. Without it, the best reachable Q is the two `tupperware in fridge` literals, 2/7 ≈ 0.29.
- **Tupperware** (`mkstwr`, scaled here to 250 x 250 x 100 mm) is an open box. A grasp must close on its thin wall at the rim (wall thickness not verified). Tupperwares sit on cabinet shelves at z 0.19-0.63, so this is a low reach.
- The fridge is single-door (`dszchb`, one joint) and starts closed in every instance. The cabinet `gjeoer` has 4 doors, all closed at start.
- Keep the tupperwares level. A pie in a tilted tupperware slides out.

### Hints for the VLM

- Kitchen of `house_single_floor`. The pies are on two plates on `countertop_kelzer_0` along the sink wall. The fridge is at the right end of that wall (7.8, -2.0). The tupperwares are in the long low cabinet `bottom_cabinet_no_top_gjeoer_0` under the counter along the x ≈ 4.1 wall. That is the one with the burner and microwave on top, not the sink wall.
- A tupperware is a clear or white square box without a lid. Two are in the scene.
- Done: two pies in two tupperwares on fridge shelves, door flush, about 15 s elapsed. The episode ends by itself on success.
