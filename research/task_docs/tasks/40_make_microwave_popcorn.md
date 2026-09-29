# 40 · Make Microwave Popcorn

Task name `make_microwave_popcorn`, task index 40.

> In the kitchen, take the popcorn bag from the countertop, put it into the microwave, and heat it until the popcorn is cooked so the cooked popcorn ends up inside the bag.

## At a glance

| item | value |
| --- | --- |
| scene | `house_double_floor_lower` |
| rooms in the goal | kitchen |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0 |
| human demo length | 107.9 s mean (3237 steps) |
| episode time limit | 161.9 s (4856 steps at 30 Hz) |
| human base travel | 8.6032 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | zs_pt50@sulab1 Q=0.00; ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://player.vimeo.com/video/1114060842 |

## Planner notes

**Tier:** D — one heating transition (`popcorn` to `cooked__popcorn`) on top of moving a 203 x 278 x 180 mm popcorn bag, which is wider than the 44 mm jaw span in every direction.

### Goal in plain words

Some popcorn in the bag must become `cooked__popcorn` while it is still inside the bag's volume. `CookingPhysicalParticleRule` (`transition_rules.py:1908`) replaces every popcorn particle inside a **heatable, fillable, non-fixed container** with cooked popcorn once the container is `Heated`, meaning its own temperature is at least 40 °C. The bag is that container: `popcorn__bag.n.01` is `fillable` and `heatable` in the KB. Both goal literals flip on the same step, so this task is all or nothing. The microwave is not in the goal. Any heat source that warms the bag to 40 °C works.

### Q traps

- Two literals, both false at start, both flip together. Q is 0 or 1.
- **Microwave path.** The bag's AABB centre must be inside the microwave's volume. The door must be fully closed, within 5 % (§6). The microwave must be toggled on *after* closing, because opening forces it off (§11). The bag reaches 40 °C in about 2.6 s (PREDICATES §7).
- **Burner path (derived, untested).** The burner `burner_mdanhg_0` sits on the same bar as the bag, at x 6.91 against the bag's x ≈ 7.55. Its heat point is a 1980 °C source that affects anything within 0.2 m (§2), and it heats the bag to 40 °C in a few steps. The bag is `flammable` (ignition 250 °C), but success ends the episode at 40 °C, long before that.
- Tipping the bag can spill popcorn outside its volume. Uncooked spilled popcorn does not count. Keep the bag upright.

### Minimal plan

Demo path (in distribution):

1. `move to the microwave` — microwave front fills the view. ~12 s.
2. `open the door of the microwave` — door swung open, cavity visible. ~17 s.
3. `move to the popcorn bag` — bag on the bar in view. ~12 s.
4. `pick up the popcorn bag from the bar` — bag lifted clear of the bar. ~13 s.
5. `move to the microwave` — ~12 s.
6. `place the popcorn bag in the microwave` — bag inside the cavity, hand withdrawn. ~14 s.
7. `close the door of the microwave` — door flush with the body. ~8 s.
8. `turn on the microwave` — press the button once. Success should fire within about 3 s. ~9 s.

The plan takes about 100 s against a 162 s limit, which leaves little slack for retries.

Grasp-free fallback (no trained prompt; closest: `push the ... to the ...` shapes from other tasks): push the bag along the bar top onto or beside the cooktop, then send `turn on the burner` (trained in cook_cabbage and cook_bacon). This is worth trying only if the bag grasp fails. See the burner caveat below.

### What the demos do differently

- All 200 demos follow the same 8 steps: open the door first, then fetch the bag. That order is right. Opening first leaves a free hand for the door.
- No demo uses the cooktop.

### Hard parts and hacks

- **Bag size.** The bag is 203 x 278 x 180 mm (asset bbox × template scale). No dimension fits the 44 mm span. A grasp may register only on a thin feature such as a folded top edge (unverified). The ft40k checkpoint scored 0 on instance 311.
- **Microwave door.** Opening the `hjjxmi` door needs a handle or an edge the jaws can close on. Its width is not verified.
- **Fit.** The microwave is 343 x 517 x 264 mm outside, and the bag is 180 mm tall. It fits, but only if the bag goes in upright.
- **Burner caveat.** `burner_mdanhg` has 5 `heatsource` and 5 `togglebutton` meta links. `HeatSourceOrSink` and `ToggledOn` each use only the first matching link (`LinkBasedStateMixin.link`, `object_states/link_based_state_mixin.py`), so only one zone heats and only one knob works. Which ones is not verified. In the single-floor house, demos always use the "right burner" (see cook_cabbage and cook_bacon).
- The bag stays at z 0.98 on `bar_byvbuc_0`, with x 7.45-7.66 across all 20 instances. The microwave is at (6.12, -0.70) on the same bar.

### Hints for the VLM

- Kitchen of `house_double_floor_lower`. `bar_byvbuc_0` is the counter run along the y ≈ -0.7 wall. In order of increasing x it holds the two-door fridge (x 5.2, just past the bar end), the microwave (x 6.1), the range with its cooktop over the oven (x 6.9), and the popcorn bag (x ≈ 7.55).
- There is only one microwave and only one popcorn bag.
- Done: the episode ends by itself on success. If it does not end within about 5 s of pressing the button, check that the door is flush and that the bag is inside, then press once more.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(real cooked__popcorn.n.01_1)` | no | yes |
| `(contains popcorn__bag.n.01_1 cooked__popcorn.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (real ?cooked__popcorn.n.01_1)
            (contains ?popcorn__bag.n.01_1 ?cooked__popcorn.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `popcorn.n.02_1` | particle system | popcorn | - | - | - | - |
| `cooked__popcorn.n.01_1` | particle system | cooked__popcorn | - | - | - | - |
| `popcorn__bag.n.01_1` | popcorn_bag_73 | popcorn_bag / hdcpqg | kitchen_0 | table/counter (0.6-1.1 m), z 0.98 | 2.99 m (range 1.31-5.84) | yes, spread 0.36 m |
| `microwave.n.02_1` | microwave_hjjxmi_0 | microwave / hjjxmi | kitchen_0 | table/counter (0.6-1.1 m), z 1.01 | 2.64 m (range 1.18-4.71) | no (fixed) |
| `countertop.n.01_1` | bar_byvbuc_0 | bar / byvbuc | kitchen_0 | low (0.25-0.6 m), z 0.4 | 2.81 m (range 1.21-5.21) | no (fixed) |
| `floor.n.01_1` | floors_zqjkvm_0 | floors / zqjkvm | kitchen_0 | floor, z -0.15 | 2.12 m (range 0.88-3.2) | no (fixed) |

Initial conditions from `:init`:

```lisp
(filled popcorn__bag.n.01_1 popcorn.n.02_1)
(future cooked__popcorn.n.01_1)
(inroom countertop.n.01_1 kitchen)
(inroom floor.n.01_1 kitchen)
(inroom microwave.n.02_1 kitchen)
(ontop agent.n.01_1 floor.n.01_1)
(ontop popcorn__bag.n.01_1 countertop.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching countertop.n.01_1 popcorn__bag.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching popcorn__bag.n.01_1 countertop.n.01_1)
```

## What the human demos did

200 annotated demos. Length 105.03 s (range 51.67-161.77). Skills per demo 8.0. 1 distinct skill orders; the most common one covers 100% of demos.

Most common skill counts per demo (100% of demos): move to x3, close door x1, open door x1, pick up from x1, place in x1, turn on switch x1.

Representative demo `episode_00400950.json` (105.1 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the microwave` (0.7-16.9 s)
2. `open the door of the microwave` (17.7-42.8 s)
3. `move to the popcorn bag` (42.8-49.6 s)
4. `pick up the popcorn bag from the bar` (52.3-60.1 s)
5. `move to the microwave` (60.2-70.0 s)
6. `place the popcorn bag in the microwave` (71.6-86.2 s)
7. `close the door of the microwave` (86.3-94.8 s)
8. `turn on the microwave` (95.5-105.8 s)

Mean duration per skill in this task: close door 8.0 s, move to 12.4 s, open door 16.9 s, pick up from 13.2 s, place in 14.3 s, turn on switch 8.8 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the microwave` | 398 |
| `move to the popcorn bag` | 202 |
| `open the door of the microwave` | 200 |
| `place the popcorn bag in the microwave` | 200 |
| `close the door of the microwave` | 200 |
| `turn on the microwave` | 200 |
| `pick up the popcorn bag from the bar` | 199 |
| `pick up the popcorn bag from the microwave` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/40_make_microwave_popcorn.json`. Planner notes: `task_docs/notes/40_make_microwave_popcorn.md`.
