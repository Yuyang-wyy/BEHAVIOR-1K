# 45 · Cook Hot Dogs

Task name `cook_hot_dogs`, task index 45.

> Take the two hot dogs out of the refrigerator in the kitchen and cook them in the microwave until both are cooked.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, dining_room_0, entryway_0, garden_0, kitchen_0, living_room_0, living_room_1 |
| human demo length | 304.8 s mean (9144 steps) |
| episode time limit | 457.2 s (13717 steps at 30 Hz) |
| human base travel | 25.7822 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.50; ft40k@local Q=0.50 |
| demo video | https://player.vimeo.com/video/1114061371 |

## Planner notes

**Tier:** D — heat both hot dogs to 60 °C, plus two picks from the fridge and two places into the microwave.

### Goal in plain words

Both hot dogs must reach `cooked`, i.e. `MaxTemperature` of at least 60 °C (hotdog `cook_temperature`, §15). Cooked latches, so they may cool off afterwards. **Heat source:** the demos use the microwave `microwave_abzvij_0` (100 °C, rate 0.1). It heats only when it is closed, toggled on, and the hot dog's centre is inside it (§2). The burner `burner_mjvqii_0` also works: a 1980 °C source that heats anything within 0.2 m of its active point. No container is needed. The fridge and the microwave state are not in the goal.

### Q traps

- Two literals, both false at start (hot dogs start at -2.2 °C). Max Q is 1.0, and each hot dog is worth 0.5.
- **Microwave order:** put the hot dogs in, close the door flush (within 5 %), and only then press start. Opening the door turns the microwave off, and a press while the door is open does nothing (§11).
- Heating time in the microwave, from -2.2 °C to 60 °C, is about 10 s (derived from §2: T_ss ≈ 87 °C, time constant 8.3 s). Opening before that loses the heat, but `MaxTemperature` keeps the progress.
- Both hot dogs can go in together, so one heating cycle does both. Cooking them one at a time needs a second open, place, close and press.
- A hot dog on the floor of the cavity but with its centre outside the microwave's volume (half out of the door) does not heat.

### Minimal plan

1. `move to the fridge`, `open the door of the fridge` — ~24 s + ~35 s.
2. `pick up the hotdog from the middle_level fridge` (use the shelf word that fits: `low_level`, `middle_level` or `high_level`) — ~26 s.
3. Pick the second hot dog with the other hand, using the same prompt shape. ~26 s.
4. Skip `close the door of the fridge` (not in the goal; saves ~23 s).
5. `move to the microwave` — ~24 s.
6. `place the hotdog on the countertop` — frees a hand for the door. ~12 s.
7. `open the door of the microwave` — ~35 s.
8. `place the hotdog in the microwave` — ~17 s.
9. `pick up the hotdog from the countertop`, then `place the hotdog in the microwave` — ~26 s + ~17 s.
10. `close the door of the microwave` — door flush. ~23 s.
11. `turn on the microwave` — ~11 s. Wait about 12 s. Success ends the episode.

The plan takes about 275 s against a 457 s limit.

Alternative, no door (derived, untested): `move to the burner`, place both hot dogs on the right burner (no trained prompt; closest: `place the hotdog on the countertop`), then `turn on the burner`. They would cook in well under a second. This saves steps 6-11, about 140 s, but it depends on the working burner zone (see below).

### What the demos do differently

- All demos close the fridge right after taking the hot dogs out (~23 s, not needed).
- All demos set one hot dog on the countertop to free a hand for the microwave door, then load them one by one. That is the right trick with two hands full.
- No demo uses the burner.

### Hard parts and hacks

- **Grasp span.** A hot dog is 76 x 158 x 54 mm by bbox, so no axis is under 44 mm. The ft40k checkpoint still cooked one hot dog on instance 311 (Q 0.5). A grasp is therefore possible, probably on the narrow sausage end sticking out of the bun (unverified).
- **Shelf height** varies: z 0.50, 0.91 or 1.32.
- **Microwave door.** Opening it needs a graspable handle or edge (width not verified). Closing can be a push.
- **Burner caveat.** `burner_mjvqii` has 5 heat points and 5 knobs, but only the first of each is used (`link_based_state_mixin.py:90`). The demos in cook_cabbage and cook_bacon always cook on the "right burner".

### Hints for the VLM

- Kitchen of `house_single_floor`. The fridge is at (7.8, -2.0) on the sink wall. The microwave `abzvij` sits on the counter along the x ≈ 4.2 wall, at y ≈ 0.8, 1.04 m up. The burner is on the same counter at y ≈ -0.5.
- There is only one microwave and one pair of hot dogs (sausage in a bun) in the fridge.
- Done: both hot dogs inside the closed, running microwave for about 10 s. The episode ends by itself on success.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(cooked hotdog.n.02_1)` | no | yes |
| `(cooked hotdog.n.02_2)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (forall 
                (?hotdog.n.02 - hotdog.n.02) 
                (cooked ?hotdog.n.02)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `microwave.n.02_1` | microwave_abzvij_0 | microwave / abzvij | kitchen_0 | table/counter (0.6-1.1 m), z 1.04 | 1.84 m (range 0.99-4.39) | no (fixed) |
| `hotdog.n.02_1` | hotdog_208 | hotdog / lsajfg | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.71 m (range 0.79-4.27) | yes, spread 0.4 m |
| `hotdog.n.02_2` | hotdog_207 | hotdog / lsajfg | kitchen_0 | table/counter (0.6-1.1 m), z 0.91 | 2.68 m (range 0.77-4.3) | yes, spread 0.39 m |
| `electric_refrigerator.n.01_1` | fridge_dszchb_0 | fridge / dszchb | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.84 m (range 0.97-4.31) | no (fixed) |
| `floor.n.01_1` | floors_kxcpgy_0 | floors / kxcpgy | kitchen_0 | floor, z -0.14 | 1.44 m (range 0.75-2.21) | no (fixed) |

Initial conditions from `:init`:

```lisp
(inroom electric_refrigerator.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom microwave.n.02_1 kitchen)
(inside hotdog.n.02_1 electric_refrigerator.n.01_1)
(inside hotdog.n.02_2 electric_refrigerator.n.01_1)
(ontop agent.n.01_1 floor.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
```

## What the human demos did

200 annotated demos. Length 288.9 s (range 211.5-737.93). Skills per demo 13.0 (range 12-13). 2 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): pick up from x3, close door x2, move to x2, open door x2, place in x2, place on x1, turn on switch x1.

Representative demo `episode_00451760.json` (288.6 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the fridge` (0.0-31.0 s)
2. `open the door of the fridge` (31.0-66.9 s)
3. `pick up the hotdog from the high_level fridge` (66.9-91.4 s)
4. `pick up the hotdog from the middle_level fridge` (91.4-113.9 s)
5. `close the door of the fridge` (113.9-142.6 s)
6. `move to the microwave` (142.6-170.1 s)
7. `place the hotdog on the countertop` (170.1-185.7 s)
8. `open the door of the microwave` (185.7-214.6 s)
9. `place the hotdog in the microwave` (214.6-227.7 s)
10. `pick up the hotdog from the countertop` (227.7-249.7 s)
11. `place the hotdog in the microwave` (249.7-263.7 s)
12. `close the door of the microwave` (263.7-273.2 s)
13. `turn on the microwave` (273.2-288.6 s)

Mean duration per skill in this task: close door 23.2 s, move to 24.1 s, open door 34.6 s, pick up from 25.8 s, place in 17.0 s, place on 11.8 s, turn on switch 11.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `place the hotdog in the microwave` | 398 |
| `move to the fridge` | 200 |
| `place the hotdog on the countertop` | 200 |
| `open the door of the microwave` | 200 |
| `close the door of the microwave` | 200 |
| `close the door of the fridge` | 199 |
| `move to the microwave` | 199 |
| `open the door of the fridge` | 198 |
| `turn on the microwave` | 198 |
| `pick up the hotdog from the countertop` | 197 |
| `pick up the hotdog from the low_level fridge` | 148 |
| `pick up the hotdog from the middle_level fridge` | 136 |
| `pick up the hotdog from the high_level fridge` | 115 |
| `pick up the hotdog from the microwave` | 2 |
| `turn on the fridge` | 2 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/45_cook_hot_dogs.json`. Planner notes: `task_docs/notes/45_cook_hot_dogs.md`.
