## Planner notes

**Tier:** C — the tomato (0.069 m) and milk carton (0.067 x 0.099 x 0.174 m) are wider than the 44 mm jaw span, they start inside a paper bag inside the car trunk, and the fridge is 9-15 m away.

### Goal in plain words

The beefsteak tomato and the milk carton must both be inside the kitchen fridge (there is only one fridge in the kitchen, so the `exists` has one choice).
The car trunk must be closed and the fridge must be closed at the end.
The paper bag itself has no goal; it can be left anywhere.

### Q traps

- 4 literals. `not open fridge` is already true at reset (fridge joint_pos [0, 0] in all 20 instances), so it never scores. Max partial Q is 0.75; full success still needs the fridge closed.
- `not open car` DOES score: the trunk starts open (joint_pos 2.531 in the template and all 20 instances). Closing the trunk alone gives Q = 0.25. zs_pt50 scored exactly 0.25 on instance 311, most likely this way.
- Close the trunk only after the bag is out, or the groceries are locked in. If the grasp on the bag fails, close the trunk anyway to bank 0.25.
- The fridge is side-by-side (`left_door` and `right_door` links). `not open` fails if either door is past 5 % of its range (PREDICATES §6). Close the door you opened and check the other was not bumped.
- `inside` needs the AABB centre in the fridge's fillable volume. Door bins are not verified to have volume (PREDICATES §16); place on a shelf (`layer_4` / `layer_5` in the demo prompts).
- The two items can be on different shelves; both just need to be inside the same fridge.

### Minimal plan

Robot starts in the garage, 1.3-4.8 m from the bag. The garage-corridor door `door_bexenl_0` starts closed; every demo opens it.

1. `move to the paper bag` — bag centred in view inside the open trunk. ~28 s.
2. `pick up the paper bag from the car` — bag lifted clear of the trunk floor. ~16 s.
3. `close the lid of the car` — trunk lid visibly down and flush. ~34 s. Scores 1/4.
4. `move to the door`, `open the door of the door` — corridor visible through the doorway. ~28 s + 23 s.
5. `move to the breakfast table`, `place the paper bag on the breakfast table` — bag standing on the table, gripper open. ~28 s + 15 s.
6. `pick up the beefsteak tomato from the paper bag` — tomato in the gripper above the bag. ~16 s.
7. `move to the fridge`, `open the door of the right_door fridge` — right door swung wide. ~28 s + 23 s.
8. `place the beefsteak tomato in the layer_5 fridge` — tomato resting on a shelf, gripper out. ~16 s.
9. `move to the paper bag`, `pick up the paper bag from the breakfast table`, `tip over the paper bag`, `pour the carton of milk into the paper bag`, `place the paper bag on the breakfast table` — carton lying on the table. ~28 + 16 + 8 + 18 + 15 s. (The demo annotators called tipping the carton out a "pour"; copy the string as is.)
10. `pick up the carton of milk from the breakfast table`, `move to the fridge`, `place the carton of milk in the layer_4 fridge`. ~16 + 28 + 16 s.
11. `close the door of the right_door fridge` — door flush with the cabinet body. ~41 s.

Budget: about 520 s against a 714 s limit. Leave the right door open between steps 7 and 11.

### What the demos do differently

- 170/200 demos follow the plan above exactly (bag out, trunk shut, door, bag on table, tomato, tip bag, milk).
- About 20 demos hand the tomato from one arm to the other (`hand over the beefsteak tomato with the left`) to free a hand for the fridge door. Keep the right arm free instead.
- Picking the carton straight out of the bag, without tipping, is not in the demos.
- The paper bag is only a carrier. A shorter plan that the goal allows: take the bag straight to the fridge and pick items from it there. No demo does that, so the prompts would be out of distribution.

### Hard parts and hacks

- Tomato: 0.069 m sphere, wider than the 44 mm grasp span. The assisted grasp will not register across it; unverified whether a tip-of-finger pinch works.
- Milk carton: smallest side 0.067 m, also wider than the span.
- Paper bag: 0.12 x 0.18 x 0.29 m, no handle link in the asset. A grasp is possible only across a bag wall.
- Fridge door handle width is unknown.
- Given the grasp limits, the reliable Q is 0.25 from the trunk. Close it early.

### Hints for the VLM

- The car is the only car, in the garage, trunk already open with the brown paper bag inside at about 0.9 m.
- The kitchen has one fridge (tall, two vertical doors), one breakfast table, four straight chairs, a dishwasher, an oven and a microwave. Do not confuse the dishwasher or oven doors with the fridge.
- Done for the trunk: lid down, no gap at the rear. Done for the fridge: both doors flush, no light visible at the seam.
- Done for an item: visible resting on a fridge shelf inside the cabinet, not on a door shelf.
