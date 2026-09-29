# 71 · Clean Your Rusty Garden Tools

Task name `clean_your_rusty_garden_tools`, task index 71.

> Use the steel wool to clean the rust off the garden tools, then put the tools into the toolbox.

## At a glance

| item | value |
| --- | --- |
| scene | `house_single_floor` |
| rooms in the goal | garden |
| rooms loaded | corridor_0, garden_0, kitchen_0, living_room_0, garage_0 |
| human demo length | 505.3 s mean (15157 steps) |
| episode time limit | 757.9 s (22736 steps at 30 Hz) |
| human base travel | 68.579 m |
| goal literals (best ground option) | 5 |
| literals already true at start (inferred) | 1 |
| max Q short of full success | 0.8 |
| ground goal options | 1 |
| public test instances | 20 (ids 301-320) |
| closed-loop results, instance 311, n=1 | ft40k@sulab1 Q=0.00; ft40k@local Q=0.00 |
| demo video | https://www.youtube.com/embed/tHiesuHDgkc |

## Planner notes

**Tier:** D — every rust particle must be scrubbed off two small tools with steel wool, and then both tools packed into a lidded toolbox. The objects are scattered across a large garden.

### Goal in plain words

The trowel and the scraper must both carry zero rust particles, both be inside the toolbox, and the toolbox lid must be closed at the end. Where the steel wool ends up does not matter.

### Q traps

- 5 literals. `not open toolbox` is true at reset, so it never scores but blocks success. Max partial Q = 4/5 = 0.8.
- Result on 311 (ft40k): Q = 0.00.
- **All rust must go** (PREDICATES §12). Each instance has 40 rust particles (`rust.n.01_1.n_particles`), spread over both tools. One particle left keeps `covered` True.
- Steel wool removes rust with condition "always". The method is ADJACENCY: any rust particle inside the steel wool's world AABB grown by 2 cm is deleted that step. There is no rate limit below 200.
- Clean before packing, and check each tool from both sides: particles sit on the top and bottom faces (template offsets span roughly -6 to +13 mm about the tool centre).
- Close the lid last, and re-check that both tools are still inside: a tool poking out can stop the lid, or its centre can end above the volume.

### Minimal plan

1. `move to the toolbox` ~58 s (long walks here).
2. `open the lid of the toolbox` — lid up. ~28 s. It starts closed (joint_pos 0).
3. `pick up the steel wool from the toolbox` ~22 s. Keep holding it for both tools.
4. `move to the trowel`, `pick up the trowel from the driveway` — second hand. ~58 + 22 s.
5. `wipe the steel wool` — rub the pad along both faces of the trowel until no rust spots remain. ~10 s per pass.
6. `move to the toolbox`, `place the trowel in the toolbox` ~58 + 21 s.
7. `move to the scraper`, `pick up the scraper from the driveway`, `wipe the steel wool`, `move to the toolbox`, `place the scraper in the toolbox`.
8. Skip `place the steel wool in the toolbox` if the hand can simply drop it. It is not in the goal, but keep it out of the toolbox if it would block the lid.
9. `close the lid of the toolbox` — the lid is flush (within 5 % of closed). ~24 s.

The demo mean is 505 s against a 758 s limit. Base travel in the demos is 69 m.

### What the demos do differently

- 199/200 follow exactly the plan above, including putting the steel wool back in the toolbox.
- 59/200 add `move to the steel wool`.
- No demo carries the toolbox to the tools. Carrying it could save walks, but the toolbox has no handle data and it is 0.26 × 0.61 × 0.35 m.

### Hard parts and hacks

- **Distances:** trowel, scraper and toolbox are spread across the garden driveway area (per-object spread 29-37 m across instances). In several instances a tool is 25-29 m from the start (301, 309, 319, 320). Plan the walk order by what is nearest.
- **Grasps:**
  - The trowel (0.28 × 0.046 × 0.024 m) and scraper (0.175 × 0.055 × 0.024 m) lie flat on the ground. The narrow handle ends should fit the 44 mm jaws; exact handle widths are unverified.
  - The steel wool is a flat 0.31 × 0.087 × 0.02 m pad lying inside the toolbox. Its only thin axis is vertical, so a top-down grasp does not straddle it. This is the riskiest grasp (see r1pro-grasp-span lesson).
- **Scrubbing geometry:** the removal box is the steel wool's world-aligned AABB plus 2 cm. A pad held flat is only ~6 cm tall with that margin.
  - Pass it over the tool so the tool's faces fall inside that box. Tilting the pad enlarges the AABB.
- Possible shortcut (derived, unverified): the steel wool does not need to be held for removal. Pressing a held tool flat onto the pad lying in the toolbox would clear the particles inside the pad's AABB + 2 cm, but not the top face.

### Hints for the VLM

- Garden of house_single_floor, on or near the driveway. The toolbox is a 0.6 m long box on the ground with a lid (`toolbox_redmtl`), and at start the steel wool is inside it.
- Rust shows as small spots on the metal tools. A tool is done when no spot is visible on either face.
- Done: both tools lying in the toolbox and the lid shut. The steel wool may be anywhere.

## Goal and Q scoring

Q is the fraction of literals in the best ground option that were **false at reset and are true at the end**. A literal that is already true at reset sits in the denominator but can never earn credit. Full success scores 1.0 regardless.

Ground literals of the best option (initial truth inferred from `:init`):

| literal | true at start? | scores? |
| --- | --- | --- |
| `(not covered trowel.n.01_1 rust.n.01_1))` | no | yes |
| `(not covered scraper.n.01_1 rust.n.01_1))` | no | yes |
| `(inside trowel.n.01_1 toolbox.n.01_1)` | no | yes |
| `(inside scraper.n.01_1 toolbox.n.01_1)` | no | yes |
| `(not open toolbox.n.01_1))` | yes | never (already true) |

BDDL goal:

```lisp
(:goal
        (and
            (not
                (covered ?trowel.n.01_1 ?rust.n.01_1)
            )
            (not
                (covered ?scraper.n.01_1 ?rust.n.01_1)
            )
            (inside ?trowel.n.01_1 ?toolbox.n.01_1)
            (inside ?scraper.n.01_1 ?toolbox.n.01_1)
            (not
                (open ?toolbox.n.01_1)
            )
        )
    )
)
```

## Objects and where they start

Heights and distances come from the 20 public instances (301-320). Distance is horizontal, from the robot's start pose.

| BDDL instance | scene object | category / model | room | height | dist from start | moves between instances |
| --- | --- | --- | --- | --- | --- | --- |
| `rust.n.01_1` | particle system | rust | - | - | - | - |
| `trowel.n.01_1` | trowel_335 | trowel / ematag | garden_0 | floor, z -0.01 | 8.57 m (range 0.98-27.15) | yes, spread 37.03 m |
| `scraper.n.01_1` | scraper_334 | scraper / icqmje | garden_0 | floor, z -0.01 | 11.46 m (range 3.49-29.34) | yes, spread 34.17 m |
| `driveway.n.01_1` | driveway_hmbdky_0 | driveway / hmbdky | garden_0 | floor, z -0.16 | 7.53 m (range 0.58-15.84) | no (fixed) |
| `steel_wool.n.01_1` | steel_wool_333 | steel_wool / egeolq | garden_0 | floor, z 0.0 | 10.49 m (range 2.85-19.81) | yes, spread 29.26 m |
| `toolbox.n.01_1` | toolbox_332 | toolbox / redmtl | garden_0 | floor, z 0.06 | 10.45 m (range 2.77-19.84) | yes, spread 29.4 m |

Task-specific asset whitelist / rescaling (`task_custom_lists.json`; a list of three numbers is a forced bounding-box size in metres):

```json
{
 "room_types": [
  "garden"
 ],
 "house_single_floor": {
  "whitelist": {
   "steel_wool.n.01": {
    "steel_wool": {
     "egeolq": null
    }
   },
   "scraper.n.01": {
    "scraper": {
     "icqmje": null
    }
   },
   "toolbox.n.01": {
    "toolbox": {
     "redmtl": null
    }
   },
   "trowel.n.01": {
    "trowel": {
     "ematag": null
    }
   }
  },
  "blacklist": {}
 }
}
```

Initial conditions from `:init`:

```lisp
(covered scraper.n.01_1 rust.n.01_1)
(covered trowel.n.01_1 rust.n.01_1)
(inroom driveway.n.01_1 garden)
(inside steel_wool.n.01_1 toolbox.n.01_1)
(ontop agent.n.01_1 driveway.n.01_1)
(ontop scraper.n.01_1 driveway.n.01_1)
(ontop toolbox.n.01_1 driveway.n.01_1)
(ontop trowel.n.01_1 driveway.n.01_1)
(touching agent.n.01_1 driveway.n.01_1)
(touching driveway.n.01_1 agent.n.01_1)
(touching driveway.n.01_1 scraper.n.01_1)
(touching driveway.n.01_1 toolbox.n.01_1)
(touching driveway.n.01_1 trowel.n.01_1)
(touching scraper.n.01_1 driveway.n.01_1)
(touching toolbox.n.01_1 driveway.n.01_1)
(touching trowel.n.01_1 driveway.n.01_1)
```

## What the human demos did

200 annotated demos. Length 484.65 s (range 299.07-903.67). Skills per demo 15.0 (range 15-16). 2 distinct skill orders; the most common one covers 70% of demos.

Most common skill counts per demo (70% of demos): move to x5, pick up from x3, place in x3, wipe hard x2, close lid x1, open lid x1.

Representative demo `episode_00710330.json` (467.3 s). The prompts are the exact skill sentences Comet was fine-tuned on, so they are in-distribution prompts:

1. `move to the toolbox` (0.0-30.0 s)
2. `open the lid of the toolbox` (30.0-57.0 s)
3. `pick up the steel wool from the toolbox` (57.0-78.0 s)
4. `move to the trowel` (78.0-136.0 s)
5. `pick up the trowel from the driveway` (136.0-151.2 s)
6. `wipe the steel wool` (151.2-164.0 s)
7. `move to the toolbox` (164.0-204.0 s)
8. `place the trowel in the toolbox` (204.0-224.0 s)
9. `move to the scraper` (224.0-303.0 s)
10. `pick up the scraper from the driveway` (303.0-318.4 s)
11. `wipe the steel wool` (318.4-344.0 s)
12. `move to the toolbox` (344.0-414.0 s)
13. `place the scraper in the toolbox` (414.0-428.0 s)
14. `place the steel wool in the toolbox` (428.0-441.0 s)
15. `close the lid of the toolbox` (441.0-467.0 s)

Mean duration per skill in this task: close lid 24.1 s, move to 57.6 s, open lid 28.4 s, pick up from 21.7 s, place in 20.7 s, wipe hard 9.6 s.

Most frequent skill sentences across all 200 demos:

| skill sentence | count |
| --- | --- |
| `move to the toolbox` | 600 |
| `wipe the steel wool` | 400 |
| `open the lid of the toolbox` | 200 |
| `pick up the steel wool from the toolbox` | 200 |
| `move to the trowel` | 200 |
| `pick up the trowel from the driveway` | 200 |
| `place the trowel in the toolbox` | 200 |
| `move to the scraper` | 200 |
| `place the scraper in the toolbox` | 200 |
| `place the steel wool in the toolbox` | 200 |
| `close the lid of the toolbox` | 200 |
| `pick up the scraper from the driveway` | 199 |
| `move to the steel wool` | 59 |
| `pick up the scraper from the floors` | 1 |

## Sources

Generated by `task_docs/tools/build_task_facts.py` from `BEHAVIOR-1K/bddl3` (goal compiled with the evaluator's wildcard expansion), `datasets/2026-challenge-task-instances`, `data/2026-challenge-metadata-git/annotations`, and the eval JSONs. Raw facts: `task_docs/facts/71_clean_your_rusty_garden_tools.json`. Planner notes: `task_docs/notes/71_clean_your_rusty_garden_tools.md`.
