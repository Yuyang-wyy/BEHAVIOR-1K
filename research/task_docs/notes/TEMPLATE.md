## Planner notes

**Tier:** A | B | C | D — one line why. A = no grasp needed (touch, push, toggle, close). B = pick-and-place of objects that fit the 44 mm jaw span or have a thin handle. C = large, heavy, bimanual, deformable, or container-in-container work. D = needs a state transition (cook, freeze, slice, fill, clean, ignite) on top of pick-and-place.

### Goal in plain words

Two to five sentences: what must be true at the end, which objects are interchangeable, which container or surface choices are free, and what must NOT happen (for example an item left in the wrong bin, a door left open).

### Q traps

Bullets. Literals that are already true at reset and never score, literals that are easy to undo by accident, ordering traps (close the door only after the last item is in), objects that must end up together in the same container, anything that makes the best reachable partial Q different from the naive count.

### Minimal plan

Numbered steps. For each step give:

- the Comet skill sentence to send, in the trained wording (copy it from the demo prompts in the facts: verb template plus cleaned object names, such as `pick up the can of soda from the floors`), or `task sentence` when the whole-task prompt is the better bet, or `code: <skill>` when a scripted skill is clearly better;
- the done-check the planner can verify from RGB, depth or proprioception only (gripper closed and fingers stopped short of fully closed, object no longer visible on the source surface, base stopped, door visibly closed);
- a rough time budget in seconds, from the demo mean duration for that skill.

Keep the plan shorter than the human demo when parts of the demo do not affect the goal, and say so.

### What the demos do differently

Bullets: extra steps the humans take that the goal does not need, alternative orders seen in the demos, bimanual hand-overs, anything a planner copying the demo order should know.

### Hard parts and hacks

Bullets: the physically hardest step and why (object size vs the 44 mm grasp span, height, reach, clutter, distance, articulated joints, particles, tools), realistic failure modes of a VLA here, and any cheap scripted shortcut that is legal (only RGB-D and proprioception at eval) and that the goal allows.

### Hints for the VLM

Bullets: how to recognise the target objects and the correct furniture in the camera images, which room they are in, distractor objects of the same category, and what "done" looks like for each literal.
