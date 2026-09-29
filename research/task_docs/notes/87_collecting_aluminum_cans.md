## Planner notes

**Tier:** C — six pick-and-places into one ice bucket, but every can is 63-81 mm across (asset bboxes), wider than the 44 mm jaw span.

### Goal in plain words

All six soda cans must be inside the ice bucket. Three start on a bed and three on the bedroom floor. The cans are interchangeable. The bucket may be moved. Nothing else is checked.

### Q traps

- Six literals, each 1/6, all false at reset. Every can banks 1/6 independently.
- `inside` tests only the can's AABB centre against the bucket's fillable volume (PREDICATES §3). A can wedged upright on the rim does not count.
- The bucket (`ice_bucket/vlurir`, 0.34 x 0.41 x 0.39 m) is a single link. Knocking it over spills cans already scored; every literal is read at the final step.
- Six cans of 0.11-0.15 m height in a 0.34 x 0.41 m bucket: they fit side by side or stacked, but a late can can land on top of others with its centre above the rim (derived; inner volume not verified).

### Minimal plan

1. `move to the can of soda` then `pick up the can of soda from the floors` — can in one hand. ~18 s + 19 s.
2. `move to the can of soda` then `pick up the can of soda from the floors` (or `from the bed`) — second can in the other hand. ~18 s + 19 s.
3. `move to the ice bucket` — bucket in view at close range. ~18 s.
4. `place the can of soda in the ice bucket` twice — both cans dropped in, none on the rim. ~15 s each.
5. Repeat 1-4 twice more for the remaining four cans.

Budget: 510 s limit vs 340 s demo mean. Each two-can trip is about 110 s of skills.

### What the demos do differently

- 74% of demos follow the plan above: two cans per trip, three trips.
- No demo moves the bucket.

### Hard parts and hacks

- Grasp widths (asset bboxes, 6 different models): 0.063 x 0.063 x 0.114 m up to 0.081 x 0.081 x 0.130 m. No can fits the 44 mm span. Expect the grasp to fail unless the pull tab or rim registers; not verified.
- Three cans stand on `bed_kddswt_1` (top about 0.6 m); three stand on the floor (full trunk bend).
- The bucket starts on the floor, 0.9-5.6 m from the start, and moves up to 6.6 m between instances. Some floor cans start within 0.3 m of it (for example instance 304).
- Hack (unverified): pushing the bucket next to the floor cans shortens every trip; the bucket is too wide to grasp (no axis under 0.33 m).

### Hints for the VLM

- Scene hotel_suite_large, bedroom_0. Two beds; only the bed at y -0.29 (`bed_kddswt_1`) holds cans. The six cans are six different can models, so they look different.
- The ice bucket is the only bucket in the room.
- Done per literal: can visibly inside the bucket, top below the rim.
