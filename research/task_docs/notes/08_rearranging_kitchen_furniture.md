## Planner notes

**Tier:** C. Three countertop appliances must go into a wall-mounted top cabinet (root z 1.89 m) behind two hinged doors, then both doors must be shut.

### Goal in plain words

- Toaster, food processor and French press must all end inside the same cabinet.
- Either of the two top cabinets counts (`exists`, 2 ground options). They are the only cabinets in the kitchen (template init_info: 2 `top_cabinet`, no bottom cabinets).
- That cabinet must be closed at the end: both its doors within 5 % of closed (PREDICATES.md §6).
- Splitting items across the two cabinets scores only the items in the better one.

### Q traps

- 4 literals. `not open cabinet` is true at reset (both joints ~0 in the template and all 20 instances), so it never scores. Max partial Q = 0.75.
- Full success needs the doors closed; closing earns no partial Q but is the only route to 1.0.
- Open both doors of one cabinet only. Opening the other cabinet adds nothing.
- Closing a door onto an item can push its centre out of the volume (§3). Push items well back before closing.
- ft40k scored Q=0.5 on 311 (2 of 3 inside), so the top cabinet volume works.
- Each cabinet has 2 joints; any door left ajar breaks success.

### Minimal plan

1. `move to the top cabinet`. Done: base stopped below the cabinet, doors in view. ~10 s.
2. `open the door of the right_door top cabinet`. Done: right door swung clearly open. ~39 s.
3. `open the door of the left_door top cabinet`. ~39 s.
4. `move to the toaster`. ~10 s.
5. `pick up the toaster from the bar`. Done: gripper closed short of full, toaster lifted off the bar. ~15 s.
6. `move to the top cabinet`. ~10 s.
7. `place the toaster in the low_level top cabinet`. Done: gripper open, toaster on the lower shelf, arm withdrawn. ~18 s.
8. `move to the food processor`; `pick up the food processor from the bar`; `move to the top cabinet`; `place the food processor in the low_level top cabinet next to the right toaster`. ~50 s.
9. `move to the french press`; `pick up the french press from the bar`; `move to the top cabinet`; `place the french press in the low_level top cabinet next to the right food processor`. ~50 s.
10. `close the door of the right_door top cabinet`. Done: door flush with the frame in RGB/depth. ~18 s.
11. `close the door of the left_door top cabinet`. ~18 s.

Budget: human mean 298 s, limit 447 s. Door opening (~39 s each) is the costliest step.

### What the demos do differently

- 199/200 demos use `top_cabinet_tynnnw_1` (cabinet.n.01_2, y ~0.83); one used both. The goal accepts either one.
- 132 `turn to` segments across the 200 demos (`turn to the food processor` 72, `turn to the french press` 58) to reorient the item in hand. Only needed if the item will not fit through the doors.
- The "next to" placements are wording only; `nextto` is not in the goal.
- Some demos open the left door first. Order does not matter.

### Hard parts and hacks

- Height: the cabinet shelf is above shoulder level. Carrying an appliance extended high risks tipping the robot (robot fact).
- Grasp: object widths are unknown (no custom list). Humans pick all three directly from the bar with no push-to-edge. The French press likely has a handle (unverified). ft40k got two items in, so at least two are graspable in practice.
- Door opening needs the handle; handle width is unverified against the 44 mm limit.
- Placement depth: releasing on the shelf lip leaves the centre outside the volume or blocks the door.
- The French press position varies most (spread 1.95 m; x from ~5.8 to ~7.7 along the bar in instances). The toaster and food processor stay within ~0.35 m.
- Closing is push-only (§6), so a scripted close (push each door flat) is legal and cheap.

### Hints for the VLM

- Everything is in `kitchen_0`. The "countertop" is a bar (`bar_byvbuc_0`); a second bar exists in the kitchen as a distractor.
- The two top cabinets are identical models (tynnnw) side by side on the wall, ~1.2 m apart. Pick one and use it for all three items.
- Toaster, food processor and French press are the only instances of their categories in the scene.
- Other appliances nearby (microwave, oven, fridge, dishwasher) are not targets.
- Done looks like: bar empty of the three items, all three visible on the chosen cabinet's shelf, then both doors of that cabinet flush.
