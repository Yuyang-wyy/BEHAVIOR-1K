## Planner notes

**Tier:** B. This is two small pick-and-place moves into a floor bin. The half banana is 42 mm thick, just inside the ~44 mm jaw span. The half pomegranate is 76-93 mm on every axis, so a registered assisted grasp on it is doubtful.

### Goal in plain words

- Both food halves must end inside the kitchen trash can (`trash_can_66`, model ifzxzj), which stands on the kitchen floor.
- There are no other goal literals. Nothing needs closing, and the bin may stay where it is.
- The kitchen also has a `public_trash_can`. Food put in it earns nothing.

### Q traps

- There are 2 literals and both score (0/2 true at reset). Each one is worth 0.5.
- `inside` tests only the food's AABB centre against the bin's volume (PREDICATES §3). A half that lands on the rim or the lid does not count.
- The bin is 0.31 x 0.40 x 0.80 m (asset bbox, scale 1). A tipped bin loses anything already in it, so do not bump it while placing the second item.
- The bin's lid joint starts at 0.63-0.66 in all 20 instances (template and instance `joint_pos`). The joint limits are in the encrypted USD, so whether the lid is open or ajar is unverified. The demos never open it.

### Minimal plan

1. `move to the half pomegranate`. Done when the counter and the fruit are centred in the head camera and the base has stopped. About 10 s.
2. `pick up the half pomegranate from the countertop`. Done when the gripper is closed but not fully (the fingers stopped short) and the fruit is gone from the counter. About 10 s.
3. `move to the trash can`. Done when the bin is in front at arm's reach and the base has stopped. About 10 s.
4. `place the half pomegranate in the trash can`. Done when the gripper is open and the fruit is not visible on the rim or the floor. About 9 s.
5. `move to the half banana`. About 10 s.
6. `pick up the half banana from the countertop`. About 10 s.
7. `move to the trash can`. About 10 s.
8. `place the half banana in the trash can`. About 9 s.

- The plan totals about 80 s against a 181.9 s limit.
- To save one trip, pick both halves first, one per hand (two `pick up ... from the countertop` calls), then do one `move to the trash can` and two places. This is unverified: the modal demo order (88% of demos) carries one item per trip.

### What the demos do differently

- 100% of demos first carry the trash can to the furniture sink (`pick up the trash can from the floors`, `place the trash can on the floors next to the furniture sink`). The goal does not need this. Skip it and save about 35 s.
- Carrying the 0.8 m bin also risks tipping the robot. The bin stays a valid target wherever it ends up.
- The demos go pomegranate first, then banana. The order does not matter for the goal.

### Hard parts and hacks

- The pomegranate half has no dimension under 44 mm, so a VLA grasp may slip. If the grasp fails twice, try pushing the half off the counter edge into the bin. This only works if the bin sits next to the counter, which is unverified.
- The bin is 0.80 m tall. Release above the opening, not beside it. The fruit's centre has to end up in the cavity.
- The food and the bin move between instances (the food spreads about 1.5 m and the bin about 1.3 m). Do not reuse a fixed route.
- ft40k scored Q=0 on instance 311, so the task sentence alone does not work. Use skill sentences.

### Hints for the VLM

- Both halves start on the kitchen countertop (z ~1.06-1.12 m). The robot starts in the living room, 1.2-4.8 m away.
- The target bin is a 0.8 m tall kitchen trash can with a hinged lid. Do not use the public trash can, which is a different category.
- Done for each literal: the fruit is not visible on the counter or the floor, and looking down into the bin shows it inside.
