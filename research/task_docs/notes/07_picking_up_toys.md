## Planner notes

**Tier:** B, borderline C. Pure pick-and-place into an open box, but five of the six items are flat boxes that the humans push to the table or bed edge before they can grip them.

### Goal in plain words

- All six toys must end with their AABB centre inside the toy box: 3 board games, 2 jigsaw puzzles, 1 tennis ball.
- There is only one toy box, so there is no container choice.
- The toy box has no lid or joints (no `joint_pos` in the template registry), so nothing needs opening or closing.
- Nothing must be left out; there are no `not` literals.

### Q traps

- 6 literals, none true at reset. Each item placed is worth 1/6.
- Zero-shot `zs_pt50` reached Q=0.83 (5/6) on instance 311, so the toy box's `inside` volume works in practice.
- Partial Q reads only the final state. Bumping or dragging the toy box can spill items already inside (PREDICATES.md §3, knock-on displacement).
- A flat box leaning on the rim with its centre outside the box scores nothing. Check it dropped in.
- The toy box itself must stay on the desk. 55/200 demos lifted it and set it back `on the to_the_edge_of desk`; not needed.

### Minimal plan

Order: desk items first (toy box is on the same desk), then the two bed items.

1. `pick up the tennis ball from the desk`. Done: gripper closed, fingers short of fully closed, ball gone from desk. ~25 s.
2. `place the tennis ball in the toy box`. Done: gripper open, ball visible inside the box in RGB. ~17 s.
3. `push the jigsaw puzzle to the to_the_edge_of desk`. Done: puzzle overhangs the desk edge nearest the robot. ~46 s.
4. `pick up the jigsaw puzzle from the desk`. Done: puzzle lifted clear of desk. ~25 s.
5. `place the jigsaw puzzle in the toy box`. ~17 s.
6. Repeat 3-5 for the second jigsaw puzzle.
7. `push the board game to the to_the_edge_of desk`, `pick up the board game from the desk`, `place the board game in the toy box`. ~90 s.
8. `move to the board game` (the ones on the bed). ~15 s.
9. `push the board game to the to_the_edge_of bed`. ~46 s (demo segments on the bed run up to ~130 s).
10. `pick up the board game from the bed`. ~25 s.
11. `move to the toy box`. Done: base stopped facing the desk with the box in view. ~15 s.
12. `place the board game in the toy box`. ~17 s.
13. Repeat 8-12 for the second board game on the bed.

Budget: human mean 630 s, limit 944.5 s. Push steps dominate (mean 46 s each, 5 per demo).

### What the demos do differently

- The representative demo does bed games first, then desk items. Order does not matter for the goal.
- 55/200 demos pick up the toy box and re-place it at the desk edge. Skip it: it risks spilling items.
- 74 hand-over segments across 200 demos (`hand over the board game with the left` is the common one) appear. Not needed if one arm can place.
- Humans push every flat item (board games, puzzles) to an edge before picking; only the tennis ball is picked directly.

### Hard parts and hacks

- Board game and puzzle sizes are unknown (no custom list). The consistent push-to-edge in 200/200 demos suggests their top faces are too wide for the 44 mm jaws, so the grip goes on the overhanging thin edge.
- The jigsaw puzzle asset (antykn) is scaled 7.6x in z and ~1x in x-y, so it is a thicker slab than the native model. Its real thickness is unknown.
- The bed items sit low (z ~0.5 m) on a soft-looking bed; pushing them to the edge is the slowest demo step.
- Pushing too far drops the item on the floor. Then `pick up the board game from the floors` is not a trained prompt for this task (unverified whether Comet generalises).
- The bed and desk are ~2.5 m apart (template poses), so each bed item needs a carry.
- No scripted shortcut beyond the pushes: every literal needs a grasp or a drop into the box.

### Hints for the VLM

- Everything is in `childs_room_0`. The other two child's rooms have no toys or toy box (template init_info).
- The "table" in the BDDL is a desk (`desk_xhjsub_0`). The toy box sits on it at z ~0.83 m.
- Two board games start on the bed, one on the desk; both puzzles and the ball start on the desk. Positions shift up to ~1.8 m between instances, so look, do not assume.
- There are no other board games, puzzles or balls in the loaded scene to confuse with.
- Done looks like: desk and bed empty of toys; all six visible inside the open toy box.
