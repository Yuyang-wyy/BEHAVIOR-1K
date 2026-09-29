# 57 · Sweeping Garage

Task name `sweeping_garage`, task index 57.

> Use the broom to sweep the dirt from the garage floor until the floor is clean.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | garage |
| rooms loaded | garage_0, corridor_0 |
| human demo length | 149.1 s mean (4473 steps) |
| episode time limit | 223.7 s (6709 steps at 30 Hz) |
| human base travel | 19.0765 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/0bdsrbEeFEc |

## Planner notes

**Tier:** D — one tool pick (the broom), then a particle-removal state change over the whole garage floor.

### Goal in plain words

- Every dust particle and every sand particle on the garage floor (`floors_nbxnpk_0`) must be gone. Two literals, 0.5 each.
- Nothing else matters: the bucket is a distractor and does not need to be used or moved.
- One particle left keeps its literal False (PREDICATES §12). Dust and sand score independently, so clearing all dust but missing one sand grain gives Q = 0.5.

### Q traps

- Particle counts per public instance: dust 8-16, sand 7-15, 18-29 in total (read from the 20 `-tro_state.json` files).
- Particles are spread over the whole garage floor, about 6.7 m x 5.4 m around the floor origin (-5.37, 5.51). The farthest particle is 4.1-7.1 m from the start pose.
- No particle lies under the car's footprint in any instance (car `car_ssxsje_0` at (-4.43, 6.89), 5.05 x 2.15 m, checked against all 445 particles). You never need to reach under the car.
- The broom removes both systems: dust "always", sand "always" by the default condition (PREDICATES §12 table). No water or toggle needed.
- The 200-per-system removal limit is far above 29, so saturation is not a risk.

### Minimal plan

1. `move to the broom` — done: broom lying on the floor centred in view, base stopped. ~14 s.
2. `pick up the broom from the floors` — done: broom lifted, gripper closed short of fully closed. ~24 s (demo mean; slowest pick of the task).
3. `move to the dirt` — ~14 s.
4. `sweep the dirt` — done: no visible dust or sand spots on the floor in a full turn of the head camera. ~95 s demo mean.
5. If spots remain, repeat `move to the dirt` then `sweep the dirt` (2/200 demos did a second pass).

Demo mean 149 s vs limit 223.7 s: ~75 s slack for one extra pass.

### What the demos do differently

- 193/200 demos use exactly the 4 steps above. 3 demos use `move to the broom` / `sweep the broom` as the sweep prompt instead.
- The trained sweep prompt here is `sweep the dirt` (199 uses), not the tool-first `sweep the broom` form that other tasks use.
- 188 of 202 sweep segments are labelled `navigation`: the humans drive the base while sweeping rather than sweeping from one spot.

### Hard parts and hacks

- Removal rule (verified in `object_states/particle_modifier.py:525-531, 983-988`): the broom has no `particleremover` meta link (asset `broom/tpyvbt` metadata lists only `base_link`), so the remover box is the **whole broom's world AABB grown by 2 cm**. No overlap or contact check applies to the broom's remover.
- Derived hack: a particle is deleted whenever it falls inside that box. Particles sit at floor level (world z ~0.0). Holding the broom low and near horizontal makes a box roughly 1.35 m long and ~0.45 m wide that reaches the floor. A code skill can drive the base in straight lanes ~0.4 m apart across the free floor with the broom held that way; no particle perception needed. Not tried in simulation.
- The boustrophedon covers about 25 m² of free floor (garage minus the car); at 0.4 m lanes that is ~60 m of base travel, likely too slow inside 224 s. Wider effective lanes need the broom held diagonal across the direction of travel. Unverified timing.
- Visual dust and sand particles are small; whether they are visible in the RGB camera at 1-2 m is unverified. Do not rely on seeing the last grain.
- Broom pick: the broom is rescaled to 1.35 x 0.45 x 0.15 m. The handle width against the 44 mm rule is unverified; 200/200 demos picked it single-armed.
- Failure mode for the VLA: sweeping one area (where the dirt is most visible) and stopping. Force at least two passes that cover the far walls.

### Hints for the VLM

- The garage is garage_0; in all 20 instances the robot starts on the garage floor (x -7.8 to -2.3, y 3.0 to 6.9). The large car occupies one side; the garage door is one wall.
- The broom lies on the floor 1.1-5.8 m from the start. The bucket (`bucket_59`) also sits on the floor; ignore it.
- Dust and sand are flat spots on the concrete floor; sand and dust are separate systems and both must go.
- Done: no spots left anywhere on the garage floor, including near walls and around the car's far side.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered floor.n.01_1 sand.n.04_1))` | no | yes |
| `(not covered floor.n.01_1 dust.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (not
                (covered ?floor.n.01_1 ?sand.n.04_1)
            )
            (not
                (covered ?floor.n.01_1 ?dust.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `broom.n.01_1` | broom_60 | broom / tpyvbt | garage_0 | floor, z 0.08 | 2.88 m (range 1.11-5.81) | yes, spread 6.95 m |
| `floor.n.01_1` | floors_nbxnpk_0 | floors / nbxnpk | garage_0 | floor, z -0.15 | 2.54 m (range 1.19-3.73) | no (fixed) |
| `sand.n.04_1` | particle system | sand | - | - | - | - |
| `dust.n.01_1` | particle system | dust | - | - | - | - |
| `bucket.n.01_1` | bucket_59 | bucket / bdhvnt | garage_0 | floor, z 0.15 | 2.29 m (range 1.01-5.7) | yes, spread 7.37 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garage"
 ],
 "house_double_floor_lower": {
  "whitelist": {
   "broom.n.01": {
    "broom": {
     "tpyvbt": [
      1.35,
      0.45,
      0.15
     ]
    }
   },
   "bucket.n.01": {
    "bucket": {
     "bdhvnt": null
    },
    "ice_bucket": {
     "vlurir": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(covered floor.n.01_1 dust.n.01_1)
(covered floor.n.01_1 sand.n.04_1)
(inroom floor.n.01_1 garage)
(ontop agent.n.01_1 floor.n.01_1)
(ontop broom.n.01_1 floor.n.01_1)
(ontop bucket.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching broom.n.01_1 floor.n.01_1)
(touching bucket.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching floor.n.01_1 broom.n.01_1)
(touching floor.n.01_1 bucket.n.01_1)
```

## What the human demos did

200 annotated demos. Length 146.75 s (range 99.4-268.23). Skills per demo 4.0 (range 4-6). 2 distinct skill orders; the most common one covers 99% of demos.

Most common skill counts per demo (99% of demos): move to x2, pick up from x1, sweep surface x1.

Representative demo `episode_00572140.json` (146.5 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the broom` (0.0-29.6 s)
2. `pick up the broom from the floors` (29.6-49.0 s)
3. `move to the dirt` (49.0-59.0 s)
4. `sweep the dirt` (59.0-146.5 s)

Mean duration per skill in this task: move to 14.1 s, pick up from 23.5 s, sweep surface 95.4 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the broom` | 201 |
| `move to the dirt` | 201 |
| `pick up the broom from the floors` | 200 |
| `sweep the dirt` | 199 |
| `sweep the broom` | 3 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/57_sweeping_garage.json`. Planner notes: `task_docs/notes/57_sweeping_garage.md`.
