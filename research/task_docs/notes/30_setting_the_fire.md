## Planner notes

**Tier:** D. Pick-and-place of a newspaper and two logs into the fireplace, then an ignition (a state transition) with a held, toggled lighter that must be switched off again.

### Goal in plain words

Both logs must rest directly on the newspaper, with their centres inside the wood fireplace, and both logs and the newspaper must be on fire. The lighter must end switched off. The newspaper itself has no `inside` literal, but it has to be under the logs in the fireplace for the log literals to hold. There is one ground option.

### Q traps

- `not toggled_on cigar_lighter` is true at reset (template `ToggledOn` value False) and never scores: 8 literals, max partial Q 0.875. Leaving the lighter on still blocks success.
- `on_fire` latches (PREDICATES §14): once a log or the paper burns, it stays burning, even if it is moved later. Igniting early costs nothing.
- `ontop log newspaper` needs direct contact and the paper under the log's AABB-centre x-y (§4). A log stacked on the other log, or resting on the fireplace floor beside the paper, fails. The paper asset is 0.29 x 0.21 m (asset metadata bbox, no custom list; unverified at runtime), a log 0.26 x 0.078 x 0.066 m; two logs side by side along the paper's long side fit.
- ft40k scored 0.75 (6/8) on instance 311. Without any `inside` literal the best is 5/8, so at least one log counted as inside: the fireplace has a working fillable volume (inferred from that result).
- Grasping the lighter can press its toggle button by accident (derived: finger contact plus overlap of the button sphere for 5 steps flips it, §11). Check the flame state after every grasp and release.
- A second press flips the lighter back. Turn it off with exactly one clean press.

### Minimal plan

1. `move to the newspaper` -> `push the newspaper to the to_the_edge_of coffee table` -> `pick up the newspaper from the coffee table`. Done: gripper closed short of full closure, paper off the table. ~85 s (push mean 38 s).
2. `move to the firewood` -> `pick up the firewood from the floors` with the free hand. Done: log lifted in the second gripper. ~33 s.
3. `move to the wood fireplace` -> `place the newspaper in the wood fireplace` -> `place the firewood in the wood fireplace`. Done: paper flat on the fireplace floor, log lying on it. ~50 s.
4. `move to the lighter` -> `pick up the lighter from the coffee table` -> `turn on the lighter`. Done: flame visible at the lighter tip. ~40 s.
5. `move to the firewood` -> `pick up the firewood from the floors` (other hand) -> `move to the wood fireplace`. ~45 s.
6. `ignite the lighter with the firewood`. Hold the flame at the log for ~3 s (lighter 23 -> 250 °C in ~2.7 s, derived). Done: fire visible on the held log. ~6 s.
7. `place the firewood in the wood fireplace`, next to the first log and on the paper. The burning log ignites the paper and the other log if they are within 0.2 m of its centre (~7 s, derived). ~16 s.
8. `turn off the lighter`. Done: flame gone. ~10 s. Then wait a few seconds and check that the paper and both logs show fire.

Total about 290 s against a 456 s limit, the same as the demo; the demo has no removable steps.

### What the demos do differently

- 94 % of demos follow exactly the order above. The demos carry the lit lighter to the second log and ignite it while holding it, so the robot holds lighter and log in two hands at once.
- 11 demos use `ignite the firewood with the lighter` and 2 ignite the newspaper; the in-distribution wording is `ignite the lighter with the firewood` (187 demos).
- A simpler variant, not in the demos: put both logs on the paper first, then light the paper or a log in place with the lighter. It avoids the two-handed carry but needs the lighter to reach into the firebox; no trained prompt for "ignite in place" other than `ignite the lighter with the firewood`.

### Hard parts and hacks

- Grasp widths (asset metadata bbox, no custom list; unverified at runtime): newspaper 46 mm thick (at or over the 44 mm limit, hence the push-to-edge), log 66-78 mm across its cross-section (above the limit unless grasped at an end or tapered part; unverified how the demos' grasp registers), lighter 18 mm thick.
- Log placement is the precision step: both log centres over the 0.29 x 0.21 m paper, in contact with it, inside the firebox. Dropping from height can roll a log off the paper.
- Keep the two logs close (centres within 0.2 m of each other and of the paper centre) so one ignition spreads to all three.
- The lighter heats anything within 0.2 m of its tip while on (§2). Switch it off before putting it down.
- Log start positions vary by up to 4.7 m between instances; the paper and lighter are always on the coffee table.

### Hints for the VLM

- living_room_0 has one wood fireplace, one coffee table, one lighter, one newspaper and two logs; no same-category distractors.
- The logs start on the floor; the newspaper and lighter start on the low coffee table (~0.4 m).
- The fireplace is a large fixed unit (0.74 x 1.75 x 1.31 m asset bbox, unverified at runtime) against a wall; the firebox opening faces the room.
- Fire should show as a flame effect on the object (rendering unverified). Done means flame on both logs and the paper, logs lying on the paper, lighter with no flame.
