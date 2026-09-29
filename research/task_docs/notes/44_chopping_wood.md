## Planner notes

**Tier:** D — four slice transitions with an axe. The logs are wider than the jaws, but they do not need to be moved.

### Goal in plain words

The four logs must each be split once, which gives eight `half__log` objects. **Tool:** the axe `axe_173` (`ax.n.01`, a `slicer` in the KB). The chopping block is **not** in the goal. `SlicingRule` needs only contact between an active slicer and the sliceable (`transition_rules.py:923-996`). Where the halves end up does not matter.

### Q traps

- 8 literals, all false at start. Max Q is 1.0. Each split log adds 2/8 = 0.25, because the two halves fill the next two free `half__log` slots (§7).
- `half__log` is **not** `diceable` (KB), so hitting a half again destroys nothing (§7).
- After each split the axe must stay off every sliceable log for 2 s to re-arm. Halves do not count, so resting the axe on halves is fine.
- A log that rolls away on first touch still counts, because one frame of contact is enough (§7). A glancing touch while the axe is still in its cooldown does not count.

### Minimal plan

This plan chops the logs where they lie. It is derived and not in the demos.

1. `move to the axe`, then `pick up the axe from the driveway` — axe lifted by its handle. ~14 s + ~17 s.
2. For each of the four logs:
   - `move to the log` — log in front of the robot at floor level. ~14 s.
   - `chop the axe with the log` — bring the axe head down onto the log. Done when two half-logs lie where the log was. ~8 s.
   - If nothing happens, lift the axe for 2 s and press again.
3. Stop. Keep the axe in hand; placing it back is not needed.

The plan takes about 130 s against a 538 s limit. Base travel between logs dominates.

### What the demos do differently

- Every demo carries each log to the chopping block (`pick up the log from the driveway`, `move to the chopping block`, `place the log on the chopping block`, ~45 s per log). It then sweeps or pushes the halves off the block (`sweep the half log 176 and half log 176 off the driveway`, `push the half log 174 to the driveway`). None of that affects the goal.
- They finish with `place the axe on the driveway`, which is also not needed.
- Useful prompts if the in-place chop fails: `place the log on the chopping block`, then `chop the axe with the log` (800 demo segments each).

### Hard parts and hacks

- **Logs do not fit the jaws.** Each is 299 x 101 x 99 mm (asset bbox × scale), and no axis is under 44 mm. The demo's carry to the block is therefore the risky part. Chopping in place removes every log grasp.
- **Low reach.** The logs rest on the driveway with their centres at z 0.05, so the robot must lower its trunk to reach them with the axe head. The block (100 mm tall) raises them only 10 cm.
- **Axe.** `plqyos` is 535 x 204 x 41 mm overall, so it fits the jaws. The handle width alone is not verified.
- **Scatter.** The logs, axe and block are spread over the 7.4 x 7.1 m driveway, with up to about 6 m between logs in one instance. Rotation drift makes re-finding logs costly. Chop the nearest log first.
- Heavy axe held far out: keep the arm low while driving to avoid tipping.

### Hints for the VLM

- Garden of `house_double_floor_lower`. The driveway is the paved area near (-12.7, 5.7), west of the house. It is separate from the lawns.
- Logs are brown cylinders about 30 cm long, lying on the pavement. There are exactly four. The chopping block is a short, wider stump. The axe lies flat on the ground.
- A split log shows as two half-cylinders side by side.
- Done: no whole log left. The episode ends by itself on success.
