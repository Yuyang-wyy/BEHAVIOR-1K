## Planner notes

**Tier:** C. Seven pick-and-place moves plus a laptop lid close; the laptop (0.32 x 0.45 m per asset bbox, unverified) and the flat books and folders must be pushed to an edge before they can be grasped, and the stapler sits on a bookcase shelf up to 1.38 m high.

### Goal in plain words

Both folders and both paperback books end inside the one bookcase in childs_room_1; any shelf is fine if the bookcase's fillable volume covers it (unverified). Both pens and the pencil end inside the pencil case, and the case must still rest on the desk. The stapler comes out of the bookcase onto the desk. The laptop moves from the bed onto the desk and its lid ends closed. There is one ground option, so no choice of container.

### Q traps

- `ontop pencil_box desk` is true at reset and never scores (11 literals, max partial Q 0.909). It still blocks success, so if the case is lifted it must go back on the desk.
- `not open laptop` is NOT true at reset: the template gives the laptop hinge `joint_pos` 2.4 rad in all 20 instances, so it starts open and closing it scores. The joint range is not in the asset metadata; "closed" means within 5 % of the closed end (PREDICATES §6).
- The stapler starts inside the bookcase; there is no `not inside` literal, only `ontop stapler desk`.
- `inside pen pencil_case` needs the pen's AABB centre inside the case's fillable volume. The case asset metadata lists no meta links; whether the runtime USD has a fillable link is not verified (PREDICATES §3). A pen resting across the rim scores nothing.
- Books or folders placed on top of the bookcase (1.76 m tall) are not inside it.
- Placing items on the desk next to the pencil case can knock it; the case sitting on a folder or pen instead of the desk breaks `ontop pencil_box desk` (needs direct contact, §4).
- Closing the lid while the laptop overhangs the desk edge can tip it off.

### Minimal plan

1. `move to the paperback book` -> `push the paperback book to the to_the_edge_of desk` -> `pick up the paperback book from the desk` -> `move to the bookcase` -> `place the paperback book in the 2X3 bookcase`. Done: book no longer on desk, visible on a shelf in the depth image. ~65 s each; repeat for the second book.
2. Same for the folder on the desk: `push the folder to the to_the_edge_of desk`, `pick up the folder from the desk`, `place the folder in the 3X3 bookcase`. ~70 s.
3. Folder on the chair: `move to the folder`, `push the folder to the to_the_edge_of eames chair`, `pick up the folder from the eames chair`, `move to the bookcase`, `place the folder in the 3X3 bookcase`. ~75 s. Skip the demo's `push the eames chair to the under desk`; the chair is not in the goal.
4. `move to the pen` -> `pick up the pen from the desk` -> `insert the pen into the pencil case`. Done: pen gone from desk surface, not lying across the case. ~35 s each; repeat for the second pen, then the pencil (`pick up the pencil from the desk`, `insert the pencil into the pencil case`). The demos hold the case with the other hand (`pick up the pencil case from the desk` first); inserting into the case while it rests on the desk avoids having to re-place it (untested). If the case was lifted: `place the pencil case on the desk`.
5. `move to the laptop` -> `push the laptop to the to_the_edge_of bed` -> `pick up the laptop from the bed` -> `move to the desk` -> `place the laptop on the desk`. Done: laptop visible flat on the desk top. Budget ~150 s; the push alone averages 34.5 s and took 114 s in the representative demo.
6. `close the lid of the laptop`. Done: screen no longer vertical, laptop a thin slab in depth. ~23 s.
7. `move to the stapler` -> `pick up the stapler from the 1x1 bookcase` -> `move to the desk` -> `place the stapler on the desk`. ~60 s; longer when the stapler is on the top shelf.

Total roughly 650 s against a 1071 s limit.

### What the demos do differently

- 167 distinct orders; no single order dominates (3 %). Order among the sub-goals is free.
- Humans stack the second folder and second book on the first (`place the folder on the folder`, `place the paperback book on the paperback book`). That is fine if the stack's centre stays inside the bookcase volume.
- Humans push the eames chair under the desk; not needed.
- Humans pick up the pencil case and insert pens while holding it, then put it back on the desk.
- The shelf words `1x1`, `2X3`, `3X3` in the prompts are annotation labels for bookcase cells; keep them verbatim.

### Hard parts and hacks

- Grasp widths from asset metadata bbox times template scale (no custom list; unverified at runtime): paperback book 20 mm thick, folder 45 mm (at the 44 mm limit), pen and pencil 15 mm, stapler 40 mm wide, laptop 37 mm closed. Flat items on a surface need the push-to-edge step so a jaw can go under.
- The laptop is the largest and slowest item; ft40k scored 0.27 (3/11) on instance 311, which literals is unknown.
- Stapler shelf height varies by instance (root z): 0.17-0.18 m in 301, 302, 310, 314, 316; ~0.58 m in 307, 312, 313, 315; ~0.98 m in 303, 317, 319, 320; ~1.38 m in 304, 305, 306, 308, 309, 311, 318. Half the leaderboard instances (301-310) have it on the top shelf. Reaching 1.38 m at 0.33 m depth needs the trunk raised; low shelves need the trunk bent.
- For the books and folders, prefer the lowest reachable empty shelf that is at arm height.
- Pens into a ~105 mm-tall case (asset bbox, unverified): a vertical drop from above the opening is the natural motion; failure is the pen landing across the rim.

### Hints for the VLM

- Room childs_room_1 has exactly one desk, one bookcase, one bed, one eames chair and one nightstand; no same-category distractors for goal furniture.
- Layout is fixed: bookcase near (22.9, 12.5), desk near (23.9, 13.2), bed near (21.3, 13.0); all within ~2.7 m, so few long drives.
- At start one folder is on the chair, the other folder, both books, both pens, the pencil and the pencil case are on the desk, the laptop is open on the bed, the stapler is on a bookcase shelf.
- Done looks like: desk holds only the pencil case (with pens and pencil hidden inside), the stapler and the closed laptop; four flat items on bookcase shelves.
