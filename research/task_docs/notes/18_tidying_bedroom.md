## Planner notes

**Tier:** B — two sandals (0.24 x 0.09 x 0.03 m, flat on the floor) and one hardback (0.19 x 0.13 x 0.02 m, flat on the bed) in one room. All three models scored 0.67 on instance 311, so at least two literals are reachable with the current policy.

### Goal in plain words

Sandal 1 (`sandal_190`) must be next to the bed, and sandal 2 (`sandal_189`) must be next to sandal 1.
The book must rest on either nightstand (2 ground options, Q takes the better one).
The two sandals are NOT interchangeable in the literals: `sandal_190` is the one that must be by the bed, and `sandal_189` must be by `sandal_190`.
Nothing has to be closed.

### Q traps

- 3 literals, all inferred False at reset. Max partial Q 1.0.
- Estimated from instance poses and asset bboxes (AABB gap vs the L/6 threshold, PREDICATES §5; ray test not checked): in instance 305 `sandal_190` starts 0.24 m from the bed, under its 0.29 m threshold, so `nextto sandal_190 bed` is probably already true there and would never score. In 306 the gap (0.287 m) is on the threshold. In 311 it is 0.46 m, so it is False.
- `nextto sandal_189 sandal_190` is a small-small pair: the AABB gap must be under about 5 cm (L/6 = 0.044-0.054 m across instances). Placing both "next to the bed" with a hand-width gap fails this literal. Put the second sandal practically touching the first.
- `nextto sandal bed` allows up to ~0.29 m gap, but the height term counts: a sandal on the floor beside the 0.8 m bed is fine because the AABBs overlap in z.
- The book on a nightstand needs its centre over the top and contact (PREDICATES §4). A table lamp stands on each nightstand; the book must not rest on the lamp base.

### Minimal plan

Everything is in bedroom_0, 0.4-4.3 m from the start.

1. `move to the sandal` — a sandal centred in view on the floor. ~27 s.
2. `pick up the sandal from the floors` — sandal off the floor in one gripper. ~36 s.
3. `move to the sandal`, `pick up the sandal from the floors` — second sandal in the other gripper. ~27 s + 36 s.
4. `move to the bed` — base stopped beside the bed. ~27 s.
5. `place the sandal on the floors next to the left bed` — place `sandal_190` first, on the floor within ~0.25 m of the bed side. ~23 s.
6. `place the sandal on the floors next to the left bed` — place `sandal_189` touching `sandal_190` (gap < 5 cm). ~23 s. `place the sandal on the floors next to the left sandal` exists (3 demos) and states the true requirement; it is rarer in training.
7. `move to the hardback` — book on the bed in view. ~27 s.
8. `push the hardback to the to_the_edge_of bed` — book overhanging the mattress edge. ~53 s.
9. `pick up the hardback from the bed` — book lifted clear. ~36 s.
10. `move to the nightstand`, `place the hardback on the nightstand` — book flat on the top, beside the lamp. ~27 s + 28 s.

Budget: about 375 s against a 552 s limit.

### What the demos do differently

- All 200 demos carry both sandals at once and place them both with the "next to the left bed" sentence. They do not distinguish which sandal goes first. The planner must: `sandal_190` goes nearest the bed.
- 199/200 demos push the book to the bed edge before picking it up. This is the trained trick for a flat book; keep it.
- Every demo uses `nightstand_wbxekb_0`; either nightstand scores.

### Hard parts and hacks

- Sandals lie flat: 0.09 m wide, 0.034 m tall. A straddling grasp must be across the height (sole to strap) or on a strap; unverified which registers.
- The book is 0.021 m thick lying flat. It is only graspable after it overhangs the bed edge (the push step).
- The sandal-sandal 5 cm tolerance is the likely lost literal. Setting the second sandal down against the side of the first is the fix; a small `push the sandal to` nudge is not in the demos.

### Hints for the VLM

- The two sandals are different models (`tkfdsk` = `sandal_190`, `txkidl` = `sandal_189`); telling them apart in RGB needs a look at colour/shape at reset. Unverified which looks like which.
- The bedroom has one bed, two identical nightstands (each with a table lamp), a bench and a wall-mounted TV. The book lies on the bed.
- Done for the sandals: first sandal on the floor right beside the bed frame, second sandal side by side with it, no visible floor gap between them.
- Done for the book: lying flat on a nightstand top, not on the bed or floor.
