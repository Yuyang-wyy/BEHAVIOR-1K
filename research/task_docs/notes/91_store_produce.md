## Planner notes

**Tier:** C. It is plain pick-and-place, but every fruit is wider than the ~44 mm jaw span: mango 0.119 x 0.100 x 0.088 m, pomegranate 0.080 x 0.080 x 0.089 m (asset bbox, scale 1). A fridge door also has to be opened.

### Goal in plain words

- All four fruits (2 mangoes and 2 pomegranates) must end inside **one** of the two kitchen fridges (`fridge_jtqazu_0` or `fridge_jtqazu_1`, the same model). Either fridge works, but all four must go in the same one.
- The goal has no `not open` literal, so the fridge door may stay open.
- The freezer in the same kitchen is not a valid target.

### Q traps

- There are 4 literals and all score (0/4 true at reset). Each fruit is worth 0.25.
- Q is the max over the 2 fridge options. Fruit split 2+2 across both fridges gives only 0.5. Pick one fridge and stay with it.
- Both fridges start closed (`joint_pos` 0 in all 20 instances), so the door must be opened.
- `inside` needs the fruit's AABB centre in the fridge volume (PREDICATES §3). Fruit left on the open door or in a door bin may not count, because door-bin volumes are unverified. Put the fruit on an interior shelf.
- Closing the door earns nothing. It can push a fruit back out, so skip it.

### Minimal plan

1. `move to the wicker basket`. Done when the basket on the floor is centred and the base has stopped. About 18 s.
2. `pick up the wicker basket from the floors`. Done when the basket is off the floor and in the gripper. About 15 s.
3. `move to the commercial kitchen table`. About 18 s.
4. `pour the mango and mango and pomegranate and pomegranate into the wicker basket`. This is the demo's wording for tipping the basket out onto the table. Done when four fruits are visible on the table top. About 19 s.
5. `place the wicker basket on the floors`. About 25 s. This frees both hands.
6. `move to the fridge`. Done when a fridge door is in front at arm's reach. About 18 s.
7. `open the door of the fridge`. Done when the door is visibly swung open and the shelves can be seen. About 32 s.
8. `move to the commercial kitchen table`. About 18 s.
9. `pick up the mango from the commercial kitchen table`. About 15 s.
10. `pick up the pomegranate from the commercial kitchen table` (other hand). About 15 s.
11. `move to the fridge`. About 18 s.
12. `place the pomegranate in the fridge`. Done when the fruit is resting on a shelf inside. About 6 s.
13. `place the mango in the fridge`. About 6 s.
14. Repeat steps 8-13 for the second mango and pomegranate. The demos use `place the pomegranate in the fridge next to the pomegranate` and `place the mango in the fridge next to the mango` here.

- Totals: about 300 s without the door close, against a 476.1 s limit.

### What the demos do differently

- 197 of 200 demos end with `close the door of the fridge` (about 19 s). The goal does not need it. Leave the door open.
- They pour the basket onto a commercial kitchen table before picking. The goal does not need this either, but it lifts the fruit from floor height (z ~0.08 m in the basket) to table height. It also matches the trained prompts: there is no demo prompt for picking fruit out of the basket.
- They carry two fruits per trip, one per hand.

### Hard parts and hacks

- **Grasp span.** No fruit dimension is under 44 mm. The demos did grasp them, but whether the assisted grasp registers them at eval is unverified. Expect slips, and check that the fingers stopped short of fully closed after each pick.
- **Round fruit rolls.** A poured mango or pomegranate can roll off the table. Re-locate all four before the fridge trips.
- **Unverified hack:** carry the whole basket (0.39 x 0.41 x 0.43 m) into the open fridge with the fruit still inside. The fruit centres would then be in the fridge volume. Whether the basket fits on a shelf, and whether it can be carried that high without tipping the robot, are both unverified.
- The basket and the fruit start anywhere in the kitchen (spread ~7.8 m). The distance to the nearer fridge also varies (1.35-7.5 m). Choose the fridge nearest the table you pour onto.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The scene is a restaurant kitchen. There are two identical tall fridges (model jtqazu, ~0.9 x 1.1 x 2.1 m), which have a glass link per the asset metadata. A separate freezer is a distractor.
- The wicker basket stands on the floor. The fruit inside is roughly 8-12 cm across.
- Done for each literal: the fruit is visible on a fridge shelf behind the door line, and none is left on the table, on the floor or in the basket.
