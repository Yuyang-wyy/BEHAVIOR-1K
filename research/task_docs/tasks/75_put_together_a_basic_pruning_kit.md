# 75 · Put Together A Basic Pruning Kit

Task name `put_together_a_basic_pruning_kit`, task index 75.

> Put the pruner and shears into the toolbox, then close the toolbox.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage |
| rooms loaded | garage_0, corridor_0, garden_0 |
| human demo length | 375.5 s mean (11264 steps) |
| episode time limit | 563.2 s (16896 steps at 30 Hz) |
| human base travel | 19.4443 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 2 |
| max Q short of full success | 0.5 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/UmGRVx-OCac |

## Planner notes

**Tier:** B — two small tools go into a lidded toolbox on the garage floor, all within ~3 m. The upright pruner is an easy grasp; the flat shears are not.

### Goal in plain words

The pruner and the shears must both end inside the toolbox, the toolbox must still rest on the garage floor, and its lid must be closed.

### Q traps

- 4 literals, but `ontop toolbox floor` and `not open toolbox` are true at reset and never score. **Max partial Q = 0.5**. Each tool inside is worth 0.25, and only full success gives 1.0.
- Result on 311 (ft40k): Q = 0.00.
- Leaving the lid open, or tipping the toolbox, blocks success without costing partial Q.
- `inside` uses the AABB centre (PREDICATES §3). The pruner is 0.23 m long and the box is 0.35 m tall. Lay it down inside so the closing lid does not push it up and out.
- Close the lid last and check it is flush (5 % rule, §6). A tool handle under the lid keeps it "open".

### Minimal plan

1. `move to the toolbox` ~24 s.
2. `open the lid of the toolbox` — lid visibly up. ~56 s, the slowest skill here. It starts closed (joint_pos 0).
3. `move to the shears`, `pick up the shears from the floors` ~24 + 38 s.
4. `move to the toolbox`, `place the shears in the toolbox` ~24 + 34 s.
5. `move to the pruner`, `pick up the pruner from the floors` ~24 + 38 s.
6. `move to the toolbox`, `place the pruner in the toolbox` ~24 + 34 s.
7. `close the lid of the toolbox` — lid flush. ~38 s.

Demo mean 376 s against a 563 s limit. All objects start 0.4-7 m from the robot.

### What the demos do differently

- All 200 follow this skeleton with the shears first. The two orders on the page differ only in an extra `move to`. Tool order does not matter for the goal.
- Humans walk back to the toolbox for each tool (6 `move to` in 53 % of demos). Picking both tools and walking once saves a trip, but with two loaded hands the lid close needs a free hand.

### Hard parts and hacks

- **Pruner** (`pruner_lucqrs`, native size 0.029 × 0.067 × 0.228 m) **stands upright** on the floor in every instance: its long axis is vertical, root z 0.10. A top-down grasp across the 29 mm side fits the jaws. It has a `slicer` blade link; that is irrelevant here.
- **Shears** are forced to 0.208 × 0.08 × 0.02 m and lie flat. The only thin dimension is the 20 mm thickness, which is vertical. Top-down straddling spans 80 mm, so it needs a side pinch or a grasp through a handle loop (unverified). This is the likely failure point.
- **Toolbox** (`toolbox_redmtl`, 0.26 × 0.61 × 0.35 m) has a hinged lid. Opening it took humans ~56 s. Its yaw varies per instance, so the lid hinge side changes.
- Floor-level picks (z 0.01-0.1 m) need a deep trunk bend.

### Hints for the VLM

- house_double_floor_lower garage_0, around the car. The toolbox is a 0.6 m long box on the floor with a lid.
- The pruner stands upright like a small post, ~23 cm tall. The shears lie flat on the floor.
- Done: both tools inside the box and the lid shut flat.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop toolbox.n.01_1 floor.n.01_1)` | yes | never (already true) |
| `(inside pruner.n.02_1 toolbox.n.01_1)` | no | yes |
| `(inside shears.n.01_1 toolbox.n.01_1)` | no | yes |
| `(not open toolbox.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal 
        (and 
            (ontop ?toolbox.n.01_1 ?floor.n.01_1) 
            (inside ?pruner.n.02_1 ?toolbox.n.01_1) 
            (inside ?shears.n.01_1 ?toolbox.n.01_1)
            (not
                (open ?toolbox.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `pruner.n.02_1` | pruner_61 | pruner / lucqrs | garage_0 | floor, z 0.1 | 2.61 m (range 0.91-5.23) | yes, spread 8.2 m |
| `floor.n.01_1` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 2.0 m (range 0.88-3.37) | no (fixed) |
| `shears.n.01_1` | shears_60 | shears / iizidc | garage_0 | floor, z 0.01 | 2.39 m (range 0.37-6.22) | yes, spread 6.7 m |
| `toolbox.n.01_1` | toolbox_59 | toolbox / redmtl | garage_0 | floor, z 0.08 | 3.03 m (range 0.84-6.94) | yes, spread 8.12 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garage"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "pruner.n.02": {
    "pruner": {
     "lucqrs": null
    }
   },
   "shears.n.01": {
    "shears": {
     "iizidc": [
      0.208,
      0.08,
      0.02
     ]
    }
   },
   "toolbox.n.01": {
    "toolbox": {
     "redmtl": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 garage)
(ontop agent.n.01_1 floor.n.01_1)
(ontop pruner.n.02_1 floor.n.01_1)
(ontop shears.n.01_1 floor.n.01_1)
(ontop toolbox.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 pruner.n.02_1)
(touching floor.n.01_1 shears.n.01_1)
(touching floor.n.01_1 toolbox.n.01_1)
(touching pruner.n.02_1 floor.n.01_1)
(touching shears.n.01_1 floor.n.01_1)
(touching toolbox.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 382.78 s (range 220.27-538.97). Skills per demo 12.0 (range 11-12). 2 distinct skill orders; the most common one covers 53% of demos.

Most common skill counts per demo (53% of demos): move to x6, pick up from x2, place in x2, close lid x1, open lid x1.

Representative demo `episode_00752840.json` (382.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the toolbox` (0.0-28.0 s)
2. `open the lid of the toolbox` (28.0-87.0 s)
3. `move to the shears` (87.0-114.0 s)
4. `pick up the shears from the floors` (114.0-147.0 s)
5. `move to the toolbox` (147.0-185.0 s)
6. `place the shears in the toolbox` (185.0-214.0 s)
7. `move to the pruner` (214.0-240.0 s)
8. `pick up the pruner from the floors` (240.0-269.0 s)
9. `move to the toolbox` (269.0-312.8 s)
10. `place the pruner in the toolbox` (312.8-337.0 s)
11. `move to the toolbox` (337.0-347.0 s)
12. `close the lid of the toolbox` (347.0-382.0 s)

Mean duration per skill in this task: close lid 38.1 s, move to 23.7 s, open lid 56.2 s, pick up from 37.5 s, place in 34.0 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the toolbox` | 706 |
| `open the lid of the toolbox` | 200 |
| `move to the shears` | 200 |
| `pick up the shears from the floors` | 200 |
| `place the shears in the toolbox` | 200 |
| `move to the pruner` | 200 |
| `pick up the pruner from the floors` | 200 |
| `place the pruner in the toolbox` | 200 |
| `close the lid of the toolbox` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/75_put_together_a_basic_pruning_kit.json`. Planner notes: `task_docs/notes/75_put_together_a_basic_pruning_kit.md`.
