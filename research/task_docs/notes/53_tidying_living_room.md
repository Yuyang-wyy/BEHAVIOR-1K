## Planner notes

**Tier:** C. Nothing in the goal has an axis at or under the ~44 mm jaw span except by edge-grasping: the pot plant is 0.25 x 0.26 x 0.29 m and the hardback's thinnest axis is 47 mm (asset bbox, scale 1.0).

### Goal in plain words

- Four literals, none true at reset: pot plant on the coffee table, newspaper on the coffee table, notebook on the desk, hardback inside any one of the 4 bookcases.
- The task sentence is misleading: it says "put the books and papers into the bookcase", but the BDDL wants the newspaper on the coffee table and the notebook on the desk. Only the hardback goes in a bookcase.
- The 4 bookcases are interchangeable (4 ground options). There is one coffee table and one desk in the room.
- Nothing must stay closed. The only thing to avoid is stacking: an object resting on another object does not touch the table and fails `ontop`.

### Q traps

- No literal is true at reset (checked against `:init` and the 20 instances: newspaper and pot plant start on the floor, hardback and notebook start on the coffee table). Max Q = 1.0.
- Hardback and notebook start ON the coffee table. Put the newspaper and pot plant on free table area, not on top of them: stacked, they do not touch the table and `ontop` is False (PREDICATES §4).
- Do not put the pot plant on the newspaper for the same reason.
- `inside` bookcase uses one `openfillable` volume per bookcase of about 0.29 x 0.31 x 0.26 m, centred at z ~0.53 m (task_feasibility_probe on re_shelving_library_books 301, same bookcase model `otwukr` in the same scene). That is far smaller than the 0.30 x 0.76 x 1.05 m unit. Which cubby it covers is unverified; aim for a middle-row cubby (about 0.40-0.66 m high). A book on top of the bookcase or in a top or bottom cubby likely does not count.
- The coffee table is not fixed (`fixed: false`). Bumping it can shift or tip items already placed; placed items are scored only at the end.
- Closed loop on 311 got Q = 0.50 (2 of 4), which literals is not recorded.

### Minimal plan

Demo order already matches the goal; keep it. Times are demo means for this task.

1. `move to the newspaper` — base stopped with the newspaper (flat sheet on the floor) in view. ~21 s.
2. `pick up the newspaper from the floors` — gripper closed but not fully, sheet gone from the floor. ~35 s.
3. `move to the pot plant` — ~25 s.
4. `pick up the pot plant from the floors` (other arm) — pot lifted off the floor. ~38 s.
5. `move to the coffee table` — low glass-topped table in view. ~25 s.
6. `place the newspaper on the coffee table` — sheet lying flat on the glass, clear of the hardback and notebook. ~18 s.
7. `place the pot plant on the coffee table` — pot upright on bare glass, not on the newspaper. ~19 s.
8. `move to the hardback` — ~26 s.
9. `push the hardback to the coffee table` — hardback slid until it overhangs the table edge. ~28 s.
10. `pick up the hardback from the coffee table` — book no longer on the glass. ~23 s.
11. `move to the bookcase` — nearest white cubby unit in view. ~20 s.
12. `place the hardback in the bookcase` — book inside a middle-row cubby, gripper open and withdrawn. ~20 s.
13. `move to the notebook` — ~24 s.
14. `push the notebook to the coffee table` — notebook overhangs the edge. ~28 s.
15. `pick up the notebook from the coffee table` — ~21 s.
16. `move to the desk` — ~24 s.
17. `place the notebook on the desk` — notebook flat on the desk top. ~17 s.

Total ~400 s against a 628 s limit.

### What the demos do differently

- 52% of demos follow exactly the order above; 16 distinct orders in total.
- 88 of 200 demos add `hand over the hardback` before shelving it (about 15 s). The goal does not need it; it is a regrasp to get the book upright for the cubby.
- 6 demos use `insert the hardback into the bookcase` instead of `place ... in`. Prefer `place the hardback in the bookcase` (193 uses).
- The "push to the coffee table" steps are edge-overhang manoeuvres, not moves between furniture: the book already is on the coffee table.

### Hard parts and hacks

- Pot plant: 0.25 x 0.26 x 0.29 m, no thin axis in the bbox. Demos pick it from the floor every time (200/200), so some part (pot rim or stem) is graspable, but which part is unverified. Expect the most failed grasps here.
- Hardback `prifte`: 0.256 x 0.213 x 0.047 m. Its thickness is just over the 44 mm span; lying flat it cannot be straddled. The push-to-edge trick gives a finger access under the overhang; whether the 47 mm cover then registers is unverified.
- Notebook `ksxknp`: 0.068 x 0.110 x 0.014 m. Thin, so the edge-overhang grasp should work; 68 mm across is too wide for a top-down grasp.
- Newspaper: forced size 0.29 x 0.39 x 0.03 m, rigid (not cloth). Lying on the floor it has no graspable edge; demos take ~35 s for this pick.
- The coffee table is low (0.36 m tall bbox, glass top). Placing needs the trunk bent down.
- If the hardback grasp fails repeatedly, skip it: the other three literals give Q = 0.75.

### Hints for the VLM

- Single room, living_room_0, upstairs of `house_double_floor_upper`, with an open stair well and a glass railing. Do not drive into the stair well.
- Coffee table: low table with a dark glass top and a thin metal frame, in front of the beige sectional sofa.
- Desk: light wood top on a black metal frame, with a table lamp and a white chair, next to the stair railing.
- Bookcases: four identical white cube units (0.76 m wide, 1.05 m tall) standing in one row along a wall, reading as one long cubby wall.
- Pot plant: a potted plant on the floor. Newspaper: a flat rectangular sheet on the floor.
- Done looks like: glass table holding the plant and the newspaper side by side; desk holding the small notebook; a book standing or lying inside a middle cubby.
