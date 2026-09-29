# 93 · Clean A Keyboard

Task name `clean_a_keyboard`, task index 93.

> Use the pipe cleaner to clean the keyboard until the stain is removed.

## At a glance

| item | value |
| --- | --- |
| scene | `office_cubicles_right` |
| rooms in the goal | private_office |
| rooms loaded | private_office_0, private_office_1, private_office_2, private_office_3, shared_office_0, corridor_0 |
| human demo length | 129.2 s mean (3876 steps) |
| episode time limit | 193.8 s (5814 steps at 30 Hz) |
| human base travel | 4.4593 m |
| goal literals (best ground option) | 1 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/yEV3cFqyu-4 |

## Planner notes

**Tier:** D. The goal is a cleaning state change, and it needs a tool grasp plus a precise sweep. The keyboard itself never has to be grasped.

### Goal in plain words

- Every dust particle on the keyboard must be gone: `not covered keyboard dust`.
- There is one keyboard and one tool, the pipe cleaner, both on the same desk (`desk_mdhelw_2`) in private_office_0.
- No water, soap or sink is needed. Dust removal by `pipe_cleaner.n.01` is unconditional (PREDICATES §12).
- The live BDDL (`BEHAVIOR-1K/bddl3`) matches this. Older copies in other repos describe a different rag-and-sink task.

### Q traps

- There is 1 literal, so Q is 0 or 1. Removing 19 of 20 particles scores 0.
- `Covered` for visual dust is True with ≥ 1 particle left, and the instances hold 20 particles (see memory: clean_a_keyboard mechanics).
- Removal is geometric (ADJACENCY method). Any particle inside the tool's root-link AABB grown by 0.02 m is deleted every step.
  - So the tool only has to be swept over every part of the keyboard top. Touching one spot cleans one spot.
  - Pressing harder does nothing.
- Success ends the episode at once. Keep sweeping until it ends, because there is no signal of how many particles remain.

### Minimal plan

1. `move to the pipe cleaner`. Done when the cyan tool is centred on the desk and the base is 0.7-0.9 m from it. About 15 s.
2. `pick up the pipe cleaner from the desk`. Done when the fingers stop strictly between fully closed and fully open, and the cyan handle is lifted. About 32 s.
3. `move to the keyboard`. Keep the loaded hand low and do not raise the trunk. Done when the keyboard is in view at ~0.7-0.8 m. About 15 s.
4. `sweep the keyboard`. This is the demo's wording: the object is named, not the tool. Done when the episode ends (success). Otherwise repeat passes along the keyboard's long axis until time runs out. About 31 s per attempt.

- Totals: about 95 s against a 193.8 s (5814-step) limit.
- Skip the demo's swivel-chair push unless a chair physically blocks the approach to the desk.

### What the demos do differently

- 178 of 200 demos first do `move to the swivel chair` and `push the swivel chair to the desk`. The goal does not need this. It only clears space.
- Humans sweep once for about 31 s. Scripted experience says multiple overlapping passes are needed to catch all 20 particles.

### Hard parts and hacks

- **Tool geometry.** The task rescales the pipe cleaner (model yccyjo) to 0.40 x 0.10 x 0.10 m (`task_custom_lists.json`). A thin cyan handle fits the 44 mm jaws, so the removal box is ~0.44 x 0.14 x 0.14 m. The keyboard is 0.477 x 0.181 x 0.016 m, so one stroke cannot cover it.
- **Sweep height window is ~1.6 cm.** Too low shoves or flings the keyboard (moves of up to 0.26 m were seen). Too high and the box misses the dust.
  - The keyboard top comes from the camera, which is consistent to ~2 mm.
  - The rod axis about 0.056-0.058 m above the seen top worked.
  - Re-detect the keyboard before each stroke. If it moved, the sweep misses.
- **Tipping is the dominant failure.** The base rises in ~60% of scripted trials while carrying the tool. Never carry the tool extended high and never raise the trunk while holding. Drive with the hand where the lift left it.
- **Scripted baseline.** 40 scripted-policy versions reached only ~5-10% on fresh seeds: v35 and v40 each 1/20, best tuning-seed batch 4/20. See `radio_generalization_20260920/KEYBOARD_RESULTS.md`. ft40k scored Q=0 on instance 311.
- `code: sweep` beats Comet on the stroke geometry only if the grasp and the carry succeed. A hybrid (Comet grasp, then scripted low-carry and sweep) is untested.
- Physics hangs inside PhysX occurred when the base drove with the tool held just above the keyboard. Lift the tool ≥ 0.15 m clear before any base motion near the desk.

### Hints for the VLM

- The pipe cleaner is the only saturated cyan object (RGB about 24, 118, 150). The desk is dark wood. The keyboard is a 0.48 x 0.18 m slab about 3 cm proud of the desk.
- The room is private_office_0, with one desk and three swivel chairs. Other offices have desks too, so do not leave the room.
- Robot odometry drifts about 15% of each turn. Re-find the tool and the keyboard in the image after rotating.
- Done: the episode terminates. Nothing in RGB reliably shows the last few dust particles.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered keyboard.n.01_1 dust.n.01_1))` | no | yes |

BDDL goal:

```lisp
(:goal
        (and
            (not
                (covered ?keyboard.n.01_1 ?dust.n.01_1)
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
| `keyboard.n.01_1` | keyboard_121 | keyboard / uwacaq | private_office_0 | table/counter (0.6-1.1 m), z 0.79 | 1.44 m (range 0.84-2.58) | yes, spread 2.54 m |
| `pipe_cleaner.n.01_1` | pipe_cleaner_120 | pipe_cleaner / yccyjo | private_office_0 | table/counter (0.6-1.1 m), z 0.83 | 1.74 m (range 1.03-2.55) | yes, spread 2.51 m |
| `desk.n.01_1` | desk_mdhelw_2 | desk / mdhelw | private_office_0 | low (0.25-0.6 m), z 0.6 | 1.62 m (range 1.46-1.9) | no (fixed) |
| `floor.n.01_1` | floors_wjsaxw_0 | floors / wjsaxw | private_office_0 | floor, z -0.14 | 1.66 m (range 1.53-1.88) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "private_office"
 ],
 "office_cubicles_right": {
  "whitelist": {
   "dust.n.01": {},
   "keyboard.n.01": {
    "keyboard": {
     "uwacaq": null
    }
   },
   "pipe_cleaner.n.01": {
    "pipe_cleaner": {
     "yccyjo": [
      0.4,
      0.1,
      0.1
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
(covered keyboard.n.01_1 dust.n.01_1)
(inroom desk.n.01_1 private_office)
(inroom floor.n.01_1 private_office)
(ontop agent.n.01_1 floor.n.01_1)
(ontop keyboard.n.01_1 desk.n.01_1)
(ontop pipe_cleaner.n.01_1 desk.n.01_1)
(touching agent.n.01_1 floor.n.01_1)
(touching desk.n.01_1 keyboard.n.01_1)
(touching desk.n.01_1 pipe_cleaner.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching keyboard.n.01_1 desk.n.01_1)
(touching pipe_cleaner.n.01_1 desk.n.01_1)
```

## What the human demos did

200 annotated demos. Length 130.5 s (range 37.2-234.87). Skills per demo 6.0 (range 4-6). 3 distinct skill orders; the most common one covers 89% of demos.

Most common skill counts per demo (89% of demos): move to x3, pick up from x1, push to x1, sweep surface x1.

Representative demo `episode_00931600.json` (136.4 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the swivel chair` (0.0-19.0 s)
2. `push the swivel chair to the desk` (19.0-38.0 s)
3. `move to the pipe cleaner` (38.0-54.0 s)
4. `pick up the pipe cleaner from the desk` (54.0-87.0 s)
5. `move to the keyboard` (87.0-106.0 s)
6. `sweep the keyboard` (106.0-136.0 s)

Mean duration per skill in this task: move to 15.0 s, pick up from 31.9 s, push to 24.3 s, sweep surface 31.2 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the pipe cleaner` | 200 |
| `pick up the pipe cleaner from the desk` | 200 |
| `move to the keyboard` | 200 |
| `sweep the keyboard` | 200 |
| `move to the swivel chair` | 178 |
| `push the swivel chair to the desk` | 178 |
| `move to the desk` | 1 |
| `move to the chair` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/93_clean_a_keyboard.json`. Planner notes: `task_docs/notes/93_clean_a_keyboard.md`.
