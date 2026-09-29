## Planner notes

**Tier:** C. Three flat books (26-33 mm thick, 0.12-0.21 m across) lying on a desk; the only graspable axis is the thickness, which needs the push-to-edge overhang and usually a hand-over to fit the book into a small cubby. Closed loop scored Q = 0.00 on 311.

### Goal in plain words

- All three `book.n.02` objects must end inside any bookcase: hardback `aceozs` (0.198 x 0.149 x 0.026 m), notebook `aanuhi` (0.151 x 0.120 x 0.027 m), hardback `agbqsy` (0.213 x 0.169 x 0.033 m). Sizes are asset bbox at scale 1.0.
- Any book may go in any of the 4 bookcases (64 ground options). All three in the same cubby is fine.
- Nothing needs to be closed. Nothing is required to stay on the desk.

### Q traps

- No literal is true at reset; max Q = 1.0, 1/3 per book. Books start on the desk top (z 0.75) in all 20 instances.
- `inside` passes only if the book's AABB centre is inside the bookcase's `openfillable` volume (PREDICATES §3). The probe on instance 301 measured one volume per bookcase of about 0.29 x 0.31 x 0.26 m, centred at z ~0.53 m (TASK_AUDIT.md). The unit is 0.30 x 0.76 x 1.05 m, so the volume is one cubby-sized box, not the whole unit.
- Which cubby that box covers is unverified. It sits at the unit's mid-height (about 0.40-0.66 m), so aim for a middle-row cubby. A book on top of the bookcase (1.05 m) or in a top or bottom cubby most likely scores 0.
- A book resting half out of the cubby still counts if its centre is inside; one balanced on the front edge does not.

### Minimal plan

One book at a time, as all demos do. Times are demo means for this task.

1. `move to the notebook` (or `move to the hardback`) — base stopped facing the desk with the book in view. ~24 s.
2. `push the notebook to the desk` — book slid until part of it overhangs the desk edge. ~22 s.
3. `pick up the notebook from the desk` — gripper closed on the overhang, short of fully closed; book lifted off the desk. ~13 s.
4. `move to the bookcase` — white cube unit in view at close range. ~10 s.
5. `hand over the notebook` — book now held by the other hand in an orientation that fits the cubby. ~11 s.
6. `move to the bookcase` — small approach to face a middle-row cubby. ~10 s.
7. `insert the notebook into the bookcase` — book inside the cubby opening, gripper open and withdrawn. ~15 s.
8. Repeat 1-7 for each hardback with `move to the hardback`, `push the hardback to the desk`, `pick up the hardback from the desk`, `hand over the hardback`, `insert the hardback into the bookcase`.

About 105 s per book, ~320 s total against a 476 s limit.

### What the demos do differently

- 80% of demos follow exactly this 21-step order; 19 distinct orders.
- The hand-over appears in about 570 of 600 book transfers. It is a regrasp, not required by the goal; skip it only if the book is already held in a way that clears the cubby opening.
- Demos always use `insert ... into the bookcase`, never `place ... in`. Use `insert`.
- The two `move to the bookcase` steps around the hand-over are one approach split in two.

### Hard parts and hacks

- Grasp: lying flat, no book has a horizontal axis near 44 mm (smallest is 120 mm). Only the 26-33 mm thickness fits the jaws, which needs a finger under the book. The push-to-edge overhang is the enabling step; a top-down grasp on the flat book cannot work (PICK_PLACE_STATUS.md).
- The push must leave the book overhanging but not falling. A book that drops to the floor must be picked from the floor, which is harder still.
- Placement: the target volume is about 0.31 m wide and 0.26 m tall. A 0.21 m book held flat by its edge fits; a book held so that it sticks out towards the robot may collide with the cubby frame.
- No verified scripted pick exists for this task yet; three scripted attempts on a similar task achieved zero grasps.
- Partial credit is per book, so securing one book (Q = 0.33) beats spending the whole budget on retries.

### Hints for the VLM

- Single room, living_room_0 of `house_double_floor_upper` (the same room as tidying_living_room). Sloped ceiling, beige sectional sofa, glass coffee table, stair well with glass railing.
- Desk: light wood top on a black metal frame with wheels, with a table lamp and a white chair; the three books lie flat on it about 0.74 m high. The coffee table is not the target table (blacklisted for `table.n.02`).
- Bookcases: four identical white cube units in one row along the wall, 0.76 m apart, about 2.3 m from the desk. They read as one long cubby wall; any unit counts.
- Distractors: none of category hardback or notebook outside the three goal books.
- Done looks like: desk top empty of books; three books visible inside middle-row cubbies.
