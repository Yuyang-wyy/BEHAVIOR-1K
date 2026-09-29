## Planner notes

**Tier:** C — two storage boxes of 0.40 x 0.41 x 0.21 m each must be carried ~9 m and stacked. No dimension is under the 44 mm span, yet ft40k succeeded on instance 311 (Q 1.0 in 14103 steps, 470 s), so the boxes are graspable in practice. How the grasp registers (across a box wall, or bimanual) is unverified.

### Goal in plain words

One storage box must rest on the garage floor and the other box must rest on top of it.
The two boxes are interchangeable: either can be the bottom one (2 ground options, Q takes the better).
Nothing has to be closed afterwards; the corridor door may stay open.

### Q traps

- 2 literals per option, both False at reset. Max partial Q is 1.0.
- One box on the garage floor alone gives Q = 0.5 (what zs_pt50 reached on 311).
- Both boxes side by side on the garage floor still gives only 0.5. The stack is the second half.
- `ontop top bottom` needs the top box's AABB-centre x-y over the bottom box and direct contact (PREDICATES §4). A top box hanging half off the edge, or tipped against the bottom box while touching the floor, can fail.
- The bottom box must be on the garage floor, not on the corridor floor or the threshold.
- Knocking the bottom box while placing the top one can shift it; re-check both after release.

### Minimal plan

The robot starts in the garage, 0.7-3.7 m from the garage floor centre. The boxes are on the living-room floor, 5.3-13.3 m away. The garage-corridor door `door_bexenl_0` starts closed (template joint_pos ~0); every demo opens it first.

1. `move to the door`, `open the door of the door` — door swung open, corridor visible. ~60 s + 24 s.
2. `move to the storage box` — first box centred in view on the living-room floor. ~60 s.
3. `pick up the storage box from the floors` — box lifted clear of the floor; depth shows the gap. ~42 s.
4. `move to the floors` — base stopped inside the garage, clear floor ahead. ~60 s.
5. `place the storage box on the floors` — box on the garage floor, grippers open. ~33 s. Scores 1/2.
6. `move to the storage box`, `pick up the storage box from the floors` — second box lifted. ~60 s + 42 s.
7. `move to the storage box` — base stopped facing the first box in the garage. ~60 s.
8. `place the storage box on the storage box` — top box centred on the bottom box, grippers open. ~33 s. Success ends the episode.

Budget: about 475 s against a 730 s limit. This plan is exactly the demo plan; there is nothing to cut.

### What the demos do differently

- All 200 demos follow this plan. 111 carry `storage_box_80` first, 89 carry `storage_box_79` first; either works.
- No push, hand-over or re-grasp segments are annotated.

### Hard parts and hacks

- The boxes are large for the R1Pro: 0.40 m square. Carrying one box through the corridor doorway (door width unknown) with arms extended risks collisions and tipping (robot can tip with loads held high).
- Placing the top box needs the box lowered to ~0.21 m above the floor and centred; a misaligned drop slides it off.
- The long carry is the main time sink. If the first trip overruns ~250 s, bank the 0.5 and keep going only if time remains.

### Hints for the VLM

- The two storage boxes are identical closed boxes on the living-room floor; there are no other storage boxes in the living room or garage.
- Besides the boxes, the living room has one coffee table, a sofa, a shelf, a bottom cabinet and a fireplace.
- The garage has a car (fixed, large). Put the boxes on open floor away from the car, near the corridor door to shorten the second trip.
- Done: bottom box flat on the garage floor, top box sitting squarely on it, both upright, grippers away.
