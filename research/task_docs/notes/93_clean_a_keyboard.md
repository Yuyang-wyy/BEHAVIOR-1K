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
