# 77 · Installing A Modem

Task name `installing_a_modem`, task index 77.

> Install the modem by placing it on the cabinet and turning it on.

## At a glance

| item | value |
| --- | --- |
| scene | `Rs_int` |
| rooms in the goal | living_room |
| rooms loaded | bedroom_0, entryway_0, kitchen_0, living_room_0 |
| human demo length | 80.4 s mean (2412 steps) |
| episode time limit | 120.6 s (3619 steps at 30 Hz) |
| human base travel | 2.6609 m |
| goal literals (best ground option) | 4 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | **0.75** realistic; 1.0 from `:init` alone. the TV already rests on the console at reset in all 20 instances, so `ontop television_receiver cabinet` never scores (notes). |
| ground goal options | 2 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft24k@sulab1 Q=0.25; ft40k@sulab1 Q=0.25; ft40k@local Q=0.25; ft10k@sulab1 Q=0.00 |
| demo video | https://www.youtube.com/embed/zHEfUkrCWfc |

## Planner notes

**Tier:** B — one pick-and-place of a small modem onto the TV console, plus an ~11 mm button press, all within 120 s.

### Goal in plain words

The modem must end switched on, resting on the same cabinet as the TV, and next to the TV. The TV already stands on the long living-room TV console (`bottom_cabinet_jhymlr_0` = `cabinet.n.01_1`), so the modem goes on that console beside the TV. The other cabinet option (`bottom_cabinet_bamfsz_1`) would need the TV moved and is not realistic.

### Q traps

- **Fact-page error:** `(ontop television_receiver.n.01_1 cabinet.n.01_1)` is marked "not true at start", but it **is true at reset**. The `:init` block simply does not mention the TV, which is a scene object.
  - Evidence from the template: the TV's AABB is x 1.48-1.60, y -1.95 to -1.25, bottom z 0.757. It sits inside the console's footprint (x 1.28-1.85, y -2.32 to -0.67), whose top is at z 0.754. Positions are identical in all 20 instances.
  - So that literal never scores, and **max partial Q in the best option is 3/4 = 0.75**, not 1.0.
- Result on 311: Q = 0.25 for ft24k and ft40k, i.e. one of the three scorable literals. zs_pt50 and ft10k scored 0.
- `nextto modem TV` (PREDICATES §5): with these sizes L/6 ≈ 0.09 m. The modem must stand **within ~9 cm of the TV's AABB**, on the console top.
- `toggled_on` flips once per separate 5-step touch (§11). A second brush turns it off again. It stays on when the modem is moved, so pressing before or after placing both work.
- Do not knock the TV: the literal is already true, so knocking it off only blocks success.

### Minimal plan

1. `move to the modem` — the coffee table, 0.8-2.5 m from the start. ~16 s.
2. `pick up the modem from the coffee table` ~19 s (27 s in the representative demo).
3. `move to the cabinet` — the TV console. Not the small cabinet near the coffee table. ~16 s.
4. `place the modem on the cabinet` — upright, on the console top, touching or within a few cm of the TV's side. ~10 s.
5. `turn on the modem` — the button marker turns from red to green. ~14 s.

About 75 s against a **120.6 s limit**. A failed grasp retry uses up most of the slack.

### What the demos do differently

- 141/200 follow this plan exactly. 59/200 add `hand over the modem`.
- Every demo presses the button after placing.

### Hard parts and hacks

- **Modem grasp:** `modem_axqxsv` is 0.184 × 0.049 × 0.204 m and stands upright on the coffee table. Its thinnest side, 49 mm, is **just over the 44 mm span**. A grasp may need the top edge, if it tapers (unverified), or a slightly different axis. This is probably why the checkpoints stall at Q ≤ 0.25.
- **Button:** `togglebutton` sphere ~11 mm, the same scale as the radio. Its offset is (0.066, -0.0015, -0.033) m in the modem frame, near one end and below mid-height. Which face it shows depends on how the modem is placed; the red/green marker (`toggle.py:127`) makes it findable in RGB.
- **Console space:** the free top on either side of the TV is 0.37 m (y < -1.95) and 0.58 m (y > -1.25). The side at y > -1.25 is the roomier one.
- Cheap order option: press the button while the modem still stands on the coffee table, at a stable low height (0.40-0.60 m). Then pick and place. This removes the risk of knocking the placed modem away from the TV while pressing.

### Hints for the VLM

- Rs_int living_room_0. The modem is the small upright box on the low coffee table.
- The TV console is the long low cabinet (1.65 m) with the TV standing on it. A second, small cabinet near the coffee table is the wrong one.
- Done: the modem standing on the console right beside the TV, its button marker green.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(toggled_on modem.n.01_1)` | no | yes |
| `(nextto modem.n.01_1 television_receiver.n.01_1)` | no | yes |
| `(ontop television_receiver.n.01_1 cabinet.n.01_2)` | no | yes |
| `(ontop modem.n.01_1 cabinet.n.01_2)` | no | yes |

The goal has 2 ground options (4 literals x2); Q takes the best one, so any valid choice of container or partner object counts.

BDDL goal:

```lisp
(:goal 
        (and 
            (toggled_on ?modem.n.01_1) 
            (nextto ?modem.n.01_1 ?television_receiver.n.01_1)
            (exists 
                (?cabinet.n.01 - cabinet.n.01)
                (and 
                    (ontop ?television_receiver.n.01_1 ?cabinet.n.01)
                    (ontop ?modem.n.01_1 ?cabinet.n.01)
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
| `modem.n.01_1` | modem_72 | modem / axqxsv | living_room_0 | low (0.25-0.6 m), z 0.46 | 1.42 m (range 0.87-2.25) | yes, spread 0.91 m |
| `coffee_table.n.01_1` | coffee_table_fqluyq_0 | coffee_table / fqluyq | living_room_0 | low (0.25-0.6 m), z 0.26 | 1.4 m (range 1.02-2.22) | no |
| `cabinet.n.01_1` | bottom_cabinet_jhymlr_0 | bottom_cabinet / jhymlr | living_room_0 | low (0.25-0.6 m), z 0.38 | 1.66 m (range 0.9-2.51) | no (fixed) |
| `cabinet.n.01_2` | bottom_cabinet_bamfsz_1 | bottom_cabinet / bamfsz | living_room_0 | low (0.25-0.6 m), z 0.38 | 2.35 m (range 1.65-3.67) | no (fixed) |
| `television_receiver.n.01_1` | standing_tv_udotid_0 | standing_tv / udotid | living_room_0 | table/counter (0.6-1.1 m), z 0.83 | 1.51 m (range 0.8-2.5) | no |
| `floor.n.01_1` | floors_ptwlei_0 | floors / ptwlei | living_room_0 | floor, z -0.15 | 1.34 m (range 0.72-1.94) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "bedroom",
  "entryway",
  "kitchen",
  "living_room"
 ],
 "Rs_int": {
  "whitelist": {
   "modem.n.01": {
    "modem": {
     "axqxsv": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom cabinet.n.01_1 living_room)
(inroom cabinet.n.01_2 living_room)
(inroom coffee_table.n.01_1 living_room)
(inroom floor.n.01_1 living_room)
(inroom television_receiver.n.01_1 living_room)
(ontop agent.n.01_1 floor.n.01_1)
(ontop modem.n.01_1 coffee_table.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching coffee_table.n.01_1 modem.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching modem.n.01_1 coffee_table.n.01_1)
```

## What the human demos did

200 annotated demos. Length 71.0 s (range 50.9-165.07). Skills per demo 5.0 (range 5-7). 4 distinct skill orders; the most common one covers 70% of demos.

Most common skill counts per demo (70% of demos): move to x2, pick up from x1, place on x1, turn on switch x1.

Representative demo `episode_00770220.json` (69.2 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the modem` (0.0-9.0 s)
2. `pick up the modem from the coffee table` (9.0-36.0 s)
3. `move to the cabinet` (36.0-47.0 s)
4. `place the modem on the cabinet` (47.0-58.2 s)
5. `turn on the modem` (58.2-69.0 s)

Mean duration per skill in this task: hand over 11.9 s, move to 15.7 s, pick up from 19.4 s, place on 10.3 s, turn on switch 13.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the cabinet` | 202 |
| `move to the modem` | 200 |
| `pick up the modem from the coffee table` | 200 |
| `place the modem on the cabinet` | 200 |
| `turn on the modem` | 200 |
| `hand over the modem` | 59 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/77_installing_a_modem.json`. Planner notes: `task_docs/notes/77_installing_a_modem.md`.
