## Planner notes

**Tier:** D — every rust particle must be scrubbed off two small tools with steel wool, and then both tools packed into a lidded toolbox. The objects are scattered across a large garden.

### Goal in plain words

The trowel and the scraper must both carry zero rust particles, both be inside the toolbox, and the toolbox lid must be closed at the end. Where the steel wool ends up does not matter.

### Q traps

- 5 literals. `not open toolbox` is true at reset, so it never scores but blocks success. Max partial Q = 4/5 = 0.8.
- Result on 311 (ft40k): Q = 0.00.
- **All rust must go** (PREDICATES §12). Each instance has 40 rust particles (`rust.n.01_1.n_particles`), spread over both tools. One particle left keeps `covered` True.
- Steel wool removes rust with condition "always". The method is ADJACENCY: any rust particle inside the steel wool's world AABB grown by 2 cm is deleted that step. There is no rate limit below 200.
- Clean before packing, and check each tool from both sides: particles sit on the top and bottom faces (template offsets span roughly -6 to +13 mm about the tool centre).
- Close the lid last, and re-check that both tools are still inside: a tool poking out can stop the lid, or its centre can end above the volume.

### Minimal plan

1. `move to the toolbox` ~58 s (long walks here).
2. `open the lid of the toolbox` — lid up. ~28 s. It starts closed (joint_pos 0).
3. `pick up the steel wool from the toolbox` ~22 s. Keep holding it for both tools.
4. `move to the trowel`, `pick up the trowel from the driveway` — second hand. ~58 + 22 s.
5. `wipe the steel wool` — rub the pad along both faces of the trowel until no rust spots remain. ~10 s per pass.
6. `move to the toolbox`, `place the trowel in the toolbox` ~58 + 21 s.
7. `move to the scraper`, `pick up the scraper from the driveway`, `wipe the steel wool`, `move to the toolbox`, `place the scraper in the toolbox`.
8. Skip `place the steel wool in the toolbox` if the hand can simply drop it. It is not in the goal, but keep it out of the toolbox if it would block the lid.
9. `close the lid of the toolbox` — the lid is flush (within 5 % of closed). ~24 s.

The demo mean is 505 s against a 758 s limit. Base travel in the demos is 69 m.

### What the demos do differently

- 199/200 follow exactly the plan above, including putting the steel wool back in the toolbox.
- 59/200 add `move to the steel wool`.
- No demo carries the toolbox to the tools. Carrying it could save walks, but the toolbox has no handle data and it is 0.26 × 0.61 × 0.35 m.

### Hard parts and hacks

- **Distances:** trowel, scraper and toolbox are spread across the garden driveway area (per-object spread 29-37 m across instances). In several instances a tool is 25-29 m from the start (301, 309, 319, 320). Plan the walk order by what is nearest.
- **Grasps:**
  - The trowel (0.28 × 0.046 × 0.024 m) and scraper (0.175 × 0.055 × 0.024 m) lie flat on the ground. The narrow handle ends should fit the 44 mm jaws; exact handle widths are unverified.
  - The steel wool is a flat 0.31 × 0.087 × 0.02 m pad lying inside the toolbox. Its only thin axis is vertical, so a top-down grasp does not straddle it. This is the riskiest grasp (see r1pro-grasp-span lesson).
- **Scrubbing geometry:** the removal box is the steel wool's world-aligned AABB plus 2 cm. A pad held flat is only ~6 cm tall with that margin.
  - Pass it over the tool so the tool's faces fall inside that box. Tilting the pad enlarges the AABB.
- Possible shortcut (derived, unverified): the steel wool does not need to be held for removal. Pressing a held tool flat onto the pad lying in the toolbox would clear the particles inside the pad's AABB + 2 cm, but not the top face.

### Hints for the VLM

- Garden of house_single_floor, on or near the driveway. The toolbox is a 0.6 m long box on the ground with a lid (`toolbox_redmtl`), and at start the steel wool is inside it.
- Rust shows as small spots on the metal tools. A tool is done when no spot is visible on either face.
- Done: both tools lying in the toolbox and the lid shut. The steel wool may be anywhere.
