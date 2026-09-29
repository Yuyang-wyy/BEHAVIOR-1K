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
