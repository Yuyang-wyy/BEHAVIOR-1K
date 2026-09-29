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
