# 60 · Scrubbing Bathroom Floor

Task name `scrubbing_bathroom_floor`, task index 60.

> Use the scrub brush to scrub the bathroom floor until the floor is clean.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | bathroom |
| rooms loaded | bathroom_0, bathroom_1, garden_0 |
| human demo length | 105.1 s mean (3153 steps) |
| episode time limit | 157.7 s (4730 steps at 30 Hz) |
| human base travel | 5.3838 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00; ft10k@sulab1 Q=0.00 |
| demo video | https://www.youtube.com/embed/u9wtUgoB8o8 |

## Planner notes

**Tier:** D — one tool grasp, then a cleaning state change (`not covered`) that needs the brush swept over every dirt patch.

### Goal in plain words

- The bathroom_0 floor (`floors_mawnss_0`) must carry zero dirt particles at the end.
- One literal, one ground option. Q is all or nothing: 1.0 if every patch is gone, else 0.
- Only the scrub brush is in scope; no other tool is needed or scored.

### Q traps

- `not covered` on a visual system needs **every** particle removed; one missed patch keeps Q at 0 (PREDICATES §12).
- Dirt count per instance, from the 20 `*-tro_state.json` files: 1 to 7 particles (301: 6, 302: 2, 303: 3, 304: 4, 305: 5, 306: 3, 307: 7, 308: 7, 309: 6, 310: 3; dev 311: 4, 312: 1, 320: 1). The leaderboard set 301-310 averages ~4.6.
- Patches are spread over the whole room: relative to the floor origin, x from -2.25 to +2.1 m and y from -1.04 to +0.84 m. Instance 311 is unusually compact (all 4 within x -0.63 to 0.40, y 0.12 to 0.25), so a pass on 311 overstates 301-310.
- Particle meshes are scaled 1-3.8x per patch, so patches look different sizes, but removal is tested on the particle's centre point only (PREDICATES §12). Aim the brush at the centre of each patch.
- The scrub brush removes dirt "always" (no water needed; PREDICATES §12 table).
- Only a closed-loop test can say whether patches sampled near the bathtub, toilet or cabinet bases are reachable (unverified).

### Minimal plan

1. `move to the scrub brush` — brush centred in view on the floor; ~14 s.
2. `pick up the scrub brush from the floors` — gripper closed short of fully shut, brush off the floor; ~14 s.
3. `hand over the scrub brush` — brush in the other gripper, first gripper open; ~7 s. Every one of the 200 demos does this, so the wiping motion was learned with the brush in the receiving hand. Keep it.
4. `move to the floors` — base stopped with a visible dirt patch within arm reach in front; ~12 s.
5. `wipe the scrub brush` — brush head pressed to the floor and dragged across the patch; done when that patch is no longer visible; ~9 s.
6. Repeat 4-5 per remaining patch, nearest first.

Budget: ~35 s for steps 1-3, then ~21 s per patch. With the 157.7 s limit that allows about 5-6 patches at demo pace, so 7-patch instances (307, 308) are tight.

### What the demos do differently

- Demos do 1 to 7 wipes (708 wipes over 200 demos, 3.5 on average), with a `move to the floors` before most wipes.
- 42 wipe segments are labelled navigation: the human drove the base while wiping. Scrubbing while moving is in distribution.
- There are no extra objects or detours. The demo is already minimal.

### Hard parts and hacks

- **Removal geometry.** The brush has no `particleremover` meta link in its metadata, so the root link's visual AABB grown by 2 cm is the removal box (PREDICATES §12). The brush is forced to 0.156 x 0.048 x 0.024 m, so the box is about 0.20 x 0.09 m in plan. The patch centre must fall inside it, and the brush bottom must be within ~2 cm of the floor.
- The AABB is world-axis-aligned; a brush held at 45° has a larger plan box, which helps.
- **Brush grasp.** The forced width 0.048 m is over the 44 mm jaw span, so the grasp must close on a narrower part (the handle); unverified.
- **Seeing every patch.** Dirt is a flat decal on the floor. After each wipe, look at the whole floor before declaring done; patches behind the toilet or bathtub are easy to miss.
- **200-particle saturation** is irrelevant here (at most 7 particles).
- **Scripted option:** once the brush is held, a coded "lower to floor and raster a 0.3 x 0.3 m square" around a patch seen in RGB-D is legal and more reliable than hoping the VLA stroke crosses the centre.
- Every closed-loop run so far, including zero-shot and three fine-tunes, scored Q 0.00 on 311.

### Hints for the VLM

- Work only in bathroom_0 (bathtub, toilet, bottom cabinet, two tabletop sinks, two mirrors). bathroom_1 is also loaded and its floor is not the goal floor.
- The scrub brush is a small (~16 cm) brush lying on the bathroom floor, median 0.76 m from the start (0.23-2.7 m).
- Dirt is a visual particle system drawn on the floor surface (exact look not checked here).
- Done: no dirt patch visible anywhere on the bathroom_0 floor from a full look around the room.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered floor.n.01_1 dirt.n.02_1))` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (not 
                (covered ?floor.n.01_1 ?dirt.n.02_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `dirt.n.02_1` | particle system | dirt | - | - | - | - |
| `floor.n.01_1` | floors_mawnss_0 | floors / mawnss | bathroom_0 | floor, z -0.14 | 0.53 m (range 0.4-0.69) | no (fixed) |
| `scrub_brush.n.01_1` | scrub_brush_222 | scrub_brush / hsejyi | bathroom_0 | floor, z 0.01 | 0.76 m (range 0.23-2.7) | yes, spread 4.47 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bathroom"
 ],
 "house_single_floor": {
  "whitelist": {
   "scrub_brush.n.01": {
    "scrub_brush": {
     "hsejyi": [
      0.156,
      0.048,
      0.024
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
(covered floor.n.01_1 dirt.n.02_1)
(inroom floor.n.01_1 bathroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop scrub_brush.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 scrub_brush.n.01_1)
(touching scrub_brush.n.01_1 floor.n.01_1)
```

## What the human demos did

200 annotated demos. Length 103.38 s (range 35.53-188.53). Skills per demo 9.0 (range 4-19). 40 distinct skill orders; the most common one covers 20% of demos.

Most common skill counts per demo (20% of demos): move to x4, wipe hard x3, hand over x1, pick up from x1.

Representative demo `episode_00602640.json` (103.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the scrub brush` (0.0-14.0 s)
2. `pick up the scrub brush from the floors` (14.0-24.3 s)
3. `hand over the scrub brush` (24.3-30.0 s)
4. `move to the floors` (30.0-49.0 s)
5. `wipe the scrub brush` (49.0-55.0 s)
6. `move to the floors` (55.0-62.0 s)
7. `wipe the scrub brush` (62.0-68.0 s)
8. `move to the floors` (68.0-95.7 s)
9. `wipe the scrub brush` (95.7-103.4 s)

Mean duration per skill in this task: hand over 7.3 s, move to 12.2 s, pick up from 13.6 s, wipe hard 8.9 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `wipe the scrub brush` | 708 |
| `move to the floors` | 647 |
| `pick up the scrub brush from the floors` | 201 |
| `move to the scrub brush` | 200 |
| `hand over the scrub brush` | 200 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/60_scrubbing_bathroom_floor.json`. Planner notes: `task_docs/notes/60_scrubbing_bathroom_floor.md`.
