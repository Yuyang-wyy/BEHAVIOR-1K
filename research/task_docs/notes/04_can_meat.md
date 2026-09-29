## Planner notes

**Tier:** C — two hinged jars must come out of a high wall cabinet (z ~1.6 m), be opened and closed while held, get 2 bratwursts each, and go back. It is bimanual lid work at head height, on top of 6 pick-and-places.

### Goal in plain words

- Each of the 2 hinged jars holds **exactly 2** bratwursts. Any 2 of the 4 bratwursts may go in either jar.
- Both jar lids are closed at the end.
- Both jars are back inside `top_cabinet_lkxmne_2`.
- That cabinet is closed at the end, with every door within 5 % of closed.
- The bratwursts already start cooked (`cooked` in `:init`, MaxTemperature 72 °C in the template). No cooking is needed.

### Q traps

- There are 9 literals, and 5 of them are true at reset: both jars `inside` the cabinet, both jars `not open`, and the cabinet `not open`.
- Verified: both jars and the cabinet have joint_pos ~0 in the template and in all 20 instances. The jars' root z is 1.6 m, inside the cabinet.
- So the partial Q ceiling is 4/9 = 0.444. Only the 4 `inside bratwurst jar` literals can score.
- Partial-Q shortcut: take the jars out, open them, and put 2 bratwursts in each. That alone reaches 0.444, even with the jars left on the counter, lids open and cabinet open.
- Closing the lids, returning the jars and closing the cabinet earns 0 partial Q. It is only needed for full success (1.0).
- `forn (2)` needs exactly 2 per jar (PREDICATES §0). A third bratwurst in one jar blocks success. Partial Q is not hurt.
- The page's example option puts bratwurst_3 and _4 in both jars. It is just one of the 36 expansions. Any 2+2 split is equivalent.
- Closing a lid can push a bratwurst's centre out of the jar volume (§3). Re-check after `close the lid`.
- The cabinet has 2 doors (2 joints). A door left ajar blocks success (§6).

### Minimal plan

1. `move to the top cabinet` — base stopped under the wall cabinet. ~20 s.
2. `open the door of the right_door top cabinet`, then `open the door of the left_door top cabinet` — both doors swung open, jars visible on the lower shelf. ~67 s.
3. `pick up the hinged jar from the low_level top cabinet` — jar clear of the shelf. ~14 s.
4. `hand over the hinged jar with the right` — jar now in the other hand. ~11 s.
5. `move to the bratwurst` — cutting board with bratwursts in view. It is 2-4.6 m from the cabinet. ~20 s.
6. `open the lid of the hinged jar` — lid visibly swung up. ~10 s.
7. `pick up the bratwurst from the cutting board`, then `place the bratwurst in the hinged jar`, done 2 times — bratwurst not visible above the rim. ~46 s.
8. `close the lid of the hinged jar` — lid flush. ~7 s.
9. `move to the top cabinet`, then `place the hinged jar in the low_level top cabinet` — jar on the shelf, gripper withdrawn. ~29 s.
10. Repeat 3-9 for the second jar. ~155 s.
11. `close the door of the left_door top cabinet`, then `close the door of the right_door top cabinet` — both doors flush. ~40 s.

- The total is about 420 s against a 592.4 s limit.
- If the timer passes ~450 s before step 10 finishes, stop after the second jar's bratwursts. Q = 0.444 is already banked.

### What the demos do differently

- There are 24 distinct orders, and the most common covers only 32 % of demos. The variation is mostly which hand holds the jar and when the lid opens.
- Humans keep the jar in one hand and work the lid and bratwursts with the other. No demo sets the jar down on the counter. So `place the hinged jar on the ...` has no trained prompt.
- Humans return jar 1 before fetching jar 2, leaving the cabinet doors open in between.
- About 12 % of jar pickups (49 of ~400) and placements (48) use the `high_level` shelf wording. Either shelf is inside the cabinet.
- `turn to the hinged jar` appears 9 times. Its purpose is unclear; skip it.

### Hard parts and hacks

- Height: the jars sit at ~1.6 m, and the cabinet centre is at 1.79 m. Reaching in and back out is near the top of the R1Pro workspace. Tipping risk while holding the jar extended high is real.
- The jar's size vs the 44 mm span is unknown (model vzwhbg, scale 0.9). The bratwurst's width is also unknown (scale 0.5). It is long and thin, so it is likely graspable but unverified.
- The lid hinge needs a fingertip push while the other hand holds the jar still. VLA failures here are likely: the lid stays shut, or the jar is dropped.
- Dropping a bratwurst into a jar held at an angle can bounce it out. Place it low, over the opening.
- Travel: the cutting board is 2.0-4.6 m from the cabinet (x ~6.0-8.6 vs 4.0), and the robot does 4 legs. Rotation drift makes the return to the cabinet unreliable. Re-localise on the cabinet visually.
- Cheap legal shortcut for Q: after step 7 for both jars, the planner may skip everything else when time is short. See Q traps.

### Hints for the VLM

- The target is `top_cabinet_lkxmne_2`, a wall cabinet with 2 doors above the counter in `kitchen_0`. Its centre is at world x ~4.0, y ~0.65, z ~1.8.
- The kitchen has 3 top cabinets. Only the one holding the jars counts, so open doors until you see the 2 jars.
- The jars sit side by side on the lower shelf. Each has a hinged lid; its look is not verified.
- The cutting board lies on a counter at ~1.06 m with 4 bratwursts on it. It is the only cutting board. Its position varies by up to 2.7 m across instances.
- Distractors: 2 countertops, a bar, shelves, and a water glass. Do not put bratwursts in the glass.
- Done: each jar holds 2 bratwursts with the lid down, both jars are on the cabinet shelf, and both cabinet doors are flush.
