# Comet supervision research (BEHAVIOR-1K 2026 challenge)

Question: can a supervisor raise Q over the Comet pi0.5 policy running alone on the task sentence?
Comet checkpoints: old ft 40k (`step-00040000`) and v2 (`v2-step-00040000`, skill fine-tuned; serve with
`B1K_MAX_TOKEN_LEN=256`). All scores are official Q from the evaluator, instances 311-320 (dev), seed 0 unless noted.

## Where to look

| path | what |
| --- | --- |
| `research/task_docs/` | one page per task (scene, goal, Q traps, demo skill sentences, plan), plus `PREDICATES.md` |
| `research/task_docs/supervision/README.md` | per-task supervision results, failure points, and why each is or is not fixable |
| `scripts/comet_planner/` | harness v5: interactive episode server (`planner_episode.py`), client, batch runner, scripted grasp/place supervisor |
| `scripts/comet_planner_v6..v8/` | takeover variants tried on other tasks (drop-in container, gated takeover) |
| `scripts/comet_planner_v9/` | skill-prompt supervisor with optional scripted grasp fallback / scripted place |
| `scripts/comet_planner_v10/` | same harness + `seq_supervisor.py` (demo skill sequencer, retired) + `poke_marker.py` code skill + GPU/hang guards |

## Harness in one paragraph

`planner_episode.py` runs one official-eval episode and pauses every 150 steps (5 s). A client sends one command
per checkpoint: `global` (task sentence), `skill "<sentence>"` (Comet prompt override via the patched
`eval_b1k_wrapper.py`), or a code skill / primitive: `base`, `hand`, `grip`, `reach`, `point`, `look`, `trunk`,
`detect`, `auto_grasp`, `auto_place`. Only legal inputs are used (RGB-D, proprioception, robot kinematics);
`objinfo` is privileged and used for dev only. `wait_gpu.sh` blocks while a foreign job holds the GPU and
`hang_watch.sh` kills an episode whose trace stops for 5 min.

## Results so far

| task | Comet alone | supervised | how |
| --- | --- | --- | --- |
| picking_up_trash (311-320) | 0.40 (v2), 0.37 (old) | 0.70 (v2), 0.77 (old) | code-as-policy reflexes: scripted grasp when a hand stalls near a can, scripted place that levels the held bin |
| cook_hot_dogs (311, 313, 315) | 0, 0, 0 | 1.0, 0, 0 | skill prompts for fridge/microwave steps + navigation help to reach the microwave |
| turning_out_all_lights (311, 313, 314) | 0.4, 0, 0 | 0.2, 0.4, 0.4 | scripted drives to the right room + `poke_marker.py` (now also 1.44 m switches, squared to the wall) |
| tidying_bedroom (311-315) | 0.60 | 0.60 | no net gain: sandals already fine, flat book hard to grasp |
| spraying_for_bugs (311-312) | 0, 0 | 0.5, 0 | atomizer toggling and nozzle aim are inside Comet's manipulation |
| collecting_aluminum_cans / putting_away_toys | 0.53 / 0.65 | 0.27-0.46 / noise | takeovers hurt when Comet is already progressing |

Noise: one seed per instance moves a 5-instance mean by 0.1-0.3, so only the picking_up_trash gain is
well established. The others are 1-5 episodes and should be read as hints.

## Lessons

- Supervision pays off where Comet has a specific, repeatable failure; fast code skills fix those best.
- Live 5 s prompting is too slow for sub-2 s stalls, but works for strategic errors: wrong room, wrong
  object, a skill that stalls at a fixed step.
- Skill prompts on v2: good for local manipulation (open/close doors, pick from shelf, place in microwave),
  unreliable for navigation ("move to X" often goes to a lookalike: oven for microwave, TV bench for nightstand,
  microwave button for a lamp).
- Toggleable objects show a legal green (on) / red (off) marker; use it to verify presses.
