# 79 · Polishing Shoes

Task name `polishing_shoes`, task index 79.

> Use the scrub brush to polish both shoes until the stains are removed.

## At a glance

| item | value |
| --- | --- |
| scene | `hotel_suite_large` |
| rooms in the goal | bedroom |
| rooms loaded | bedroom_0, bathroom_0 |
| human demo length | 357.9 s mean (10737 steps) |
| episode time limit | 536.9 s (16106 steps at 30 Hz) |
| human base travel | 17.158 m |
| goal literals (best ground option) | 6 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.833 |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/bSCbEvVJykI |

## Planner notes

**Tier:** D — a cleaning transition (every dust particle on both shoes swept off with the scrub brush) on top of placing two shoes side by side at an ottoman. The shoes (86 x 91 mm cross-section) are wider than the 44 mm jaw span.

### Goal in plain words

Both shoes must be dust-free, next to each other, and both next to the same ottoman (either of the two). The scrub brush must end on its nightstand, where it starts. Either ottoman works; Q takes the better one.

### Q traps

- `ontop scrub_brush stand` is true at reset (brush z 0.46 on nightstand_maeowc_2 in all 20 instances). It never scores but blocks success if the brush is not put back. Max partial Q is 5/6.
- `not covered` needs every particle gone (PREDICATES §12). The dust system holds 40 particles in the template and in the instances, so about 20 per shoe (derived). One missed particle keeps the literal false.
- `scrub_brush.n.01` removes dust "always": no water or soap needed. Removal is by the brush's AABB + 2 cm (ADJACENCY, root link; the asset has no `particleremover` meta link).
- `nextto` thresholds (derived from asset bboxes, PREDICATES §5): shoe to shoe needs an AABB gap of about 4.6 cm or less. Shoe to ottoman allows about 15 cm.
- Keep both shoes on the floor. A shoe on the ottoman sits above its centre height, and the horizontal rays likely miss (derived).
- The rays must hit the ottoman from the shoe's centre height (~4.5 cm). Whether the ottoman has open legs at that height is not verified. Pushing the shoe against the ottoman's side is the safe choice.
- Cleaning before placing is not required: `not covered` and `nextto` are independent. But brushing a placed shoe can shove it out of `nextto`; re-check both at the end.

### Minimal plan

1. `move to the scrub brush` — brush on the nightstand in view. ~20 s.
2. `pick up the scrub brush from the nightstand` — brush in hand (handle is 24 mm thick). ~24 s.
3. `move to the shoe` — shoe on the floor in view. ~20 s.
4. `wipe the shoe` — brush passes over every side of the shoe; no dust specks visible. ~34 s. Demo humans hold the shoe in the other hand (`pick up the shoe from the floors`, `hand over the scrub brush` first); brushing it on the floor is the untested alternative.
5. `move to the bed` then `place the shoe on the floors` — shoe on the floor touching the ottoman at the foot of a bed. ~20 s + 23 s.
6. Repeat 3-5 for the second shoe, placed within a few cm of the first, both against the same ottoman.
7. `move to the nightstand` then `place the scrub brush on the nightstand` — brush resting on the nightstand top. ~20 s + 23 s.

Budget: 537 s limit vs 358 s demo mean. Enough for one extra wipe pass per shoe.

### What the demos do differently

- 57% follow one order: brush, hand-over, then per shoe pick up, wipe, carry to the bed, place on the floor; then return the brush.
- `move to the bed` is the demo word for walking to the ottoman at the foot of the bed.
- 56 segments use `place on next to the shoe with the floors`. It is an odd, ungrammatical string; use `place the shoe on the floors`.
- The demo `hand over the scrub brush` moves the brush to the other hand so one hand can hold the shoe.

### Hard parts and hacks

- The shoe (asset bbox 0.239 x 0.086 x 0.091 m) is wider than 44 mm on both short axes. Picking it up may fail; the heel collar might fit but that is unverified. Pushing the shoe along the floor to the ottoman needs no grasp.
- Full coverage is the hard part: the brush's removal box (about 0.20 x 0.09 x 0.06 m, from the forced 0.156 x 0.048 x 0.024 size) must reach the sides and toe of the shoe, not just the top.
- The shoes start up to 6.9 m from the robot and anywhere in the bedroom. The ottomans are fixed in every instance at (0.14, -2.54) and (0.14, -0.28): the foot of each bed.
- Scripted shortcut (unverified): keep the brush moving over the shoe from several sides until the time limit. Success ends the episode the moment all six literals hold, so extra sweeping costs nothing.

### Hints for the VLM

- Room: bedroom_0 of hotel_suite_large. Two beds side by side, each with a long ottoman bench (1.47 m) across its foot.
- The brush is a small (16 cm) brush on nightstand_maeowc_2 at (-1.97, 0.82), beside the head of the bed at y -0.29. There are three identical nightstands; it must go back on this one.
- The two shoes (category "walker") are the only footwear on the floor.
- Done: two clean shoes side by side, touching or nearly touching, pressed against one ottoman; brush back on its nightstand.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop scrub_brush.n.01_1 stand.n.04_1)` | yes | never (already true) |
| `(not covered shoe.n.01_1 dust.n.01_1))` | no | yes |
| `(not covered shoe.n.01_2 dust.n.01_1))` | no | yes |
| `(nextto shoe.n.01_1 shoe.n.01_2)` | no | yes |
| `(nextto shoe.n.01_1 footstool.n.01_2)` | no | yes |
| `(nextto shoe.n.01_2 footstool.n.01_2)` | no | yes |

The goal has 2 ground options (6 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal
        (and
            (ontop scrub_brush.n.01_1 stand.n.04_1)
            (not
                (covered ?shoe.n.01_1 ?dust.n.01_1)
            )
            (not
                (covered ?shoe.n.01_2 ?dust.n.01_1)
            )
            (nextto ?shoe.n.01_1 ?shoe.n.01_2)
            (exists
                (?footstool.n.01 - footstool.n.01)
                (and
                    (nextto ?shoe.n.01_1 ?footstool.n.01)
                    (nextto ?shoe.n.01_2 ?footstool.n.01)
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
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `shoe.n.01_1` | walker_44 | walker / uewtgk | bedroom_0 | floor, z 0.03 | 2.46 m (range 0.98-6.32) | yes, spread 8.22 m |
| `shoe.n.01_2` | walker_43 | walker / pmypfd | bedroom_0 | floor, z 0.03 | 2.09 m (range 0.66-6.87) | yes, spread 8.13 m |
| `scrub_brush.n.01_1` | scrub_brush_42 | scrub_brush / hsejyi | bedroom_0 | low (0.25-0.6 m), z 0.46 | 3.15 m (range 1.27-5.35) | yes, spread 0.59 m |
| `stand.n.04_1` | nightstand_maeowc_2 | nightstand / maeowc | bedroom_0 | floor, z 0.22 | 3.26 m (range 1.27-5.4) | no (fixed) |
| `footstool.n.01_1` | ottoman_hnmndv_0 | ottoman / hnmndv | bedroom_0 | low (0.25-0.6 m), z 0.29 | 2.26 m (range 0.99-4.43) | no |
| `footstool.n.01_2` | ottoman_hnmndv_1 | ottoman / hnmndv | bedroom_0 | low (0.25-0.6 m), z 0.29 | 2.17 m (range 0.8-3.41) | no |
| `floor.n.01_1` | floors_nwjrkc_0 | floors / nwjrkc | bedroom_0 | floor, z -0.14 | 2.12 m (range 1.09-3.62) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom"
 ],
 "hotel_suite_large": {
  "whitelist": {
   "scrub_brush.n.01": {
    "scrub_brush": {
     "hsejyi": [
      0.156,
      0.048,
      0.024
     ]
    }
   },
   "shoe.n.01": {
    "walker": {
     "pmypfd": null,
     "uewtgk": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(covered shoe.n.01_1 dust.n.01_1)
(covered shoe.n.01_2 dust.n.01_1)
(inroom floor.n.01_1 bedroom)
(inroom footstool.n.01_1 bedroom)
(inroom footstool.n.01_2 bedroom)
(inroom stand.n.04_1 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop scrub_brush.n.01_1 stand.n.04_1)
(ontop shoe.n.01_1 floor.n.01_1)
(ontop shoe.n.01_2 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 shoe.n.01_1)
(touching floor.n.01_1 shoe.n.01_2)
(touching scrub_brush.n.01_1 stand.n.04_1)
(touching shoe.n.01_1 floor.n.01_1)
(touching shoe.n.01_2 floor.n.01_1)
(touching stand.n.04_1 scrub_brush.n.01_1)
```

## What the human demos did

200 annotated demos. Length 353.63 s (range 243.1-525.4). Skills per demo 15.0 (range 14-21). 16 distinct skill orders; the most common one covers 57% of demos.

Most common skill counts per demo (57% of demos): move to x6, pick up from x3, place on x3, wipe hard x2, hand over x1.

Representative demo `episode_00790310.json` (344.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the scrub brush` (0.0-14.0 s)
2. `pick up the scrub brush from the nightstand` (14.0-37.0 s)
3. `hand over the scrub brush` (37.0-47.0 s)
4. `move to the shoe` (47.0-50.0 s)
5. `pick up the shoe from the floors` (50.0-66.7 s)
6. `wipe the shoe` (66.7-97.0 s)
7. `move to the bed` (97.0-130.0 s)
8. `place the shoe on the floors` (130.0-163.0 s)
9. `move to the shoe` (163.0-190.0 s)
10. `pick up the shoe from the floors` (190.0-208.0 s)
11. `wipe the shoe` (208.0-254.0 s)
12. `move to the bed` (254.0-272.0 s)
13. `place the shoe on the floors` (272.0-298.0 s)
14. `move to the nightstand` (298.0-327.0 s)
15. `place the scrub brush on the nightstand` (327.0-344.0 s)

Mean duration per skill in this task: hand over 14.7 s, move to 20.0 s, pick up from 23.9 s, place on 23.4 s, place on next to 28.1 s, push to 20.0 s, wipe hard 33.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `pick up the shoe from the floors` | 436 |
| `move to the shoe` | 435 |
| `wipe the shoe` | 400 |
| `move to the bed` | 389 |
| `place the shoe on the floors` | 370 |
| `move to the scrub brush` | 200 |
| `pick up the scrub brush from the nightstand` | 200 |
| `hand over the scrub brush` | 200 |
| `move to the nightstand` | 200 |
| `place the scrub brush on the nightstand` | 200 |
| `place on next to the shoe with the floors` | 56 |
| `move to the floors` | 10 |
| `place on next to the shoe with the bed` | 4 |
| `place the shoe on the bed` | 3 |
| `place the floors on the bed` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/79_polishing_shoes.json`. Planner notes: `task_docs/notes/79_polishing_shoes.md`.
