# Brief for writing planner notes (shared by all note writers)

You are writing planner notes for BEHAVIOR-1K 2026 challenge tasks. The reader is a high-level VLM planner that prompts a pi0.5 VLA ("Comet") one skill sentence at a time and checks progress from RGB, depth and proprioception only; secondarily, engineers deciding where scripted code skills beat the VLA.

## Read first (once)
- /home/ywang/Behavior/task_docs/README.md — Q scoring, eval rules, Comet prompt templates.
- /home/ywang/Behavior/task_docs/PREDICATES.md — source-verified mechanics of every goal predicate. Rely on it; cite it rather than re-deriving.
- /home/ywang/Behavior/task_docs/notes/TEMPLATE.md — the exact section structure your notes must follow.
- Robot facts: Galaxea R1Pro, two 7-DoF arms, parallel grippers, holonomic base, 4-joint trunk. Assisted grasping registers only across objects or handles <= ~44 mm wide. Rotation odometry drifts. Robot can tip when carrying loads extended high. Time limit = 1.5x human mean demo length.

## For each task assigned to you
1. Read `task_docs/tasks/NN_<task>.md` (rendered facts page) and, where useful, `task_docs/facts/NN_<task>.json` (has full literal list, all top prompts, per-object poses).
2. Check anything the page cannot settle directly in the data:
   - the BDDL: /home/ywang/Behavior/BEHAVIOR-1K/bddl3/bddl/activity_definitions/<task>/problem0.bddl
   - the scene template + 20 public instances: /home/ywang/Behavior/BEHAVIOR-1K/datasets/2026-challenge-task-instances/scene_test/public/<scene>/json/<scene>_task_<task>_0_0_template.json and ..._instances/*-tro_state.json. The template's state.registry.object_registry has articulated `joint_pos` (so you can tell whether a door/drawer starts open) and non_kin states; objects_info.init_info lists every scene object with category and in_rooms (use it to count distractors, e.g. how many cabinets or countertops are in the goal room).
   - task_custom_lists: /home/ywang/Behavior/BEHAVIOR-1K/datasets/2026-challenge-task-instances/metadata/task_custom_lists.json (forced sizes).
   - transition rules / recipes when the task cooks, slices, mixes: /home/ywang/Behavior/BEHAVIOR-1K/bddl3/bddl/generated_data/ and /home/ywang/Behavior/BEHAVIOR-1K/OmniGibson/omnigibson/transition_rules.py
   - OmniGibson source for any mechanic PREDICATES.md does not cover: /home/ywang/Behavior/BEHAVIOR-1K/OmniGibson/omnigibson
   - Demo annotations if you need more than the page shows: /home/ywang/Behavior/data/2026-challenge-metadata-git/annotations/task-00NN/episode_*.json
3. The "true at start" column on the pages is INFERRED from :init. If you find it wrong for a literal (e.g. a door starts open per joint_pos, or a literal is vacuously true), say so explicitly in "Q traps" with the evidence.
4. Write `/home/ywang/Behavior/task_docs/notes/NN_<task>.md` (same stem as the facts file), starting with the line `## Planner notes` and following TEMPLATE.md's sections exactly. Skill sentences in the Minimal plan must be copied from that task's demo prompts (top_prompts / representative episode) — do not invent paraphrases; if a needed step has no demo prompt, say `no trained prompt; closest: ...`.

## Rules
- Only facts you verified from the files above or from PREDICATES.md. Mark anything else "unverified". Never guess object sizes: use custom_lists or say unknown.
- Plain, concise writing: short bullets, one idea per sentence, no filler. Aim for 40-90 lines per task.
- Do not run the simulator, do not use GPUs, do not edit any file other than your own notes files, and do not run render_task_docs.py.
- Finish all assigned tasks. When done, reply with: the list of files written, then up to 8 bullets of cross-task findings that matter for the planner (e.g. a fact-page error you found, a task that is easier or harder than it looks, a reusable hack).
