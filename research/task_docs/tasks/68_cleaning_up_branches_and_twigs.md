# 68 · Cleaning Up Branches And Twigs

Task name `cleaning_up_branches_and_twigs`, task index 68.

> Collect all of the branches and twigs from the garden and put them into the recycling bin.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, garage_0, kitchen_0, living_room_0 |
| human demo length | 417.6 s mean (12527 steps) |
| episode time limit | 626.4 s (18790 steps at 30 Hz) |
| human base travel | 40.8589 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.8 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/iztsNYYMpv0 |

## Planner notes

**Tier:** C — four large, bushy branches (0.63 m long) must go into a lidded bin 0.91 m tall, and they are scattered along a ~16 m garden strip.

### Goal in plain words

All four branches must end inside the recycling bin, and the bin must still stand on the garden floor. The lid is not in the goal; it can be left open.

### Q traps

- 5 literals. `ontop recycling_bin floor` is true at reset, so it never scores, but tipping or lifting the bin breaks success. Max partial Q = 4/5 = 0.8.
  - In every instance the bin root sits at z 0.47, the same height, which is consistent with the bin on the floor. This is inferred; there is no sim check.
- Result on 311 (ft40k): Q = 0.00.
- `inside` tests the branch's AABB centre against the bin's volume (PREDICATES §3). A branch lying across the rim, or across the open lid, does not count.
- **Capacity (derived):** the forced sizes are bin 0.684 × 0.588 × 0.912 m and branch 0.625 × 0.30 × 0.255 m. Four branches stacked flat are ~1.0 m high, taller than the bin.
  - The last branch's centre may end up above the volume. Drop branches in steeply or on end so they pack.
- Do not push the bin to the branches with the base: that risks tipping it (the ontop literal). Seven demos push it anyway.

### Minimal plan

1. `move to the recycling bin` ~29 s.
2. `open the lid of the recycling bin` — the lid is visibly up and the opening clear. ~37 s. The lid starts closed (joint_pos 0) in all 20 instances. The demos log 310 open-lid segments over 200 episodes, so a retry is common.
3. `move to the branch`, `pick up the branch from the floors` — the branch is lifted clear of the ground. ~29 + 23 s.
4. `move to the branch`, `pick up the branch from the floors` with the other hand, as in the demos. ~29 + 23 s.
5. `move to the recycling bin`, `place the branch in the recycling bin` ×2 — each branch drops below the rim. ~29 + 2 × 9 s.
6. Repeat steps 3-5 for the last two branches.
7. Skip `close the lid of the recycling bin`; it is not in the goal, and closing could lift a branch that pokes out.

Demo mean 418 s against a 626 s limit. The walking dominates: the demos cover 41 m of base travel.

### What the demos do differently

- They carry two branches per trip, one per hand. 62-72/200 follow exactly two-and-two.
- All 200 close the lid at the end. This is not needed.
- 7/200 push the bin toward the driveway.

### Hard parts and hacks

- **Branch grasp:** the whole branch is 0.63 × 0.30 × 0.26 m, so only a single twig or the stem can be gripped. Twig thickness is not in the metadata (unverified vs the 44 mm span). Grab near the stem so the branch does not swing into the bin rim.
- **Scatter:** branches and bin are placed along a strip at x -16 to +0.5, y -3 to +1.4. Their spread per object across instances is 14-16 m. Expect branches out of view at the start.
- **Lid:** the bin has three movable links but one joint. Opening it needs a grip on the lid edge. A lid that falls back shut blocks every insert.
- Tipping risk: carrying two 0.63 m branches spread wide at shoulder height. Keep them low while driving.
- A dropped branch that lands against the bin but outside it is common. Re-check after each place.

### Hints for the VLM

- The garden of house_double_floor_lower, along the strip y ≈ -3 to +1.5, x ≈ -16 to +0.5. There are many bushes (55) and trees (26); the task branches are loose, lying flat on the paved/grass ground at z ~0.05 m.
- The recycling bin is the only bin in the garden: 0.9 m tall, with a hinged lid (one joint).
- Done: four branches visible inside the bin opening, none on the ground or across the rim, and the bin upright.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside branch.n.02_4 recycling_bin.n.01_1)` | no | yes |
| `(inside branch.n.02_2 recycling_bin.n.01_1)` | no | yes |
| `(inside branch.n.02_1 recycling_bin.n.01_1)` | no | yes |
| `(inside branch.n.02_3 recycling_bin.n.01_1)` | no | yes |
| `(ontop recycling_bin.n.01_1 floor.n.01_1)` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
            (forall
                (?branch.n.02 - branch.n.02)
                (inside ?branch.n.02 ?recycling_bin.n.01_1)
            )
            (ontop ?recycling_bin.n.01_1 ?floor.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `floor.n.01_1` | floors_qadhjb_0 | floors / qadhjb | garden_0 | floor, z -0.15 | 5.52 m (range 1.06-7.91) | no (fixed) |
| `branch.n.02_1` | branch_178 | branch / ijgexf | garden_0 | floor, z 0.05 | 7.52 m (range 0.91-12.47) | yes, spread 14.46 m |
| `branch.n.02_2` | branch_177 | branch / ijgexf | garden_0 | floor, z 0.05 | 5.33 m (range 0.79-12.82) | yes, spread 15.59 m |
| `branch.n.02_3` | branch_176 | branch / ijgexf | garden_0 | floor, z 0.05 | 6.16 m (range 0.79-10.46) | yes, spread 15.28 m |
| `branch.n.02_4` | branch_175 | branch / ijgexf | garden_0 | floor, z 0.05 | 6.08 m (range 1.01-15.65) | yes, spread 16.29 m |
| `recycling_bin.n.01_1` | recycling_bin_174 | recycling_bin / nuoypc | garden_0 | low (0.25-0.6 m), z 0.47 | 5.97 m (range 1.26-14.87) | yes, spread 15.92 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garden"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "recycling_bin.n.01": {
    "recycling_bin": {
     "nuoypc": [
      0.684,
      0.588,
      0.912
     ]
    }
   },
   "branch.n.02": {
    "branch": {
     "ijgexf": [
      0.625,
      0.3,
      0.255
     ]
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 garden)
(ontop agent.n.01_1 floor.n.01_1)
(ontop branch.n.02_1 floor.n.01_1)
(ontop branch.n.02_2 floor.n.01_1)
(ontop branch.n.02_3 floor.n.01_1)
(ontop branch.n.02_4 floor.n.01_1)
(ontop recycling_bin.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching branch.n.02_1 floor.n.01_1)
(touching branch.n.02_2 floor.n.01_1)
(touching branch.n.02_3 floor.n.01_1)
(touching branch.n.02_4 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 branch.n.02_1)
(touching floor.n.01_1 branch.n.02_2)
(touching floor.n.01_1 branch.n.02_3)
(touching floor.n.01_1 branch.n.02_4)
(touching floor.n.01_1 recycling_bin.n.01_1)
(touching recycling_bin.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 417.6 s (range 257.33-556.0). Skills per demo 18.0 (range 16-20). 41 distinct skill orders; the most common one covers 26% of demos.

Most common skill counts per demo (30% of demos): move to x8, pick up from x4, place in x4, open lid x2, close lid x1.

Representative demo `episode_00682230.json` (396.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the recycling bin` (0.0-32.0 s)
2. `open the lid of the recycling bin` (32.0-77.0 s)
3. `move to the branch` (77.0-103.0 s)
4. `pick up the branch from the floors` (103.0-115.0 s)
5. `move to the branch` (115.0-130.0 s)
6. `pick up the branch from the floors` (130.0-140.0 s)
7. `move to the recycling bin` (140.0-165.7 s)
8. `place the branch in the recycling bin` (165.7-179.0 s)
9. `place the branch in the recycling bin` (179.0-191.0 s)
10. `move to the branch` (191.0-250.0 s)
11. `pick up the branch from the floors` (250.0-272.0 s)
12. `move to the branch` (272.0-286.0 s)
13. `pick up the branch from the floors` (286.0-308.0 s)
14. `move to the recycling bin` (308.0-363.0 s)
15. `place the branch in the recycling bin` (363.0-373.0 s)
16. `place the branch in the recycling bin` (373.0-387.0 s)
17. `close the lid of the recycling bin` (387.0-396.0 s)

Mean duration per skill in this task: close lid 10.0 s, move to 28.7 s, open lid 37.4 s, pick up from 23.0 s, place in 9.3 s, push to 26.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the branch from the floors` | 800 |
| `place the branch in the recycling bin` | 798 |
| `move to the branch` | 788 |
| `move to the recycling bin` | 729 |
| `open the lid of the recycling bin` | 310 |
| `close the lid of the recycling bin` | 200 |
| `push the recycling bin to the driveway` | 7 |
| `place the recycling bin in the recycling bin` | 1 |
| `open the lid of the branch` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/68_cleaning_up_branches_and_twigs.json`. Planner notes: `task_docs/notes/68_cleaning_up_branches_and_twigs.md`.
