# 88 · Rearrange Your Room

Task name `rearrange_your_room`, task index 88.

> Rearrange the room by putting the pillows on the bed, moving the chair next to the desk, and placing the tissue dispenser on the nightstand.

## At a glance

| item | value |
| --- | --- |
| scene | `hotel_suite_large` |
| rooms in the goal | bathroom, bedroom |
| rooms loaded | bedroom_0, bathroom_0 |
| human demo length | 428.5 s mean (12854 steps) |
| episode time limit | 642.7 s (19282 steps at 30 Hz) |
| human base travel | 24.028 m |
| goal literals (best ground option) | 3 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 8 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | not evaluated yet |
| demo video | https://www.youtube.com/embed/PuP9DeUF4K4 |

## Planner notes

**Tier:** C — three pick-and-places of wide objects: two pillows (0.49 x 0.33 x 0.09 m) and a tissue dispenser (0.10 x 0.19 x 0.17 m), none with an axis under 44 mm.

### Goal in plain words

Each bed must end with one pillow on it, and the tissue dispenser must rest on any stand. The pillows must go to **different** beds (`forpairs`). The stand can be any of four: the long low stand along the wall or one of the three nightstands. The chair in the task sentence is not in the goal.

### Q traps

- Three literals, each 1/3, all false at reset. Q takes the best of 8 ground options.
- `forpairs` pillow-bed needs a perfect matching. Both pillows on one bed score only 1 of the 2 pillow literals (max 2/3 with the dispenser).
- `ontop` needs the pillow's centre over the bed and nothing of the bed above it (PREDICATES §4). A headboard overhang is not verified; the middle of the mattress is safe.
- `push the chair to the desk` (in all 200 demos) earns nothing. Skip it.
- The fact page lists `stand.n.04_2..4` as "(runtime)". The instances resolve them to the three nightstands `nightstand_maeowc_0/1/2` at x -1.97, y -3.66 / -1.42 / 0.82, beside the bed heads. `stand.n.04_1` is `stand_dbskvf_0`, a 7.5 m long, 0.38 m high stand along the x 2.12 wall.

### Minimal plan

1. `move to the tissue dispenser` then `pick up the tissue dispenser from the armchair` — box lifted off the armchair. ~25 s + 41 s.
2. `move to the nightstand` then `place the tissue dispenser on the nightstand` — box standing on a stand top. ~25 s + 35 s. The long wall stand is closer (see hacks), but no demo prompt names it; closest trained wording is this one.
3. `move to the pillow` then `pick up the pillow from the floors` — pillow held. ~25 s + 41 s.
4. `move to the bed` then `place the pillow on the bed` — pillow lying on the first bed. ~25 s + 35 s.
5. Repeat 3-4 with the second pillow, placed on the **other** bed.

Budget: 643 s limit vs 429 s demo mean. Dropping the chair push saves about 55 s.

### What the demos do differently

- All 200 demos use one order: both pillows picked (one per hand), first pillow placed, chair pushed to the desk, second pillow placed, then the dispenser.
- Humans carry both pillows at once. Placing them on two different beds is required, though the prompt `place the pillow on the bed` does not say which.

### Hard parts and hacks

- Grasp widths (asset bboxes): pillow 0.49 x 0.327 x 0.089 m, lying flat on the floor; dispenser 0.10 x 0.191 x 0.168 m. Neither fits 44 mm. Expect grasp failures.
- The dispenser starts on `armchair_ybcnmu_0` at (1.63, -4.44). The long stand `stand_dbskvf_0` runs along x 2.12 from about y -4.46 to 3.08, so its end is roughly 0.5 m from the armchair (derived from poses and bbox). That is the shortest valid target; the nightstands are 3.6 m or more away.
- The pillows start anywhere on the bedroom floor, up to 6 m from the start and up to 7.7 m apart between instances.
- The beds (`bed_kddswt_0` at y -2.54, `bed_kddswt_1` at y -0.29) are 2.17 x 1.59 m, side by side with ottomans at their feet.

### Hints for the VLM

- Scene hotel_suite_large, bedroom_0. Two identical beds side by side; two identical pillows on the floor; a small tissue box on the armchair near the long wall stand.
- The long low stand under the wall TV counts as a stand; a TV above it is a separate object and does not block `ontop`.
- Done: one pillow on each bed, tissue box on a stand top.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(ontop tissue_dispenser.n.01_1 stand.n.04_1)` | no | yes |
| `(ontop pillow.n.01_2 bed.n.01_1)` | no | yes |
| `(ontop pillow.n.01_1 bed.n.01_2)` | no | yes |

The goal has 8 ground options (3 literals x8); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (exists
                (?stand.n.04 - stand.n.04)
                (ontop tissue_dispenser.n.01_1 ?stand.n.04)
            )
            (forpairs
                (?pillow.n.01 - pillow.n.01)
                (?bed.n.01 - bed.n.01)
                (ontop ?pillow.n.01 ?bed.n.01)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `floor.n.01_1` | floors_nwjrkc_0 | floors / nwjrkc | bedroom_0 | floor, z -0.14 | 2.34 m (range 0.91-3.32) | no (fixed) |
| `floor.n.01_2` | floors_kudtlk_0 | floors / kudtlk | bathroom_0 | floor, z -0.14 | 4.19 m (range 2.7-8.16) | no (fixed) |
| `pillow.n.01_1` | pillow_66 | pillow / ajpapo | bedroom_0 | floor, z 0.03 | 3.36 m (range 1.05-5.97) | yes, spread 7.15 m |
| `pillow.n.01_2` | pillow_65 | pillow / ajpapo | bedroom_0 | floor, z 0.03 | 2.49 m (range 0.86-5.36) | yes, spread 7.67 m |
| `bed.n.01_1` | bed_kddswt_1 | bed / kddswt | bedroom_0 | floor, z 0.18 | 2.43 m (range 2.07-4.15) | no (fixed) |
| `bed.n.01_2` | bed_kddswt_0 | bed / kddswt | bedroom_0 | floor, z 0.18 | 3.7 m (range 2.26-4.38) | no (fixed) |
| `armchair.n.01_1` | armchair_ybcnmu_0 | armchair / ybcnmu | bedroom_0 | low (0.25-0.6 m), z 0.37 | 4.78 m (range 0.98-6.17) | no |
| `tissue_dispenser.n.01_1` | tissue_dispenser_64 | tissue_dispenser / frdbld | bedroom_0 | low (0.25-0.6 m), z 0.49 | 4.65 m (range 0.9-6.07) | yes, spread 0.55 m |
| `stand.n.04_1` | stand_dbskvf_0 | stand / dbskvf | bedroom_0 | floor, z 0.16 | 2.01 m (range 1.11-3.45) | no (fixed) |
| `stand.n.04_2` | (runtime) | nightstand/stand | - | floor, z 0.22 | 3.11 m (range 2.2-5.47) | no |
| `stand.n.04_3` | (runtime) | nightstand/stand | - | floor, z 0.22 | 5.02 m (range 2.61-5.68) | no |
| `stand.n.04_4` | (runtime) | nightstand/stand | - | floor, z 0.22 | 3.53 m (range 2.87-3.86) | no |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom",
  "bathroom"
 ],
 "hotel_suite_large": {
  "whitelist": {
   "pillow.n.01": {
    "pillow": {
     "ajpapo": null
    }
   },
   "tissue_dispenser.n.01": {
    "tissue_dispenser": {
     "frdbld": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom armchair.n.01_1 bedroom)
(inroom bed.n.01_1 bedroom)
(inroom bed.n.01_2 bedroom)
(inroom floor.n.01_1 bedroom)
(inroom floor.n.01_2 bathroom)
(inroom stand.n.04_1 bedroom)
(inroom stand.n.04_2 bedroom)
(inroom stand.n.04_3 bedroom)
(inroom stand.n.04_4 bedroom)
(ontop agent.n.01_1 floor.n.01_1)
(ontop pillow.n.01_1 floor.n.01_1)
(ontop pillow.n.01_2 floor.n.01_1)
(ontop tissue_dispenser.n.01_1 armchair.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching armchair.n.01_1 tissue_dispenser.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 pillow.n.01_1)
(touching floor.n.01_1 pillow.n.01_2)
(touching pillow.n.01_1 floor.n.01_1)
(touching pillow.n.01_2 floor.n.01_1)
(touching tissue_dispenser.n.01_1 armchair.n.01_1)
```

## What the human demos did

200 annotated demos. Length 402.0 s (range 284.93-608.73). Skills per demo 14.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x7, pick up from x3, place on x3, push to x1.

Representative demo `episode_00882600.json` (402.7 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the pillow` (0.0-17.0 s)
2. `pick up the pillow from the floors` (17.0-55.0 s)
3. `move to the pillow` (55.0-73.0 s)
4. `pick up the pillow from the floors` (73.0-121.0 s)
5. `move to the bed` (121.0-134.0 s)
6. `place the pillow on the bed` (134.0-171.0 s)
7. `move to the chair` (171.0-209.0 s)
8. `push the chair to the desk` (209.0-241.0 s)
9. `move to the bed` (241.0-263.0 s)
10. `place the pillow on the bed` (263.0-300.0 s)
11. `move to the tissue dispenser` (300.0-321.0 s)
12. `pick up the tissue dispenser from the armchair` (321.0-360.0 s)
13. `move to the nightstand` (360.0-375.0 s)
14. `place the tissue dispenser on the nightstand` (375.0-402.7 s)

Mean duration per skill in this task: move to 24.5 s, pick up from 40.9 s, place on 34.5 s, push to 30.5 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the pillow` | 401 |
| `pick up the pillow from the floors` | 400 |
| `move to the bed` | 400 |
| `place the pillow on the bed` | 400 |
| `push the chair to the desk` | 200 |
| `move to the tissue dispenser` | 200 |
| `pick up the tissue dispenser from the armchair` | 200 |
| `move to the nightstand` | 200 |
| `place the tissue dispenser on the nightstand` | 200 |
| `move to the chair` | 199 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/88_rearrange_your_room.json`. Planner notes: `task_docs/notes/88_rearrange_your_room.md`.
