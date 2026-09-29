## Planner notes

**Tier:** D — four items out of a closed two-door cabinet into the washer, then a washer cycle (a state transition) clears three particle systems.

### Goal in plain words

Both teddy bears must be free of dirt and dust, the tennis ball free of debris, the softball free of dirt.
The route is one washer cycle with all four toys inside: open washer, open cabinet, move the four toys into the washer, close the washer door, turn it on.
The cabinet may be left open: the goal has no `not open` literal.

### Q traps

- 6 literals, 2 already true at reset, so max partial Q is 0.667 (4 scoring literals). Verified from the template `system_registry` in all 20 instances:
  - dirt: 40 particles, 20 on `teddy_bear_191` (teddy_1) and 20 on the softball;
  - dust: 20 particles, only on `teddy_bear_190` (teddy_2);
  - debris: 20 on the tennis ball (19 or 13 in instances 309, 314, 315).
  - So `not covered teddy_2 dirt` and `not covered teddy_1 dust` are true at reset and never score. The page is right.
- The washer cleans only on the step it **changes** to (toggled on AND closed) (`transition_rules.py:745-757`). Per system, it clears `covered` only if the washer volume holds at least 1 particle of that system at that step (`transition_rules.py:846-884`). Then every object with any collision point in the volume is cleaned of it.
  - dust lives only on teddy_2, and debris only on the tennis ball. If either of them is missing or only grazing the rim, that literal stays false even though the others clean.
- Washer starts closed and off in all 20 instances; the cabinet (`gjrero_0`, 2 doors) starts closed in all 20 (joint_pos ~0).
- Four toys in one drum: a teddy leg or ball in the doorway keeps the door >5 % open (§6), so nothing fires. Check the door is flush before pressing.
- Fallback: several cycles work. Opening the washer forces it off; close and press again to fire a new cycle. Each toy scores 1 literal (Q 0.167 each).
- Success ends the episode on the press step.

### Minimal plan

1. `move to the washer` — washer front in view. ~14 s.
2. `open the door of the washer` — door open, drum visible. ~34 s.
3. `move to the bottom cabinet no top` — cabinet doors in view at close range. ~14 s.
4. `open the door of the left_door bottom cabinet no top` — left door swung open. ~34 s.
5. `open the door of the right_door bottom cabinet no top` — right door open; both shelves visible. ~34 s.
6. `pick up the teddy bear from the high_level bottom cabinet no top` (or `..._middle_level ...`, and the softball / tennis ball variants, matching the shelf the item is on) — gripper closed short of fully closed; item gone from the shelf. ~13 s each. Carry two items per trip, one per hand.
7. If an item faces the wrong way: `push the teddy bear to the reorient bottom cabinet no top` (same for softball / tennis ball). ~12 s.
8. `move to the washer` — ~14 s.
9. `place the teddy bear in the washer` / `place the softball in the washer` / `place the tennis ball in the washer` — item released, not visible outside the drum. ~21 s each.
10. Repeat 3, 6, 8, 9 for the second pair (`move to the teddy bear` etc. also works as the move prompt).
11. `close the door of the washer` — door flush. ~21 s.
12. `turn on the washer` — fingertip on the control; episode ends on success. ~22 s.

About 350 s against a 561.1 s limit; the representative demo is already this plan (350.8 s). Prioritise teddy_2 (dust) and the tennis ball (debris) if time is short: they are the only carriers of those systems.

### What the demos do differently

- All demos open the washer before the cabinet, then do two trips of two items each.
- 253 segments reorient a teddy inside the cabinet with `push ... to the reorient ...` before grasping it. Balls are reoriented less often.
- Humans never close the cabinet; do not spend time on it.
- The shelf words `high_level` / `middle_level` in the prompts track which shelf the item is on (items sit at z≈0.71 or z≈0.45 in the instances; the mapping of words to shelves is unverified).

### Hard parts and hacks

- Grasping inside a cabinet shelf with doors half in the way; the low shelf is at ~0.45 m.
- Item sizes are unknown (no custom list). Demos grasp all four, so some part registers within 44 mm; which part is unverified (teddy limbs likely).
- Cabinet and washer door handles: width vs 44 mm unverified. The washer door is the slow step.
- The cabinet row (x≈24.58) faces the washer (x≈22.0) across the room, ~2.6 m apart.
- Button location on washer `ynwamu` unverified; the press needs 5 steps of finger contact on the button sphere (§11). A scripted press routine is legal once the hand is there.
- Closed-loop so far: Q 0.00 on instance 311 for all three checkpoints.

### Hints for the VLM

- Utility room. The toys are always in `bottom_cabinet_no_top_gjrero_0`, the end cabinet (y≈1.68) of a row of four identical two-door cabinets under the long counter. The other three (and a fifth under the far counter) are distractors.
- Washer and clothes dryer stand side by side on the opposite wall (washer y≈0.33, dryer y≈0.95). Use the washer.
- Two teddy bears (slightly different scale, 0.8 vs 0.9), one tennis ball, one softball. Dirt, dust and debris show as small specks on them; they vanish on the press step.
- Done = all four toys out of the cabinet and inside the washer drum, washer door flush, washer pressed.
