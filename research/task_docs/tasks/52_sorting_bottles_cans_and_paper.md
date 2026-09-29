# 52 · Sorting Bottles Cans And Paper

Task name `sorting_bottles_cans_and_paper`, task index 52.

> Sort the recyclables into separate containers: put the bottles together in one bucket, the cans together in another bucket, and the newspaper and magazine together in a third bucket.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | kitchen_0, corridor_0, garden_0, living_room_0 |
| human demo length | 342.1 s mean (10263 steps) |
| episode time limit | 513.2 s (15395 steps at 30 Hz) |
| human base travel | 26.7573 m |
| goal literals (best ground option) | 16 |
| literals already true at start (inferred) | 10 |
| max Q short of full success | 0.375 |
| ground goal options | 6 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.06; ft40k@local Q=0.06 |
| demo video | https://www.youtube.com/embed/h8-XZ85UxSU |

## Planner notes

**Tier:** C. It is pick-and-place into buckets, but the can body (76 mm) and the wine bottle body (67 mm) are wider than the 44 mm jaw span. The newspaper and magazine lie flat and can only be pinched at an edge.

### Goal in plain words

- Both wine bottles must end up in one bucket, both cans in a second bucket, and the newspaper and magazine in a third bucket.
- Which physical bucket plays which role is free: there are 6 ground options (3! assignments), and Q takes the best one.
- The three roles need three different buckets. Mixing classes breaks success. A can in the bottle bucket, a bottle in the can bucket, or either of them in the paper bucket is a failure.
- The two bottles must share a bucket (`forall`). So must the two cans. Splitting a pair over two buckets fails that pair.
- The buckets: `ice_bucket_86` and `ice_bucket_84` (vlurir, 0.34 x 0.41 x 0.39 m, from asset metadata `bbox_size`), and `bucket_85` (bdhvnt, forced to 0.5 x 0.625 x 0.52 m by custom_lists). All three are on the kitchen floor.

### Q traps

- 10 of the 16 literals are `not inside` literals that are already true at reset, since nothing starts in a bucket (`:init`, template positions). They never score. The best partial Q is 6/16 = 0.375. Only full success reaches 1.0.
- Breaking a `not inside` literal (for example a can dropped into the bottle bucket) costs no partial Q, but it blocks success until that item is taken out again.
- `inside` checks only the item's AABB centre (PREDICATES §3). The newspaper is 0.29 x 0.39 m. Dropped flat onto an ice bucket's 0.34 x 0.41 m top, it can rest on the rim with its centre above the volume, which does not count. Use the big bdhvnt bucket for the papers, as all 200 demos do.
- Partial Q reads only the final state. A bucket that gets knocked over and spills loses every item in it.
- Whether the ice bucket (vlurir) has a runtime fillable volume is unverified. Its metadata lists only `base_link`, but PREDICATES §2 says metadata cannot answer this. The demos put bottles and cans in it 798 times.
- Closed-loop ft40k on instance 311 scored Q = 0.0625, which is 1 of the 16 literals.

### Minimal plan

The skill sentences below are copied from the demo prompts. Both hands can each carry one item, as in the representative demo. Budgets use the task means: move to 15.7 s, pick up 12.0 s, place in 12.4 s, push to 20.1 s.

1. `move to the can of soda`, then `pick up the can of soda from the floors`. Done when that gripper stops short of fully closed and the can has left the floor in the image. About 28 s.
2. `move to the wine bottle`, then `pick up the wine bottle from the floors` with the other hand. Same check. About 28 s.
3. `move to the ice bucket`, then `place the wine bottle in the ice bucket`. Done when the gripper is open and the bottle is below the bucket rim in depth. About 28 s. Remember which ice bucket this was. It is now the bottle bucket.
4. `move to the ice bucket` (the other one), then `place the can of soda in the ice bucket`. Same check. About 28 s.
5. `move to the wine bottle`, then `pick up the wine bottle from the bar`. `move to the can of soda`, then `pick up the can of soda from the bar`. About 56 s.
6. Put the bottle into the bottle bucket and the can into the can bucket: `move to the ice bucket`, then `place the wine bottle in the ice bucket` (and the same for the can). About 56 s.
7. `move to the newspaper`, then `push the newspaper to the bar`. Done when the paper visibly overhangs the bar edge. Then `pick up the newspaper from the bar`. About 48 s.
8. `move to the magazine`, then `push the magazine to the bar`, then `pick up the magazine from the bar`. About 48 s.
9. `move to the bucket`, then `place the magazine in the bucket` and `place the newspaper in the bucket`. Done when both are inside the tall bucket and neither is draped over the rim. About 40 s.

That is about 360 s against a 513 s limit. The plan is the same length as the demos, because every demo step affects the goal.

### What the demos do differently

- The bucket roles never vary. Bottles and cans go into the ice buckets 399 times each, and the papers go into `bucket` 200 and 199 times. Keep that assignment.
- The class order varies. The most common orders are bottles, cans, papers (69 demos) and cans, bottles, papers (51). Papers go first in 56 demos. The order does not matter for the goal.
- The humans usually carry a bottle and a can together, one per hand, and drop them into different ice buckets.
- About 9 demos pick up and move a bucket (`pick up the bucket from the floors`, `place the bucket on the floors`). This is not needed. Moving a loaded bucket risks spilling it.
- 185 to 192 demos push each paper item to the bar edge before picking it up. That push is the grasp enabler (see below). It is not an extra step.

### Hard parts and hacks

- Grasp width is the main risk. The can is 76 mm across and the bottle body 67 mm (asset `bbox_size`), both more than the 44 mm span. The bottle neck is narrower, but its width is unverified. Pinching the bottle by the neck is the best bet. How the demos grasp the can is unverified.
- Newspaper and magazine: the newspaper is forced to 0.29 x 0.39 x 0.03 m by custom_lists, and the magazine is 0.27 x 0.21 x 0.011 m per asset `bbox_size`. They can be grasped only at an edge that overhangs the bar. So use `push ... to the bar` to slide the item past the edge, then pinch it. This is a reusable hack for any flat item lying on a counter.
- Distances are long. The robot start varies by up to 6 m across instances, and objects move by up to 8 m. The human base travel is 26.8 m. Rotation odometry drifts, so the planner should re-find the buckets visually instead of dead-reckoning.
- Ice buckets are 0.39 m tall and sit on the floor. Dropping from above the rim is fine, because a floating or held item with its centre in the volume already counts.
- A realistic VLA failure is putting the can into the same ice bucket as the bottles, since both prompts say `the ice bucket`. The planner must pick the target bucket itself and aim the `move to` at it.

### Hints for the VLM

- All task objects are in `kitchen_0`. The support is `bar_egwapq_0` (items at z of about 0.9 m). There is a second, distractor bar (`bar_byvbuc_0`) and a breakfast table in the same kitchen. There are no distractor buckets, bottles or cans in the kitchen.
- At start, one bottle and one can are on the floor. The other bottle, the other can, the newspaper and the magazine are on the bar.
- The two ice buckets look identical. Tell them apart by position, and record which holds the bottles as soon as the first item goes in.
- `bucket_85` is visibly larger than the ice buckets (0.52 m tall vs 0.39 m). It is the paper bucket.
- Done looks like this: nothing left on the bar or the floor, each ice bucket holding one class only, and both paper items inside the big bucket.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(inside wine_bottle.n.01_1 bucket.n.01_3)` | no | yes |
| `(inside wine_bottle.n.01_2 bucket.n.01_3)` | no | yes |
| `(not inside can__of__soda.n.01_1 bucket.n.01_3))` | yes | never (already true) |
| `(not inside newspaper.n.03_1 bucket.n.01_3))` | yes | never (already true) |
| `(not inside magazine.n.02_1 bucket.n.01_3))` | yes | never (already true) |
| `(inside can__of__soda.n.01_1 bucket.n.01_1)` | no | yes |
| `(inside can__of__soda.n.01_2 bucket.n.01_1)` | no | yes |
| `(not inside wine_bottle.n.01_1 bucket.n.01_1))` | yes | never (already true) |
| `(not inside newspaper.n.03_1 bucket.n.01_1))` | yes | never (already true) |
| `(not inside magazine.n.02_1 bucket.n.01_1))` | yes | never (already true) |
| `(not inside can__of__soda.n.01_1 bucket.n.01_2))` | yes | never (already true) |
| `(not inside can__of__soda.n.01_2 bucket.n.01_2))` | yes | never (already true) |
| `(not inside wine_bottle.n.01_1 bucket.n.01_2))` | yes | never (already true) |
| `(not inside wine_bottle.n.01_2 bucket.n.01_2))` | yes | never (already true) |
| `(inside newspaper.n.03_1 bucket.n.01_2)` | no | yes |
| `(inside magazine.n.02_1 bucket.n.01_2)` | no | yes |

The goal has 6 ground options (16 literals x6); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (exists
                (?bucket.n.01 - bucket.n.01)
                (and
                    (forall
                        (?wine_bottle.n.01 - wine_bottle.n.01)
                        (inside ?wine_bottle.n.01 ?bucket.n.01)
                    )
                    (not
                        (inside ?can__of__soda.n.01_1 ?bucket.n.01)
                    )
                    (not
                        (inside ?newspaper.n.03_1 ?bucket.n.01)
                    )
                    (not
                        (inside ?magazine.n.02_1 ?bucket.n.01)
                    )
                )
            )
            (exists
                (?bucket.n.01 - bucket.n.01)
                (and
                    (forall
                        (?can__of__soda.n.01 - can__of__soda.n.01)
                        (inside ?can__of__soda.n.01 ?bucket.n.01)
                    )
                    (not
                        (inside ?wine_bottle.n.01_1 ?bucket.n.01)
                    )
                    (not
                        (inside ?newspaper.n.03_1 ?bucket.n.01)
                    )
                    (not
                        (inside ?magazine.n.02_1 ?bucket.n.01)
                    )
                )
            )
            (exists
                (?bucket.n.01 - bucket.n.01)
                (and
                    (forall
                        (?can__of__soda.n.01 - can__of__soda.n.01)
                        (not
                            (inside ?can__of__soda.n.01 ?bucket.n.01)
                        )
                    )
                    (forall
                        (?wine_bottle.n.01 - wine_bottle.n.01)
                        (not
                            (inside ?wine_bottle.n.01 ?bucket.n.01)
                        )
                    )
                    (inside ?newspaper.n.03_1 ?bucket.n.01)
                    (inside ?magazine.n.02_1 ?bucket.n.01)
                )
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `bucket.n.01_1` | ice_bucket_86 | ice_bucket / vlurir | kitchen_0 | floor, z 0.19 | 2.4 m (range 0.72-5.33) | yes, spread 7.48 m |
| `bucket.n.01_2` | bucket_85 | bucket / bdhvnt | kitchen_0 | low (0.25-0.6 m), z 0.26 | 2.65 m (range 0.82-5.1) | yes, spread 6.38 m |
| `bucket.n.01_3` | ice_bucket_84 | ice_bucket / vlurir | kitchen_0 | floor, z 0.19 | 3.69 m (range 0.92-6.21) | yes, spread 7.07 m |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.04 m (range 1.05-3.47) | no (fixed) |
| `wine_bottle.n.01_1` | wine_bottle_83 | wine_bottle / inkqch | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 3.21 m (range 1.0-7.52) | yes, spread 2.31 m |
| `wine_bottle.n.01_2` | wine_bottle_82 | wine_bottle / inkqch | kitchen_0 | floor, z 0.09 | 2.59 m (range 0.74-6.51) | yes, spread 7.58 m |
| `countertop.n.01_1` | bar_egwapq_0 | bar / egwapq | kitchen_0 | low (0.25-0.6 m), z 0.45 | 3.26 m (range 1.75-6.9) | no (fixed) |
| `can__of__soda.n.01_1` | can_of_soda_81 | can_of_soda / lugwcz | kitchen_0 | floor, z 0.06 | 2.29 m (range 0.56-5.71) | yes, spread 8.27 m |
| `can__of__soda.n.01_2` | can_of_soda_80 | can_of_soda / lugwcz | kitchen_0 | table/counter (0.6-1.1 m), z 0.95 | 3.36 m (range 0.93-6.95) | yes, spread 2.19 m |
| `newspaper.n.03_1` | newspaper_79 | newspaper / ukamcl | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 3.65 m (range 1.34-7.12) | yes, spread 2.04 m |
| `magazine.n.02_1` | magazine_78 | magazine / ehdwsd | kitchen_0 | table/counter (0.6-1.1 m), z 0.89 | 2.7 m (range 1.18-6.42) | yes, spread 2.06 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "kitchen"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "bucket.n.01": {
    "ice_bucket": {
     "vlurir": null
    },
    "bucket": {
     "bdhvnt": [
      0.5,
      0.625,
      0.517857
     ]
    }
   },
   "can__of__soda.n.01": {
    "can_of_soda": {
     "lugwcz": null
    }
   },
   "magazine.n.02": {
    "magazine": {
     "ehdwsd": null
    }
   },
   "newspaper.n.03": {
    "newspaper": {
     "ukamcl": [
      0.29,
      0.39,
      0.03
     ]
    }
   },
   "wine_bottle.n.01": {
    "wine_bottle": {
     "inkqch": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop bucket.n.01_1 floor.n.01_1)
(ontop bucket.n.01_2 floor.n.01_1)
(ontop bucket.n.01_3 floor.n.01_1)
(ontop can__of__soda.n.01_1 floor.n.01_1)
(ontop can__of__soda.n.01_2 countertop.n.01_1)
(ontop magazine.n.02_1 countertop.n.01_1)
(ontop newspaper.n.03_1 countertop.n.01_1)
(ontop wine_bottle.n.01_1 countertop.n.01_1)
(ontop wine_bottle.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching bucket.n.01_1 floor.n.01_1)
(touching bucket.n.01_2 floor.n.01_1)
(touching bucket.n.01_3 floor.n.01_1)
(touching can__of__soda.n.01_1 floor.n.01_1)
(touching can__of__soda.n.01_2 countertop.n.01_1)
(touching countertop.n.01_1 can__of__soda.n.01_2)
(touching countertop.n.01_1 magazine.n.02_1)
(touching countertop.n.01_1 newspaper.n.03_1)
(touching countertop.n.01_1 wine_bottle.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 bucket.n.01_1)
(touching floor.n.01_1 bucket.n.01_2)
(touching floor.n.01_1 bucket.n.01_3)
(touching floor.n.01_1 can__of__soda.n.01_1)
(touching floor.n.01_1 wine_bottle.n.01_2)
(touching magazine.n.02_1 countertop.n.01_1)
(touching newspaper.n.03_1 countertop.n.01_1)
(touching wine_bottle.n.01_1 countertop.n.01_1)
(touching wine_bottle.n.01_2 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 335.52 s (range 210.7-608.17). Skills per demo 24.0 (range 20-33). 156 distinct skill orders; the most common one covers 4% of demos.

Most common skill counts per demo (24% of demos): move to x9, pick up from x6, place in x6, push to x2.

Representative demo `episode_00520330.json` (368.0 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the can of soda` (0.0-16.7 s)
2. `pick up the can of soda from the floors` (16.7-31.0 s)
3. `move to the wine bottle` (31.0-49.8 s)
4. `pick up the wine bottle from the floors` (49.8-61.5 s)
5. `move to the ice bucket` (61.5-71.1 s)
6. `place the wine bottle in the ice bucket` (71.1-83.0 s)
7. `move to the ice bucket` (83.0-105.3 s)
8. `place the can of soda in the ice bucket` (105.3-119.0 s)
9. `move to the wine bottle` (119.0-143.7 s)
10. `pick up the wine bottle from the bar` (143.7-153.3 s)
11. `move to the can of soda` (153.3-159.7 s)
12. `pick up the can of soda from the bar` (159.7-167.2 s)
13. `move to the ice bucket` (167.2-182.1 s)
14. `place the wine bottle in the ice bucket` (182.1-192.0 s)
15. `move to the ice bucket` (192.0-211.0 s)
16. `place the can of soda in the ice bucket` (211.0-223.0 s)
17. `move to the newspaper` (223.0-246.2 s)
18. `push the newspaper to the bar` (246.2-281.4 s)
19. `pick up the newspaper from the bar` (281.4-299.5 s)
20. `move to the magazine` (299.5-308.1 s)
21. `push the magazine to the bar` (308.1-323.0 s)
22. `pick up the magazine from the bar` (323.0-329.4 s)
23. `move to the bucket` (329.4-346.5 s)
24. `place the magazine in the bucket` (346.5-356.1 s)
25. `place the newspaper in the bucket` (356.1-368.0 s)

Mean duration per skill in this task: hand over 5.8 s, move to 15.7 s, pick up from 12.0 s, place in 12.4 s, place on 6.5 s, push to 20.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the ice bucket` | 630 |
| `place the wine bottle in the ice bucket` | 399 |
| `place the can of soda in the ice bucket` | 399 |
| `move to the can of soda` | 365 |
| `move to the wine bottle` | 351 |
| `move to the bucket` | 257 |
| `pick up the wine bottle from the bar` | 202 |
| `pick up the newspaper from the bar` | 201 |
| `pick up the magazine from the bar` | 201 |
| `pick up the can of soda from the floors` | 200 |
| `place the newspaper in the bucket` | 200 |
| `place the magazine in the bucket` | 199 |
| `pick up the can of soda from the bar` | 198 |
| `pick up the wine bottle from the floors` | 197 |
| `push the magazine to the bar` | 192 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/52_sorting_bottles_cans_and_paper.json`. Planner notes: `task_docs/notes/52_sorting_bottles_cans_and_paper.md`.
