# 92 · Installing A Scanner

Task name `installing_a_scanner`, task index 92.

> Install the scanner by turning it on and leaving it on the desk near the laptop.

## At a glance

| item | value |
| --- | --- |
| scene | `office_cubicles_right` |
| rooms in the goal | private_office |
| rooms loaded | corridor_0, private_office_0, private_office_1, private_office_2, private_office_3, copy_room_0, shared_office_0 |
| human demo length | 142.0 s mean (4258 steps) |
| episode time limit | 212.9 s (6387 steps at 30 Hz) |
| human base travel | 6.4139 m |
| goal literals (best ground option) | 2 |
| literals already true at start (inferred) | 0 |
| max Q short of full success | 1.0 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/fVy3dPNOBYk |

## Planner notes

**Tier:** A, borderline B. Both literals can be met without a grasp: press the scanner's button, and push the scanner (or the laptop) along the desk until they touch. The demos lift the scanner, but it is 0.31 x 0.218 x 0.06 m (asset bbox), with no dimension under 44 mm.

### Goal in plain words

- The scanner must be toggled on and must be `nextto` the laptop.
- Both start on the same desk (`desk_mdhelw_0`) in private_office_3, 0.52-2.27 m apart (centre to centre, over the 20 instances).
- The laptop stays closed (joint 0) and does not need to be opened or switched on.

### Q traps

- There are 2 literals and both score (0/2 true at reset). The scanner starts off (`ToggledOn` false in all instances).
- **Toggle parity.** Every separate 5-step finger contact on the button flips the scanner (PREDICATES §11). Brushing the button while pushing or placing afterwards turns it back off. Press it **last**, after the nextto is done. Success ends the episode at once, so nothing can undo it.
- **nextto gap (derived from §5 and the asset sizes).** L = mean(0.513, 0.486, 0.08) = 0.36 m, so the AABB gap must be ≤ ~0.06 m. "Somewhere near the laptop" is not enough. Leave them nearly touching, on the same desk.
- The laptop is only 0.02 m thick, and the scanner's horizontal rays leave from 3 cm above the desk. The literal can still pass through the laptop's own rays hitting the scanner, so keep both flat on the desk.

### Minimal plan

1. `move to the scanner`. Done when the scanner is centred on the desk in the head camera and the base has stopped. About 30 s.
2. `push the scanner to the desk`. This is the closest trained prompt; there is none for "push to the laptop". Done when the scanner's near edge is within ~5 cm of the laptop's edge. About 29 s. If Comet will not slide it the right way, use `code: push` along the desk top toward the laptop. Alternatively, move the laptop instead (light and 0.02 m thick; no trained prompt, the closest is `pick up the laptop from the desk`, seen once).
3. `move to the laptop`. Only if the robot has to re-position. About 30 s.
4. `turn on the scanner`. Done when the button marker turns green (the toggle marker is recoloured red to green, `toggle.py` `_set_value`). Withdraw the finger right after. About 11 s.

- Totals: about 70-100 s against a 212.9 s limit.

### What the demos do differently

- 57% of demos push the scanner, then pick it up, carry it to the laptop, turn it on while holding it, and place it. That is a lift of a 0.22 m-wide box, and the place after the press risks a second button contact.
- 48 of 200 demos skip the push. None open the laptop.

### Hard parts and hacks

- **Button target.** The togglebutton meta link sits at the end face of the scanner's long axis (local x = +0.158 m on a 0.31 m body, z = +0.005 m). The sphere is small (marker size 0.009 m, like the radio's ~11 mm). The fingertip must overlap it **and** touch the scanner for 5 steps.
- **Scripted press.** `code: press` in the style of the radio toggle policy may transfer, with the end-face button as the target (unverified on this asset).
- **Pushing** a 0.31 m box across a 2.78 m desk to within 5 cm needs closed-loop depth feedback. Stop at a small gap rather than shoving the laptop off the desk.
- ft40k scored Q=0 on instance 311.

### Hints for the VLM

- The room is private_office_3, with one desk, one laptop, one scanner and three swivel chairs. There are no same-category distractors in the room.
- The scanner is the flat 0.31 x 0.22 x 0.06 m box on the desk. The laptop is the thinner 0.20 x 0.27 m slab.
- Done: the two objects visibly abut on the desk top (depth gap under ~5 cm), and the scanner's button marker is green.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(toggled_on scanner.n.02_1)` | no | yes |
| `(nextto scanner.n.02_1 laptop.n.01_1)` | no | yes |

BDDL goal:

```lisp
(:goal 
        (and 
            (toggled_on ?scanner.n.02_1) 
            (nextto ?scanner.n.02_1 ?laptop.n.01_1)
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `scanner.n.02_1` | scanner_121 | scanner / juzkjp | private_office_3 | table/counter (0.6-1.1 m), z 0.82 | 2.63 m (range 1.19-3.64) | yes, spread 2.52 m |
| `laptop.n.01_1` | laptop_120 | laptop / nvulcs | private_office_3 | table/counter (0.6-1.1 m), z 0.79 | 1.93 m (range 1.1-3.48) | yes, spread 2.47 m |
| `table.n.02_1` | desk_mdhelw_0 | desk / mdhelw | private_office_3 | low (0.25-0.6 m), z 0.6 | 2.38 m (range 1.86-2.72) | no (fixed) |
| `floor.n.01_1` | floors_zwzwbs_0 | floors / zwzwbs | private_office_3 | floor, z -0.15 | 2.08 m (range 1.6-2.4) | no (fixed) |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "private_office"
 ],
 "office_cubicles_right": {
  "whitelist": {
   "scanner.n.02": {
    "scanner": {
     "juzkjp": null
    }
   },
   "laptop.n.01": {
    "laptop": {
     "nvulcs": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(inroom floor.n.01_1 private_office)
(inroom table.n.02_1 private_office)
(ontop agent.n.01_1 floor.n.01_1)
(ontop laptop.n.01_1 table.n.02_1)
(ontop scanner.n.02_1 table.n.02_1)
(touching agent.n.01_1 floor.n.01_1)
(touching floor.n.01_1 agent.n.01_1)
(touching laptop.n.01_1 table.n.02_1)
(touching scanner.n.02_1 table.n.02_1)
(touching table.n.02_1 laptop.n.01_1)
(touching table.n.02_1 scanner.n.02_1)
```

## What the human demos did

200 annotated demos. Length 128.4 s (range 42.9-289.6). Skills per demo 6.0 (range 5-8). 7 distinct skill orders; the most common one covers 57% of demos.

Most common skill counts per demo (57% of demos): move to x2, pick up from x1, place on x1, push to x1, turn on switch x1.

Representative demo `episode_00922390.json` (133.9 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the scanner` (0.0-16.0 s)
2. `push the scanner to the desk` (16.0-46.5 s)
3. `pick up the scanner from the desk` (46.5-69.0 s)
4. `move to the laptop` (69.0-81.0 s)
5. `turn on the scanner` (81.0-101.4 s)
6. `place the scanner on the desk` (101.4-121.0 s)

Mean duration per skill in this task: move to 29.5 s, pick up from 28.0 s, place on 19.9 s, push to 28.5 s, turn on switch 11.1 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the scanner` | 204 |
| `turn on the scanner` | 200 |
| `place the scanner on the desk` | 200 |
| `pick up the scanner from the desk` | 199 |
| `move to the laptop` | 193 |
| `push the scanner to the desk` | 152 |
| `pick up the laptop from the desk` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/92_installing_a_scanner.json`. Planner notes: `task_docs/notes/92_installing_a_scanner.md`.
