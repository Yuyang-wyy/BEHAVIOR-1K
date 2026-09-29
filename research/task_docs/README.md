# BEHAVIOR-1K 2026 task docs

One page per challenge task, written for the high-level planner (a VLM) that
prompts the Comet pi0.5 checkpoint skill by skill. Start at [INDEX.md](INDEX.md).

| path | what it is | regenerate? |
| --- | --- | --- |
| `tasks/NN_<task>.md` | the page to read: facts plus planner notes | yes, `tools/render_task_docs.py` |
| `notes/NN_<task>.md` | hand-written planner notes, merged into the page | no, edit by hand |
| `facts/NN_<task>.json` | machine-readable facts (goal literals, scope, poses, demo plans, results) | yes, `tools/build_task_facts.py` |
| `PREDICATES.md` | how each goal predicate is evaluated in OmniGibson, from source | by hand |
| `data/eval_sulab1.json` | per-task closed-loop results pulled from sulab1 | re-pull |
| `data/q_ceiling_overrides.json` | partial-Q ceilings corrected by the notes | by hand |

```bash
/home/ywang/miniconda3/envs/behavior/bin/python task_docs/tools/build_task_facts.py   # ~8 min, offline
python3 task_docs/tools/render_task_docs.py
```

## Evaluation rules that shape every plan

- **Q scoring.** Q = max over ground goal options of (goal literals that were
  false at reset and are true at the end) / (literals in that option). Full
  success is 1.0. Source: `OmniGibson/omnigibson/metrics/task_metric.py`.
- **Literals already true at reset never score.** 33 of 100 tasks have them
  according to `:init`, and the planner notes found more that only geometry
  reveals (`installing_a_modem`, `sorting_books_on_shelf`). The worst ceilings
  short of success: `sorting_bottles_cans_and_paper` 0.375, `sorting_books_on_shelf`
  0.36, `canning_food` 0.4, `can_meat` 0.44 (the jars start inside the closed
  cabinet, so only the bratwursts score), `put_together_a_basic_pruning_kit` 0.5.
  Opening a cabinet that started closed and leaving it open costs success but
  no partial Q; re-closing it earns nothing either.
- **Articulated objects that start open** (a laptop, a car trunk) are read from
  the recorded joint positions of all 20 instances; closing them does score.
- **One BDDL quirk:** the parser keeps only the first top-level goal clause.
  Only `loading_the_car` is affected: its "close the trunk" clause is ignored.
- **Time limit** is 1.5x the mean human demo length, at 30 steps per second.
  It ranges from under two minutes to over half an hour; each page lists it.
- **Instances.** Public test ids 301-320. The leaderboard uses 301-310, one
  rollout each; 311-320 are the dev set. Hidden test is 321-340.
- **Inputs at eval** are RGB, depth and proprioception only. No object poses,
  no segmentation, no global robot pose.
- **Grasping** is assisted. A runtime measurement found the widest finger-to-finger
  grasp ray is 44 mm, but that is not a hard feasibility limit: humans in the
  demos pick 75 mm soda cans, logs and boxes one-handed, and zero-shot Comet
  fully solved `picking_up_trash`. How those wider grasps register is
  unverified. Flat objects lying on a surface (books, plates, tiles) are
  still hard; the demos push them past the table edge before picking them up.

## How Comet was trained to be prompted

The fine-tuned checkpoint (run comet-pt50-2026-v1, exports at
`local_eval/exports/step-000{24,40}000`) saw one of two prompts per frame,
50/50:

1. **The task sentence** from `meta/tasks.jsonl`. For tasks 0-49 the Comet
   pretraining sentence was used where it differs (listed on each page).
2. **The skill sentence** of the annotated segment covering that frame, built by
   `reproductions/winner_2025_task40/scripts/build_comet_prompts.py`.

Skill sentences follow fixed templates. Using these exact shapes keeps the
prompt in distribution:

| verb | template | demo segments |
| --- | --- | --- |
| move to | `move to the <obj>` | 143,566 |
| pick up from | `pick up the <obj> from the <support>` | 93,090 |
| place in | `place the <obj> in the <container>` | 43,360 |
| place on | `place the <obj> on the <support>` | 34,521 |
| push to | `push the <obj> to the <target>` | 13,324 |
| open door / close door | `open the door of the <obj>` | 12,810 / 10,122 |
| place on next to | `place the <obj> on the <support> next to the <obj2>` | 10,430 |
| chop | `chop the <tool> with the <obj>` (tool first, e.g. `chop the carving knife with the half head cabbage 212`) | 8,652 |
| sweep surface | `sweep the <tool>` (e.g. `sweep the broom`) | 5,003 |
| pour | `pour the <obj> into the <target>` | 4,400 |
| turn on switch / turn off switch | `turn on the <obj>` (e.g. `turn on the lighter`) | 4,400 / 2,195 |
| hand over | `hand over the <obj> with the left` | 2,879 |
| open lid / close lid | `open the lid of the <obj>` | 2,111 / 2,399 |
| wipe hard | `wipe the <tool>` (e.g. `wipe the scrub brush`) | 1,708 |
| open drawer / close drawer | `open the drawer of the <obj>` | 1,114 / 1,117 |
| others | `turn to the <obj>`, `insert the <obj> into the <obj2>`, `spray the <tool> with the <target>`, `tip over the <obj>`, `hold`/`release the <obj>`, `attach the <obj> to the <obj2>`, `hang the <obj> on the <obj2>`, `ignite the <tool> with the <target>`, `press the <obj>`, `pull tray the <obj>` | under 1,300 each |

The annotations are not always grammatical: tools come first for chop, sweep, wipe, spray and ignite, and objects created by slicing keep their numeric id. Copy the strings as they are.

Object names are the scene category with the model id removed and
underscores turned into spaces: `can of soda`, `bottom cabinet`, `trash can`.
The floor is always `the floors`. A spatial word from the annotation can
precede the object (`the left bottom cabinet`, `the in_front_of coffee table`).
Each page lists the 15 most frequent skill sentences for that task; prefer
those strings over paraphrases.

Serving notes: the server replans every 32 steps (receding horizon). When the
prompt changes, clear the action queue so the new prompt takes effect on the
next step. The zero-shot Comet pt50 checkpoint only knows tasks 0-49 and was
pretrained with its own instruction hierarchy; the skill wording above is ours
and has not been tested on it.

## Caveats

- "True at start" is inferred from the BDDL `:init` block. The simulator can
  differ, for example a door sampled ajar. Confirm critical cases with
  `BEHAVIOR-1K/scripts/aspire_radio/task_feasibility_probe.py`.
- Closed-loop results on each page are one rollout on instance 311. A
  difference below 0.3 on one task is noise.
- Demo skill plans come from 200 annotated demos per task
  (`data/2026-challenge-metadata-git/annotations`). Humans often do things the
  goal does not need, such as carrying the trash can to the cans or picking
  up the radio before pressing it. The planner notes flag these.
