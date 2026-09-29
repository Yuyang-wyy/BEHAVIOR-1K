## Planner notes

**Tier:** C — pure container-in-container placement: fruit into tupperware, tupperware into fridge. Despite the name, nothing has to freeze, but the fruit is wider than the jaws.

### Goal in plain words

Each tupperware must hold one apple and one strawberry, with a different apple and a different strawberry in each (`forpairs`, 4 ground options). Both tupperwares must be inside the fridge `fridge_dszchb_0`, and the fridge must be closed. **There is no `frozen` literal**, so there is no waiting after closing the door. **Containers:** the two tupperwares from the bottom cabinet `bottom_cabinet_no_top_gjeoer_0`. The bowl, the tray and the cabinet doors are not in the goal.

### Q traps

- 7 literals. `not open fridge` is true at start (joint 0.0 in all 20 instances), so it never scores. Max partial Q is 6/7 = 0.857 (page is right).
- **Split the fruit.** Both apples in the same tupperware satisfy only one `inside apple tupperware` literal of the best option, and the same holds for the strawberries. A full pair needs one of each per box.
- `inside` tests only the AABB centre (§3). A strawberry resting on top of an apple can poke above the rim and still count, as long as its centre is below the rim's volume top. Check it.
- Close the fridge last, and check afterwards that the door did not bounce open on a tupperware edge (§6).
- Leaving the cabinet open costs nothing. The cabinet is not in the goal, and one of its joints reads 0.0035 at start in some instances anyway.

### Minimal plan

1. `move to the bottom cabinet no top`, `open the door of the bottom cabinet no top`, `pick up the tupperware from the bottom cabinet no top` — ~14 + 24 + 10 s.
2. `place the tupperware on the countertop` — box upright near the bowl and tray. ~10 s.
3. Repeat step 1 (another door may be needed), then `place the tupperware on the countertop` again. Skip `close the door of the bottom cabinet no top` (not in the goal, ~15 s each).
4. `move to the apple`, `pick up the apple from the bowl`, then `move to the tupperware`, `place the apple in the tupperware` — ~14 + 10 + 14 + 7 s. Repeat for the second apple, into the **other** tupperware.
5. `move to the strawberry`, `pick up the strawberry from the tray`, `move to the tupperware`, `place the strawberry in the tupperware` — same timings. Repeat into the other tupperware.
6. `move to the electric refrigerator`, `open the door of the electric refrigerator` — ~14 + 24 s.
7. `pick up the tupperware from the countertop`, `place the tupperware in the electric refrigerator` — ~10 + 7 s. Do it once per tupperware. Carrying both at once (one per hand) saves a trip.
8. `close the door of the electric refrigerator` — door flush. ~15 s. Success.

The plan takes about 330 s against a 631 s limit. Picking two fruits (one per hand) per trip, as the demos do, saves about 40 s.

### What the demos do differently

- Two-handed batching: `pick up the apple from the bowl` twice, then `place the apple in the tupperware` twice.
- 199 of 200 demos park one loaded tupperware on the breakfast bar (`place the tupperware on the bar`) to free a hand for the fridge door, and fetch it again afterwards (`pick up the tupperware from the bar`). This is a staging step, not a goal need.
- They close the cabinet after each tupperware. That is not needed.
- In this task the fridge is called `electric refrigerator`, not `fridge`. Keep that wording.

### Hard parts and hacks

- **Grasp span.** Apples are 86-87 x 74 x 74 mm, and strawberries are forced to 60 x 50 x 50 mm (`task_custom_lists.json`). Both exceed the 44 mm span on every axis, so a clean grasp is unlikely. The ft40k checkpoint scored 0 on instance 311. Without fruit, the reachable Q is 2/7 ≈ 0.29, from the two tupperwares in the fridge.
- **Pour hack** (untested): pick the bowl by its rim (306 mm bowl) and tip the apples into a tupperware. Put the two tupperwares side by side first, so an apple landing in each is at least possible. There is no trained prompt; closest: `pour the ... into the ...` from other tasks. The strawberries sit on a flat 200 x 250 x 20 mm tray, which can hardly be picked.
- **Tupperware** (`mkstwr`, 219 x 219 x 136 mm, no lid in the scene) is held by the rim wall. Wall thickness is not verified. The boxes sit on a low cabinet shelf at z ≈ 0.56.

### Hints for the VLM

- Kitchen of `house_single_floor`. The tupperwares are in the long low cabinet under the counter along the x ≈ 4.1 wall, under the burner and microwave. The bowl of apples and the tray of strawberries are on `countertop_kelzer_0` along the sink wall. The fridge is at the right end of that wall (7.8, -2.0). The breakfast bar with stools is at (7.3, 0.2).
- Two red apples in a large bowl, two strawberries on a small tray. Each is the only fruit of its kind.
- Done: two boxes on fridge shelves, each visibly holding one apple and one strawberry, door flush.
