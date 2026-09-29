# 58 · Stacking Wood

Task name `stacking_wood`, task index 58.

> Stack all of the logs together on the driveway.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 531.3 s mean (15939 steps) |
| episode time limit | 797.0 s (23909 steps at 30 Hz) |
| human base travel | 85.9645 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 46656 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/8MDz0GuPlto |

## Planner notes

**Tier:** C — six 0.45 x 0.15 x 0.15 m logs spread across the garden, 0.15 m thick (far over the 44 mm jaw span), with long carries.

### Goal in plain words

- Every log must end touching at least one **other** log. That is all the goal says; no stack, no pile, no driveway literal.
- The `or` over partners gives 6^6 = 46656 ground options. Options that pair a log with itself (`touching log_1 log_1`) can never hold and are excluded from the option shown on the page. A log cannot touch itself: it is a single rigid link (`log/pepele` metadata: `base_link` only), so self-contact never appears in the contact matrix (derived).
- So the minimum is **three separate touching pairs**. Each log that touches another scores 1/6; one pair = 0.33, two pairs = 0.67.
- Touching is instantaneous contact on the last physics substep (PREDICATES §8). Logs resting against each other stay in contact; a log bounced a few mm away does not.

### Q traps

- No log touches another at reset: the closest pair in any public instance is 1.6 m apart.
- Placing a log on top of a log that then rolls off loses both literals. Side-by-side on the ground is more stable than stacking.
- A third log in a three-log group still scores as long as it touches one of them; a chain works.
- Knocking a finished pair apart while carrying the next log undoes it (final state only, §1).

### Minimal plan

Pair each log with its nearest neighbour instead of hauling all six to one pile. Optimal pairings on the 20 instances need carries of 1.6-16.7 m per pair (median ~6 m), versus spreads of 13-35 m between the farthest logs.

1. `move to the log` — done: one log centred low in the head camera, base stopped. ~41 s demo mean (includes long walks).
2. `pick up the log from the driveway` — done: log lifted off the ground, gripper not fully closed. ~13 s.
3. `move to the log` (the nearest other log) — ~41 s.
4. `place the log on the driveway next to the log` — done: the two logs visibly in contact side by side, gripper open. ~14 s.
5. Repeat 1-4 for the remaining four logs, always choosing the nearest unpaired log as the partner.

Human demo mean 531 s vs limit 797 s. Pairing cuts the carrying distance, so the plan should fit even with retries.

### What the demos do differently

- Humans carry two logs at once (one per hand, `pick up` twice before any place), then put them down together. 1199 picks over 200 demos.
- They build one pile on the driveway: `place the log on the driveway`, then `place the log on the driveway next to the log`, and later `place the log on the log` (208) to stack. Stacking is not required.
- `move to the driveway` (196) is a walk to the pile site; not needed if you pair logs where they lie.
- 24 distinct skill orders; human base travel 86 m on average.

### Hard parts and hacks

- Grasp: the log is 150 mm thick in every direction except length. That exceeds the ~44 mm assisted-grasp span, yet all 1199 demo picks were single-arm. Whether a policy grasp registers at eval is unverified; expect this to be the main failure (ft40k Q = 0 on instance 311).
- Fallback that needs no grasp: push one log against another with the gripper or base. Logs are cylinders and roll, so push them only over short distances. Useful when two logs are within ~2 m (instances 302, 303, 304, 305, 315, 317 and 320 have a pair at most 2.1 m apart).
- Two-hand carry halves the walking, but a log slipping from one hand mid-walk is lost time. Prefer one log at a time unless the time budget is short.
- Logs lie in the garden among 28 trees, 27 bushes, a boulder and garden chairs; the VLA may approach a tree trunk or the boulder instead of a log.
- Rotation odometry drifts over 80+ m of travel; re-find the partner log visually each time rather than by dead reckoning.

### Hints for the VLM

- Six identical short logs (0.45 m long, 0.15 m thick) lie on the driveway/garden ground of house_single_floor, garden_0. There are no other logs in the scene.
- Distractors: tree trunks, the boulder, a charcoal grill, a car and a recreational vehicle in the garden.
- Done for a log: it is in visible contact with another log (no daylight between them in RGB, depth continuous across the join).
- Done overall: all six logs belong to some touching group; three pairs is enough.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(touching log.n.01_2 log.n.01_1)` | no | yes |
| `(touching log.n.01_4 log.n.01_1)` | no | yes |
| `(touching log.n.01_3 log.n.01_1)` | no | yes |
| `(touching log.n.01_5 log.n.01_1)` | no | yes |
| `(touching log.n.01_6 log.n.01_1)` | no | yes |
| `(touching log.n.01_1 log.n.01_2)` | no | yes |

The goal has 46656 ground options (6 literals x46656); Q takes the best one, so any valid choice of container or partner object counts.

31031 ground options pair an object with itself (for example `nextto can_1 can_1`). Those can never hold, so the option shown above is the best one without them.

BDDL goal:

```lisp
(:goal
        (forall
            (?log.n.01 - log.n.01)
            (or
                (touching ?log.n.01 ?log.n.01_1)
                (touching ?log.n.01 ?log.n.01_2)
                (touching ?log.n.01 ?log.n.01_3)
                (touching ?log.n.01 ?log.n.01_4)
                (touching ?log.n.01 ?log.n.01_5)
                (touching ?log.n.01 ?log.n.01_6)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `log.n.01_1` | log_337 | log / pepele | garden_0 | floor, z 0.05 | 10.04 m (range 2.54-33.73) | yes, spread 33.27 m |
| `log.n.01_2` | log_336 | log / pepele | garden_0 | floor, z 0.05 | 13.32 m (range 0.84-23.11) | yes, spread 37.16 m |
| `log.n.01_3` | log_335 | log / pepele | garden_0 | floor, z 0.05 | 13.84 m (range 3.54-24.4) | yes, spread 29.63 m |
| `log.n.01_4` | log_334 | log / pepele | garden_0 | floor, z 0.05 | 7.97 m (range 1.05-30.21) | yes, spread 32.29 m |
| `log.n.01_5` | log_333 | log / pepele | garden_0 | floor, z 0.05 | 13.41 m (range 3.84-27.6) | yes, spread 36.67 m |
| `log.n.01_6` | log_332 | log / pepele | garden_0 | floor, z 0.05 | 13.21 m (range 1.71-30.94) | yes, spread 36.12 m |
| `driveway.n.01_1` | driveway_hmbdky_0 | driveway / hmbdky | garden_0 | floor, z -0.16 | 10.31 m (range 0.72-17.07) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garden"
 ],
 "house_single_floor": {
  "whitelist": {
   "log.n.01": {
    "log": {
     "pepele": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom driveway.n.01_1 garden)
(ontop agent.n.01_1 driveway.n.01_1)
(ontop log.n.01_1 driveway.n.01_1)
(ontop log.n.01_2 driveway.n.01_1)
(ontop log.n.01_3 driveway.n.01_1)
(ontop log.n.01_4 driveway.n.01_1)
(ontop log.n.01_5 driveway.n.01_1)
(ontop log.n.01_6 driveway.n.01_1)
(touching agent.n.01_1 driveway.n.01_1)
(touching driveway.n.01_1 agent.n.01_1)
(touching driveway.n.01_1 log.n.01_1)
(touching driveway.n.01_1 log.n.01_2)
(touching driveway.n.01_1 log.n.01_3)
(touching driveway.n.01_1 log.n.01_4)
(touching driveway.n.01_1 log.n.01_5)
(touching driveway.n.01_1 log.n.01_6)
(touching log.n.01_1 driveway.n.01_1)
(touching log.n.01_2 driveway.n.01_1)
(touching log.n.01_3 driveway.n.01_1)
(touching log.n.01_4 driveway.n.01_1)
(touching log.n.01_5 driveway.n.01_1)
(touching log.n.01_6 driveway.n.01_1)
```

## What the human demos did

200 annotated demos. Length 524.05 s (range 284.4-931.17). Skills per demo 21.0 (range 18-22). 24 distinct skill orders; the most common one covers 29% of demos.

Most common skill counts per demo (46% of demos): move to x9, pick up from x6, place on x3, place on next to x3.

Representative demo `episode_00581830.json` (498.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the log` (0.0-41.0 s)
2. `pick up the log from the driveway` (41.0-51.0 s)
3. `move to the log` (51.0-69.0 s)
4. `pick up the log from the driveway` (69.0-79.0 s)
5. `move to the driveway` (79.0-103.0 s)
6. `place the log on the driveway` (103.0-113.0 s)
7. `place the log on the driveway next to the log` (113.0-122.0 s)
8. `move to the log` (122.0-181.0 s)
9. `pick up the log from the driveway` (181.0-191.0 s)
10. `move to the log` (191.0-210.0 s)
11. `pick up the log from the driveway` (210.0-220.0 s)
12. `move to the log` (220.0-264.0 s)
13. `place the log on the driveway` (264.0-274.0 s)
14. `place the log on the driveway next to the log` (274.0-280.0 s)
15. `move to the log` (280.0-355.0 s)
16. `pick up the log from the driveway` (355.0-365.0 s)
17. `move to the log` (365.0-406.0 s)
18. `pick up the log from the driveway` (406.0-416.0 s)
19. `move to the log` (416.0-455.0 s)
20. `place the log on the log` (455.0-465.0 s)
21. `place the log on the log next to the log` (465.0-498.9 s)

Mean duration per skill in this task: move to 41.1 s, pick up from 12.6 s, place on 13.3 s, place on next to 13.7 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the log` | 1623 |
| `pick up the log from the driveway` | 1199 |
| `place the log on the driveway next to the log` | 483 |
| `place the log on the driveway` | 418 |
| `place the log on the log` | 208 |
| `move to the driveway` | 196 |
| `place the log on the log next to the log` | 90 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/58_stacking_wood.json`. Planner notes: `task_docs/notes/58_stacking_wood.md`.
