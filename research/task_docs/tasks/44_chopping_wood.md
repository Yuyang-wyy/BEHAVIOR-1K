# 44 · Chopping Wood

Task name `chopping_wood`, task index 44.

> Chop the four logs on the driveway in the garden into eight half logs using the axe and the chopping block.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garage_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 358.4 s mean (10751 steps) |
| episode time limit | 537.6 s (16127 steps at 30 Hz) |
| human base travel | 37.8297 m |
| goal literals (best ground option) | 8 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114061262 |

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

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real half__log.n.01_1)` | no | yes |
| `(real half__log.n.01_2)` | no | yes |
| `(real half__log.n.01_3)` | no | yes |
| `(real half__log.n.01_4)` | no | yes |
| `(real half__log.n.01_5)` | no | yes |
| `(real half__log.n.01_6)` | no | yes |
| `(real half__log.n.01_7)` | no | yes |
| `(real half__log.n.01_8)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (real ?half__log.n.01_1)
            (real ?half__log.n.01_2)
            (real ?half__log.n.01_3)
            (real ?half__log.n.01_4)
            (real ?half__log.n.01_5)
            (real ?half__log.n.01_6)
            (real ?half__log.n.01_7)
            (real ?half__log.n.01_8)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `log.n.01_1` | log_177 | log / pepele | garden_0 | floor, z 0.05 | 2.28 m (range 1.06-6.3) | yes, spread 8.49 m |
| `log.n.01_2` | log_176 | log / pepele | garden_0 | floor, z 0.05 | 2.67 m (range 0.7-6.99) | yes, spread 8.8 m |
| `log.n.01_3` | log_175 | log / pepele | garden_0 | floor, z 0.05 | 2.79 m (range 0.67-7.61) | yes, spread 8.75 m |
| `log.n.01_4` | log_174 | log / pepele | garden_0 | floor, z 0.05 | 3.36 m (range 0.8-5.66) | yes, spread 8.39 m |
| `half__log.n.01_1` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_2` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_3` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_4` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_5` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_6` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_7` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `half__log.n.01_8` | does not exist at reset; created by a transition (slicing, cooking, etc.) | half_log | - | - | - | - |
| `driveway.n.01_1` | driveway_umalys_0 | driveway / umalys | garden_0 | floor, z -0.15 | 2.67 m (range 0.96-3.71) | no (fixed) |
| `ax.n.01_1` | axe_173 | axe / plqyos | garden_0 | floor, z 0.02 | 3.35 m (range 1.07-6.39) | yes, spread 8.41 m |
| `chopping_block.n.01_1` | chopping_block_172 | chopping_block / ekowsj | garden_0 | floor, z 0.05 | 3.41 m (range 0.96-6.36) | yes, spread 7.91 m |

Initial conditions from `:init`:

```lisp
(future half__log.n.01_1)
(future half__log.n.01_2)
(future half__log.n.01_3)
(future half__log.n.01_4)
(future half__log.n.01_5)
(future half__log.n.01_6)
(future half__log.n.01_7)
(future half__log.n.01_8)
(inroom driveway.n.01_1 garden)
(ontop agent.n.01_1 driveway.n.01_1)
(ontop ax.n.01_1 driveway.n.01_1)
(ontop chopping_block.n.01_1 driveway.n.01_1)
(ontop log.n.01_1 driveway.n.01_1)
(ontop log.n.01_2 driveway.n.01_1)
(ontop log.n.01_3 driveway.n.01_1)
(ontop log.n.01_4 driveway.n.01_1)
(touching agent.n.01_1 driveway.n.01_1)
(touching ax.n.01_1 driveway.n.01_1)
(touching chopping_block.n.01_1 driveway.n.01_1)
(touching driveway.n.01_1 agent.n.01_1)
(touching driveway.n.01_1 ax.n.01_1)
(touching driveway.n.01_1 chopping_block.n.01_1)
(touching driveway.n.01_1 log.n.01_1)
(touching driveway.n.01_1 log.n.01_2)
(touching driveway.n.01_1 log.n.01_3)
(touching driveway.n.01_1 log.n.01_4)
(touching log.n.01_1 driveway.n.01_1)
(touching log.n.01_2 driveway.n.01_1)
(touching log.n.01_3 driveway.n.01_1)
(touching log.n.01_4 driveway.n.01_1)
```

## What the human demos did

200 annotated demos. Length 334.75 s (range 181.0-622.97). Skills per demo 28.0 (range 25-34). 46 distinct skill orders; the most common one covers 31% of demos.

Most common skill counts per demo (32% of demos): move to x9, pick up from x5, place on x5, chop x4, sweep off x4.

Representative demo `episode_00441090.json` (334.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the axe` (0.1-14.2 s)
2. `pick up the axe from the driveway` (14.2-42.9 s)
3. `move to the log` (42.9-50.7 s)
4. `pick up the log from the driveway` (50.7-66.2 s)
5. `move to the chopping block` (66.2-76.8 s)
6. `place the log on the chopping block` (76.8-85.3 s)
7. `chop the axe with the log` (85.3-90.6 s)
8. `sweep the half log 176 and half log 176 off the driveway` (90.6-97.2 s)
9. `move to the log` (97.2-133.6 s)
10. `pick up the log from the driveway` (133.6-145.3 s)
11. `move to the chopping block` (145.3-184.9 s)
12. `place the log on the chopping block` (184.9-196.6 s)
13. `chop the axe with the log` (196.6-200.5 s)
14. `sweep the half log 176 and half log 176 off the driveway` (200.5-205.3 s)
15. `move to the log` (206.3-220.4 s)
16. `pick up the log from the driveway` (220.4-233.5 s)
17. `move to the chopping block` (233.5-242.5 s)
18. `place the log on the chopping block` (242.5-251.6 s)
19. `chop the axe with the log` (251.6-261.1 s)
20. `sweep the half log 176 and half log 176 off the driveway` (261.1-265.4 s)
21. `move to the log` (265.4-282.9 s)
22. `pick up the log from the driveway` (282.9-299.8 s)
23. `move to the chopping block` (299.9-310.1 s)
24. `place the log on the chopping block` (310.1-318.6 s)
25. `chop the axe with the log` (318.7-324.2 s)
26. `sweep the half log 176 and half log 176 off the driveway` (324.2-328.0 s)
27. `place the axe on the driveway` (328.0-334.2 s)

Mean duration per skill in this task: chop 8.3 s, move to 14.4 s, pick up from 16.9 s, place on 14.1 s, push to 4.8 s, sweep off 5.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the log` | 922 |
| `pick up the log from the driveway` | 800 |
| `chop the axe with the log` | 800 |
| `place the log on the chopping block` | 799 |
| `move to the chopping block` | 793 |
| `sweep the half log 176 and half log 176 off the driveway` | 417 |
| `pick up the axe from the driveway` | 201 |
| `place the axe on the driveway` | 201 |
| `move to the axe` | 200 |
| `push the log to the driveway` | 152 |
| `push the half log 174 to the driveway` | 72 |
| `push the half log 175 to the driveway` | 71 |
| `push the half log 177 to the driveway` | 69 |
| `push the half log 176 to the driveway` | 66 |
| `push the half-log-176-0 to the driveway` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/44_chopping_wood.json`. Planner notes: `task_docs/notes/44_chopping_wood.md`.
