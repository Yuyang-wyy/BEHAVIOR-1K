# BDDL goal predicates: how the evaluator decides them

This is a reference for the goal predicates used by the 100 BEHAVIOR-1K 2026 challenge tasks, checked against the source code the evaluator runs. It is written for anyone writing per-task planner notes and for the high-level planner that prompts Comet one skill at a time.

**Paths.** Paths such as `object_states/x.py:N` are relative to `BEHAVIOR-1K/OmniGibson/omnigibson/`. Paths starting `bddl/` are relative to `BEHAVIOR-1K/bddl3/`. The per-synset numbers (cook temperatures, tool conditions and so on) are the runtime abilities that `bddl/object_taxonomy.py` loads from `bddl/generated_data/output_hierarchy_properties.json`. They were queried directly, so they are not copied from the CSVs.

**Timing.** Evaluation runs at 30 Hz for actions and state updates and 120 Hz for physics (`eval/utils/eval_utils.py:198-200`). One "step" below means one env step, which is 1/30 s. Object states and transition rules update once per env step in `Simulator._non_physics_step` (`simulator.py:1202`).

**Labels.** "Derived" marks a consequence read directly from the code but not reproduced in the simulator. "Not verified" marks something the source doesn't settle.

---

## 0. How a literal becomes True or False

- `BehaviorTask._evaluate_predicate` (`tasks/behavior_task.py:167`) looks up the BDDL instance in `object_scope` and calls `evaluate_bddl_predicate` (`utils/bddl_utils.py:207`).
- `real(x)` is `x is not None`, `future(x)` is `x is None`, and `insource` is always True (`bddl_utils.py:214-219`).
- Every other predicate goes through `PREDICATE_TO_STATE` (`bddl_utils.py:180`). **If any argument is `None` or not initialized, the predicate returns False** (`bddl_utils.py:224-236`). So once an object has been removed (sliced, diced, or consumed by a recipe), `inside/ontop/...` on it are False and `not inside/...` on it are True.
- The scope changes during an episode (`behavior_task.py:628-682`):
  - A newly spawned object fills the **first** `None` slot whose category matches it.
  - A removed object's slot is set to `None`.
  - A particle system fills its slot when the system is initialized, which happens when its first particle is created, and empties it when the system is cleared.
- Quantifiers (`bddl/bddl/condition_evaluation.py`):
  - `forall` means all children, and `exists` means any child.
  - **`forn (N)` succeeds only if exactly N children hold** (`:305`). Satisfying N+1 fails the success check, although partial Q can still reach 1.0 (see §1). This appears in tasks 4, 5, 9 and 99.
  - `forpairs` needs a perfect matching (`:365-375`).

## 1. Q scoring (`metrics/task_metric.py`)

- **At reset** (`task_metric.py:22-25`), every literal of every ground goal option in `env.task.ground_goal_state_options` is evaluated and stored.
- **At episode end** (`:35-47`):
  - If `env.task.success` is set, Q = 1.0. Success is set by the `PredicateGoal` termination (`termination_conditions/predicate_goal.py:34`, `tasks/task_base.py:363`) on the first step where the whole goal holds, and that step also ends the episode.
  - Otherwise Q = max over options of `#(literals False at reset AND True at the final step) / #(literals in option)`.
- **Ground options** are every way of satisfying the goal once `or`, `exists`, `forn` and `forpairs` are expanded (`bddl/bddl/condition_evaluation.py:741`). Options that contain both P and `not P` are dropped. Each `not` literal counts as one literal.
- **Consequences for planning:**
  - A literal that is already True at reset never scores, although it still counts in the denominator. Examples: a cabinet that starts closed under `not open`, an object that already starts inside its target, or `not toggled_on lighter` when the lighter starts off. The best partial Q for a task is therefore below 1.0 whenever such literals exist (see the "max partial Q" column in `INDEX.md`).
  - Undoing such a literal and then redoing it earns nothing. Leaving it undone (for example, a fridge left open) still blocks full success.
  - Partial Q reads only the **final** state. An object placed correctly earlier but knocked off later scores 0. Nothing is credited for "was true at some point".
  - Success is checked every step. The instant everything holds at once, the episode ends with Q = 1.0, so there is no need to hold the state afterwards.

---

## 2. Shared machinery (read once)

**Object AABB** (`prims/entity_prim.py:1393`, read through `object_states/aabb.py:5`)
- World-axis-aligned min/max over the collision points of **all links**, including opened doors and drawers.

**Container volume** (`fillable` / `openfillable` meta links, `object_states/contains.py:14`)
- `link.check_points_in_volume` (`prims/rigid_prim.py:627`) tests a point against the link's visual meshes. Those meshes are treated as convex hulls through a Delaunay test (`prims/geom_prim.py:210`).
- These links must exist in the object's USD at runtime. `misc/metadata.json` does not tell you whether they do (verified earlier in this project).

**Vertical adjacency** (`object_states/adjacency.py:160`, `compute_adjacencies` at `:64`)
- It casts **one ray up and one ray down** from the object's own top and bottom surfaces, at the x-y of its AABB centre. The start points come from pre-shooting a ray that finds the object's own surface (`:97-126`).
- Rays run up to 5 m (`MAX_DISTANCE_VERTICAL`) with `only_closest=False`, so **every** object hit along the ray is a neighbour, not just the nearest one.
- The object's own links are ignored. Hits are mapped to whole objects: a hit on any link of a cabinet or shelf counts as the cabinet or shelf.

**Horizontal adjacency** (`adjacency.py:184`)
- It casts 20 rays (5 planes x 2 axes x ±, 22.5° apart) from the AABB centre, horizontally, up to 5 m, recording all hits.

**Contact** (`utils/usd_utils.py:683`, `RigidContactAPI.is_in_contact`)
- This is PhysX contact-matrix membership with no force threshold.
- `current_only=True` means the latest physics substep only. `current_only=False` means any substep since the last env step. Transition rules use the latter.

**Temperature model** (`object_states/temperature.py`)
- Ambient temperature is 23 °C.
- Every step, `T += (23 − T)·0.02·dt` (`:56`).
- Every active heat or cold source affecting the object adds `(T_src − T)·rate·dt` (`:39`), with `dt` = 1/30 s.
- For one source, T converges exponentially to `T_ss = (rate·T_src + 0.02·23)/(rate + 0.02)`, with time constant `1/(rate+0.02)`. That is 8.3 s at rate 0.1.
- Which objects a source affects (`object_states/heat_source_or_sink.py:199-285`):
  - **`requires_inside` sources** (microwave, oven, fridge, toaster): the object must overlap the source's AABB box (`:224`) **and** satisfy `Inside(obj, source)` (`:250`). So its AABB centre must be in the source's fillable volume.
  - **Other sources** (stove, burner, grill, lighter, anything on fire): any collision shape of the object must overlap a sphere of radius `distance_threshold` = **0.2 m** (default `:24`, overlap at `:262`). The sphere is centred on the `heatsource` meta link, or on the root-link AABB centre when there is no such link.
- A source is active only if it is toggled on (when `requires_toggled_on`) **and** not open (when `requires_closed`) (`:165-175`).
- Heat does not conduct between objects. A pan does not heat the food in it. The food itself must be inside the oven or microwave, or within 0.2 m of the burner.

Source parameters (runtime KB):

| source | T_src (°C) | rate | needs on | needs closed | needs inside | T_ss (°C) |
|---|---|---|---|---|---|---|
| stove.n.01 | 1980 | 0.1 | yes | no | no | ~1653 |
| oven.n.01 | 250 | 0.1 | yes | yes | yes | ~212 |
| microwave.n.02 | 100 | 0.1 | yes | yes | yes | ~87 |
| electric_refrigerator.n.01 (cold) | −18 | 0.1 | no | yes | yes | ~−11.2 |
| cigar_lighter.n.01 | 1000 | 0.1 | yes | no | no | ~837 |
| anything OnFire | 1000 | 0.04 | – | – | no | ~674 |

---

## 3. `inside` (232) and `not inside` (13)

- **Class:** `Inside` at `object_states/inside.py:28`. Test at `_get_value`, `:240-263`.
- **Test** (the object is A, the container is B):
  1. A's AABB centre lies inside B's whole-object AABB (`:246-253`).
  2. The same centre point lies in the volume of **any** `fillable`/`openfillable` meta link of B (`:259-263`).
- **Not required:**
  - No contact is needed. An object floating or **held by the gripper** with its centre in the volume counts.
  - B does not have to be closed.
  - There is no size or fit check. Only one point is tested.
- **What the robot does:**
  - Pick A, then carry it and release it so that its centre ends up in the container volume.
  - For fridges, cabinets and microwaves, open the door or drawer first. For drawers, the volume presumably moves with the drawer, but that is not verified.
  - A grasp is needed for anything moved by hand. The R1Pro assisted grasp only closes on parts up to ~44 mm across (a finger-to-finger ray through the object is required), so wide objects cannot be picked up conventionally. They have to be pushed, or the task needs a graspable handle.
- **Silent failures:**
  - **No volume.** A container with no fillable/openfillable link in its runtime USD can never satisfy `inside`. The failure is silent: the loop over links finds nothing and returns False.
  - **Centre, not body.** A long object (a book or a bottle) poking out still counts if its AABB centre is inside the volume. A small object resting on the rim does not count, even when it looks inside.
  - **Volumes are convex hulls of the fillable mesh.** They typically cover the interior cavity or shelf space, not the walls. An object sitting *on top of* a cabinet is not inside it.
  - **Closing onto the object.** Closing a door or lid can push A out of the volume, or wedge it so its centre is outside. Re-check after closing. Cabinet or fridge goals usually pair `inside` with `not open`, and both must hold at the end.
  - **Knock-on displacement.** Knocking a container moves its volume. An object that falls out of a tipped bin loses the literal.
  - **Removed objects.** If A has been removed from the scene, `inside` is False and `not inside` is True.
- **`not inside`:**
  - Scores only if A was inside at reset. Examples: `not inside easter_egg basket`, and the task-52 variants on the bucket.
  - Take A out so that its AABB centre is outside the volume. Moving it just past the rim is enough.

## 4. `ontop` (103)

- **Class:** `OnTop` at `object_states/on_top.py:12`. Test at `:43-52`.
- **Test:** `Touching(A, B)` **and** B appears among A's downward neighbours **and** B does *not* appear among A's upward neighbours (`:47-52`).
  - Touching means mutual rigid contact (§8).
  - The downward check uses the single ray down from A's bottom, at the x-y of A's AABB centre.
  - The upward check uses the single ray up from A's top.
- **What the robot does:** grasp A (or push it), place it so it rests on B with A's **AABB-centre x-y over B's geometry**, and release it.
- **Silent failures:**
  - **Overhang.** If A's centre x-y overhangs B's edge, or sits over a gap in B (a slatted rack, a hole in a grill, the gap between two cushions), the downward ray misses B and the literal is False even though A touches B.
  - **Geometry of B above A (derived).** If *any part of B itself* is directly above A's centre within 5 m, the literal is False: B is then in A's upward neighbours. Examples: the upper board of a multi-shelf unit, a faucet over a sink basin, a hutch over a desk, the shelf above inside a fridge. Placing on the **topmost** surface of such objects avoids this. Other objects above A (a wall cabinet above a countertop) do not matter.
  - **Stacking needs direct contact.** For A on C on B, B is in A's downward neighbours, but A does not touch B, so `ontop A B` is False.
  - **Physics shifts.** A resting on a sloped or rounded surface can roll or slide off. Re-check after releasing.
  - **Holding still counts.** An object pressed onto B while still held satisfies the literal. Releasing it can make it fall off.
- **`ontop X floor`:** the floor is below everything in the room, so any object resting on the floor scores. An object on a rug may not score: the rug is a separate object, so the object does not touch the floor.

## 5. `nextto` (41)

- **Class:** `NextTo` at `object_states/next_to.py:9`. Test at `:16-58`.
- **Test:**
  1. `d` = Euclidean norm of the per-axis gap between the two AABBs (0 on any axis where they overlap).
  2. `L` = mean over x, y, z of `(extent_A + extent_B)`.
  3. If `d > L/6`, the literal is False (`next_to.py:39`).
  4. Otherwise B must be hit by one of A's 20 horizontal rays from A's AABB centre, or A must be hit by one of B's rays (`:43-58`).
- **Scale of the threshold:**
  - Two 10 cm objects: gap ≤ ~3.3 cm.
  - A sandal (0.25 × 0.10 × 0.08 m) and a bed (2.0 × 1.6 × 0.6 m): gap ≤ ~0.26 m.
  - The allowed gap grows with the **larger** object. Small–small pairs must be almost touching.
- **Height matters:** the gap includes vertical separation, and the rays are horizontal at the AABB-centre heights. An object on a table is usually *not* `nextto` a chair beside the table, even when it looks adjacent from above.
- **What the robot does:** grasp A and place it on the same support surface as B, beside it, with a small gap.
- **Silent failures:**
  - A gap that looks small but exceeds L/6 for a small–small pair.
  - Being at a different height from B.
  - A third object between them does not block the literal (rays record all hits), but the gap limit still applies.

## 6. `not open` (33); `open` is not used in goals

- **Class:** `Open` at `object_states/open_state.py:118`. Test at `:172-201`.
- **Test:** the relevant joints come from the object's metadata `openable_joint_ids`, falling back to **all** joints (`:71-115`). A joint is "open" if it is past 5 % of its range from the closed end:
  - `threshold = 0.95·closed_end + 0.05·open_end`, for both revolute and prismatic joints (`:19-22`, `:47-50`, `:68`).
  - The object is open if **any** relevant joint is open (`:198`).
  - For `openable_both_sides` objects, it must be open when viewed from both sign conventions (`:182-201`).
- **So `not open` needs every relevant door and drawer within 5 % of closed.** Examples: a 90° door within ~4.5°; a 40 cm drawer within 2 cm.
- **What the robot does:** push or swing every door and drawer shut. Closing can be done by pushing, so no grasp is required. Opening a door usually needs the handle, and the handle must be ≤ ~44 mm to be graspable.
- **Silent failures:**
  - **Rebound.** A door that rebounds or is left slightly ajar from a collision stays "open".
  - **Scoring.** It usually starts closed, so it usually scores nothing (§1) but still blocks success.
  - **Multi-door and multi-drawer furniture.** A cabinet counts as open if *any* door or drawer is open, including one the robot bumped by accident.
  - **Side effects on appliances.** Opening the microwave turns it off (§11). Opening the oven or fridge stops heating or cooling (§2).

## 7. `real` (28), `not real` (5), and slicing / dicing

- **Class:** none. `real(x)` = the scope slot is not `None` (`bddl_utils.py:218-219`).
  - A future object's slot fills when an object of its category is spawned, into the first free matching slot (`behavior_task.py:628-642`).
  - A future particle system's slot fills when the system is initialized, i.e. when its first particle is created (`:658-669`).
  - `not real(x)` becomes True when x is removed from the scene (`:645-656`).

**Slicing** (`SlicingRule`, `transition_rules.py:923-996`)
- **Condition** (`:938-939`): the `sliceable` object is in contact (`current_only=False`) with **any link of any `slicer`-ability object**, **and** that slicer's `SlicerActive` is True.
  - No blade meta link is consulted: the `slicer` ability has no link requirement (`object_states/factory.py:68`).
  - Whether a knife's handle contact also slices, or whether knife assets have separate blade/handle rigid links, is not verified.
- **Slicers in the runtime KB:** `carving_knife.n.01`, `parer.n.02`, `cleaver.n.01`, `ax.n.01`. The ability is on the tool, so no chopping board is needed.
- **Result:**
  - The whole object is **removed** (`:994`). Its `real` becomes False and every spatial literal about it becomes False.
  - Parts are spawned from the asset's `object_parts` metadata. All 207 KB slicing rules produce **2 halves** (`bddl/.../tm_jsons/slicing.json`). The halves spawn at the part poses and inherit non-kinematic state such as temperature, cooked and max temperature (`:984-990`).
- **Examples from the goals:**
  - 8 × `real half__log` requires 4 logs sliced (the halves fill slots _1.._8 in order).
  - 2 × `real half__hard-boiled_egg` requires 1 egg sliced.
  - Slicing a zucchini, pepper or beet makes `not real ?zucchini` (etc.) True.

**SlicerActive** (`object_states/slicer_active.py:17`)
- It starts True.
- In the step after the slicer touches any `sliceable` object, it becomes False (`:74-76`).
- It re-arms after `REACTIVATION_DELAY` = 2.0 s (60 steps) of **not touching any sliceable** object (`:14`, `:41`, `:85-103`).
- Halves are `diceable`, not `sliceable`. Resting the knife on them therefore does **not** hold the cooldown.

**Dicing** (`DicingRule`, `transition_rules.py:999-1035`)
- **Condition:** the same test, with a `diceable` object and an active slicer.
- **Result:** the diceable object (for example `half__zucchini`, which is diceable in the KB) is **removed**. Particles of system `diced__<category>` are generated from its root-link volume, or `cooked__diced__<category>` if the half was Cooked (`:1022-1032`). The particle count is not verified.
- **So `real diced__X` needs two cuts:** slice the whole X, then touch a half again after the knife re-arms.
- **Halves that must survive (derived):** in halve_an_egg and cook_brussels_sprouts, the goal needs `real half__...`. Those halves **are diceable** (`half__hard-boiled_egg`, `half__brussels_sprouts`). If the knife is still touching a half 2 s after the cut, it re-arms and **dices the half, destroying it**. Lift the knife away right after the cut. `half__log` is not diceable, so axes are safe.

**Grasp and failures**
- A grasp on the knife or axe is needed. Knife handles are usually narrow; axe handle width is not verified against the 44 mm limit.
- If the target object moves on contact (it rolls away), no contact persists. A single frame of contact is enough, because the rule reads all physics substeps.

**Cooking of particles** (`CookingPhysicalParticleRule`, `transition_rules.py:1908-2020`)
- All particles of X inside a `heatable` container's fillable volume become `cooked__X` as soon as the container is `Heated`: its own temperature ≥ 40 °C, the default `heat_temperature` (`object_states/heated.py:10`, `:41`; condition at `transition_rules.py:1973`).
- The pan must itself be within 0.2 m of the burner (§2). On a stove this takes well under a second.
- This path gives `cooked__diced__head_cabbage` / `cooked__diced__chili` in cook_cabbage, and `cooked__popcorn` (a `substance_cooking` rule) when the popcorn bag is heated inside a closed, running microwave (~2.6 s to reach 40 °C).
- **Recipe outputs:** a pizza on a cookie sheet in an oven is produced by `CookingObjectRule` recipes (`bddl/.../tm_jsons/heat_cook.json`). Recipe preconditions are task-specific; read the JSON.

## 8. `touching` (10) and `not touching` (4)

- **Class:** `Touching` at `object_states/touching.py:7`. Test at `:29-38`.
- **Test:** rigid contact on the latest physics substep (`current_only=True`), checked in both directions (`:38`).
  - **If both objects are kinematic-only** (fixed-base, no joints, no attachment; `utils/usd_utils.py:2690`), the literal is **always False** (`:11-12`).
  - Cloth objects use the cloth's contact list instead.
- **What the robot does:** place A in resting contact with B. Examples: log on log in stacking_wood, a shoe on the hallstand. Needs a grasp to move A.
- **`not touching A floor`** (putting_shoes_on_rack): A must not touch the floor at all. A shoe partly resting on the floor fails.
- **Failures:**
  - A resting a few mm away, or bouncing off, is not in contact.
  - Contact is instantaneous, so a jittering object can flicker.
  - Contact through a third object does not count.

## 9. `under` (5)

- **Class:** `Under` at `object_states/under.py:11`. Test at `:42-51`.
- **Test** (all must hold):
  - B is among A's **upward** neighbours (the ray up from A's top at A's centre x-y hits B within 5 m).
  - B is not among A's downward neighbours.
  - A is not among B's upward neighbours.
- **Not required:** contact and closeness. B only has to be somewhere directly above A's centre.
- **What the robot does:** put A on the floor (or a lower surface) with its centre directly below B's geometry. Examples: mousetrap under sink, gift box under Christmas tree, computer under desk.
- **Failures:**
  - A's centre x-y is not under solid geometry of B, for example in the open knee-space of a desk beyond the top's edge, or beside a pedestal sink. The branches of a tree mesh may be sparse, so this is not verified for the Christmas tree.
- **Grasp:** needed to move A.

## 10. `attached` (4)

- **Class:** `AttachedTo` at `object_states/attached_to.py:78`. Value at `:311` (`other == self.parent`). Auto-attach at `_update`, `:219-240`.
- **Auto-attach rule:** every step, while A (the child) is unattached, the code:
  1. looks at every object A is in contact with (`current_only=False`),
  2. tries to pair a **male** `attachment` meta link of A (id ending in `M`) with an unoccupied **female** link of B that has the same id ending in `F` (`:363-386`),
  3. requires those two links to be within **5 cm** and **15°** of each other (`:34-35`, `:343-358`).
  If all of this holds, a fixed joint is created. No release is needed.
- **Joint breakage:** the joint breaks above 5000 N or 10000 N·m (`:37-38`, `:213-217`), and A is then detached.
- **What the robot does:** grasp A and bring its mounting point onto B's mounting point with the right orientation, touching B. Examples: poster onto wall nail, camera onto tripod, cabinet door onto base, smoke alarm onto nail.
- **Failures:**
  - **Orientation outside 15°.** For a VLA this is the hard part: the poster must face the right way, and the camera must sit upright on the mount.
  - **Female link occupied.** If the female link is already used, it cannot be reused.
  - **Wrong parent first.** A child can attach to only one parent. If it first latches onto the wrong object with matching links, it stays there until the joint breaks.
  - **Meta links not verified.** The exact `attachment` meta-link placement and ids per asset are not verified here.

## 11. `toggled_on` (5) and `not toggled_on` (6)

- **Class:** `ToggledOn` at `object_states/toggle.py:24`. Value is a stored bool (`:116`). Update at `:207-232`.
- **Test, every step:**
  - `robot_can_toggle` = a robot **finger link is in contact** with the object (`:79-110`, `:215`) **and** a finger link overlaps a sphere at the `togglebutton` meta link (`:189-203`, `:219`). The sphere radius is `min(marker extent · scale)`, about 11 mm on the radio.
  - A counter increments while `robot_can_toggle` holds and resets to 0 otherwise.
  - When the counter **equals** `CAN_TOGGLE_STEPS` = 5 (`:21`, `:231`), the value flips.
  - Holding longer does nothing more. **A second, separate 5-step touch flips it back.**
- **`requires_closed` toggleables** (runtime KB): microwave, dishwasher, washer, clothes dryer, blender.
  - While these are open, the value is forced False and the counter is reset (`:209-212`).
  - **Opening the microwave turns it off.**
  - **Close first, then press.** A press while the door is open does nothing lasting.
- **What the robot does:** press the button with a fingertip and hold for ≥ 5 steps (0.17 s), then withdraw. No grasp is needed.
- **Failures:**
  - Missing the small sphere: touching the body elsewhere does nothing.
  - Brushing the button again later turns it back off.
  - For `not toggled_on` (a switch or lamp that starts on), exactly one clean press. It scores only if the object was on at reset.
  - `not toggled_on cigar_lighter` in setting_the_fire is usually True at reset, so it does not score, but the lighter must be switched back off for success.
- **Toggled-on tools also matter:**
  - The atomizers (§12) and the vacuum only work while toggled on.
  - The lighter heats only while on (§14).

## 12. `covered` (4) and `not covered` (21)

- **Class:** `Covered` at `object_states/covered.py:24`. Test at `:55-81`.
- **Which systems appear in the goals:** dust, dirt, debris, mud, sand, rust, insectifuge and pesticide. All of them are **visual** particle systems in the KB.
  - **Visual systems:** True iff the object's attachment group has **≥ 1 particle** (`VISUAL_PARTICLE_THRESHOLD` = 1, `:12`, `:64`).
  - **Physical systems:** ≥ 1 particle in contact (`:65-74`). None appear in these goals.
- **`not covered` means every single particle on that object must be gone.** Initial sampling puts at most 20 visual particles per object (`MAX_VISUAL_PARTICLES`, `:15`). The exact count per task instance is not verified.

**Removal with a ParticleRemover tool** (`object_states/particle_modifier.py:816`)
- **ADJACENCY method** (brushes, broom, steel wool, pipe cleaner, gloves):
  - Every step (`N_STEPS_PER_REMOVAL` = 1, `:52`), any visual particle of an allowed system whose position lies inside the remover link's **visual AABB grown by 0.02 m** is deleted (`:66`, `:524-531`, `:927-949`).
  - The remover link is the `particleremover` meta link if the tool has one, otherwise the root link (`:985-988`).
  - The particles live on the dirty object's surface, so the tool's box must be swept over **every** particle location. Touching one spot does not clean the object.
- **PROJECTION method** (vacuum): particles inside the projection mesh are removed while the tool is toggled on.
- **Remover conditions** (runtime KB):
  - A condition of `[]` means always.
  - `None` means never. A system missing from the list falls back to `default_visual_conditions`.
  - The limit is 200 visual particles removed per system per tool (`VISUAL_PARTICLES_REMOVAL_LIMIT`, `:59`). After that the tool is "Saturated" and stops (`:704-708`). Whether this ever resets is not verified.

| tool | dust | dirt | debris | mud | rust | sand (default) |
|---|---|---|---|---|---|---|
| broom.n.01 | always | always | always | always | never | always |
| scrub_brush.n.01, pipe_cleaner.n.01 | always | always | always | needs saturated water | never | always |
| steel_wool.n.01 | never | never | never | never | always | never |
| vacuum.n.04 (projection) | toggled_on | toggled_on | toggled_on | never | never | toggled_on |
| boxing_glove.n.01 (itself a remover) | never | never | never | saturated water | never | never |

**Washer path** (`WasherRule`, `transition_rules.py:813-890`)
- It fires **once, on the step the washer changes to (toggled_on AND closed)** (`ChangeConditionWrapper`, `:455-500`; conditions at `:753-754`).
- For each system the washer `Contains`, where dust, dirt, debris and mud are removed unconditionally (`tm_jsons/washer.json`), it clears `Covered` on every object with any collision point inside the washer volume.
- **Order:** load the items, close the door, then press start. Re-pressing requires toggling off and on again.

**Applying particles with a ParticleApplier** (for `covered`: insectifuge on pot plants, pesticide on trees)
- The atomizer's condition is `toggled_on: True`, with the PROJECTION method.
- Every 5 steps (`:51`) rays are cast inside the spray cone. Each hit object receives up to 2 visual particles (`:47`) in its own group (`:1312-1354`).
- One particle landing on the target is enough. So: grasp the atomizer, toggle it on, and point the nozzle at each target from close range.
- Cone size comes from asset annotation and is not verified.

**Grasp and failures**
- **Grasp:** a grasp on the tool is needed, unless the dirty object is carried to the washer. For the known touch-is-enough case, see the clean_a_keyboard notes.
- **Failures:**
  - A missed patch, even one particle, keeps `covered` True.
  - Using a tool whose condition for that system is `never`.
  - A saturated-water condition that was never met.
  - A tool that is not in fact overlapping the particles. The AABB is axis-aligned in the world, so a rotated brush has a larger or smaller box than it looks.

## 13. `contains` (4), `not contains` (2), `filled` (2)

- **Classes:** `ContainedParticles` / `Contains` at `object_states/contains.py:27/92`; `Filled` at `object_states/filled.py:15`.
- **Which volume is used:** `ContainedParticles` uses **one** container link, the first `fillable`/`openfillable` link found (`object_states/link_based_state_mixin.py:90-96`, `:120-125`). By contrast, `Inside` checks all container links. Visual particles are offset 1 cm along their normal before the test (`contains.py:15`, `:65-70`).
- **`contains C S`:** at least 1 particle of S is in C's volume (`contains.py:95`).
- **`not contains C S`:** zero particles of S in C's volume.
  - In canning_food this separates the steak bowl from the pineapple bowl: a single stray particle in the wrong bowl breaks it.
  - If system S does not exist yet, `contains` is False and `not contains` is True, because the argument is `None` (§0).
- **`filled C S`:** `(2r)^3 · n_in_volume / volume(link) > 0.2` (`filled.py:25-31`). This models particles as cubes filling more than 20 % of the fillable volume. The particle radius of diced systems is not verified. With few diced particles in a big bowl, 20 % may be unreachable; use the smallest bowl.
- **What the robot does:**
  - Pour or scrape particles into C, which requires grasping and tilting the source container.
  - Alternatively, create them inside C: dice over a bowl, or cook diced particles already sitting in the pan (§7).
- **Failures:**
  - Particles bouncing out.
  - Particles above the rim of the volume.
  - Pouring into the wrong one of two fillable sub-volumes.

## 14. `on_fire` (3)

- **Class:** `OnFire` at `object_states/on_fire.py:15`, a `HeatSourceOrSink`. Test at `:86-87`.
- **Test:** `Temperature ≥ ignition_temperature`. Firewood and newspaper use 250 °C in the KB (`flammable`: ignition 250, fire 1000, rate 0.04, distance 0.2).
- **It latches:** while on fire, `_update` resets the object's temperature to 1000 °C every step (`:78-84`). It never cools back down unless state is set externally.
- **A burning object is itself a 1000 °C source** with a 0.2 m sphere around its root-link AABB centre (`:51-59`, `:67-70`). It ignites neighbours whose collision shapes intersect that sphere.
- **Estimated timings** from the §2 model (derived, not measured):
  - A lighter (on, T_ss ≈ 837) held at an object: 23 → 250 °C in ~2.7 s.
  - A burning newspaper igniting firewood within 0.2 m: ~7 s.
- **What the robot does:** grasp the `cigar_lighter`, toggle it on (§11), hold its heat point within 0.2 m of the newspaper for a few seconds, then toggle it off.
  - setting_the_fire also needs firewood `ontop` the newspaper and `inside` the fireplace, which requires a grasp.
  - Arrange the wood on the paper first, so that the burning paper (0.2 m radius from its AABB centre) reaches every log.
- **Failures:**
  - Firewood beyond 0.2 m of the paper's centre never ignites.
  - The lighter is left on, which fails the `not toggled_on` literal.

## 15. `cooked` (23)

- **Class:** `Cooked` at `object_states/cooked.py:13`. Test at `:35-36`.
- **Test:** `MaxTemperature ≥ cook_temperature`. MaxTemperature is the **highest temperature ever reached** (`object_states/max_temperature.py:68-70`).
- **It latches:** once cooked, it stays cooked even after cooling. Halves inherit it (§7).
- **Cook temperatures** (runtime KB):

| synset | cook_temperature (°C) |
|---|---|
| hotdog | 60 |
| bacon | 63 |
| brisket | 63 |
| apple_pie | 80 |
| half__brussels_sprouts | 58 |
| broccolini | 58 |
| clove.n.03 | 58 |
| hard-boiled_egg | 74 |

  The default is 70 (`cooked.py:10`).
- **Estimated times** from reset temperature 23 °C, using §2 (derived; the object must stay in range the whole time):
  - **Microwave** (closed + on + food Inside): hotdog 60 °C in ~7 s; pie 80 °C in ~18 s.
  - **Oven** (closed + on + Inside): pie 80 °C in ~3 s from 23 °C, or ~5 s from −30 °C (frozen).
  - **Stove burner:** 60 °C in ~0.2 s once the food is within 0.2 m of the burner's heat-source point.
- **What the robot does:**
  - **Microwave or oven:** open the door, place the food inside (its AABB centre in the fillable volume; a plate or pan is fine), close the door fully (§6), toggle it on, and wait.
  - **Stove:** put the food in or on a pan on the active burner, and turn the burner on.
  - A grasp is needed to move the food, and possibly the handles, subject to the 44 mm limit.
- **Failures:**
  - The door is not fully closed (5 % rule), so there is no heating. For the microwave, being open also turns it off.
  - The food is placed on the oven door or rack edge with its centre outside the fillable volume.
  - The food is beyond 0.2 m of the burner point.
  - It is removed before reaching the threshold. Progress is not lost, because MaxTemperature is kept, but temperature decays while out of range.

## 16. `frozen` (2) and `not frozen` (2)

- **Class:** `Frozen` at `object_states/frozen.py:18`. Test at `:42-43`.
- **Test:** **current** `Temperature ≤ freeze_temperature`. The default is 0 °C (`:10`); no freezable parameters are set in the KB. Unlike Cooked, this is **not latched**.
- **Freezing** (freeze_pies): `electric_refrigerator` is the only relevant cold source (−18 °C, needs closed + Inside, T_ss ≈ −11.2 °C). 23 → 0 °C takes ~9 s with the door fully closed (derived).
- **Flip-back (derived):** once the object leaves the fridge, or the door opens, it warms toward 23 °C at 0.02/s. From −11 °C it reaches 0 °C again in ~20 s. **The object must still be in the closed fridge at episode end.** Goals usually also require `inside` the fridge and `not open` on it.
- **Thawing** (`not frozen`, thawing_frozen_food):
  - `set_value(True)` samples the initial temperature between −50 and −10 °C (`:14-15`, `:31-36`).
  - Room-temperature decay alone thaws the object in ~18–58 s (derived) once it is out of the fridge.
  - A running microwave (closed, food Inside) thaws it in ~4 s.
  - It scores only if the object was frozen at reset.
- **Grasp:** needed to move the object, and possibly for the fridge handle.
- **Failures:**
  - A fridge door left ajar (> 5 %), so there is no cooling.
  - An object whose AABB centre is outside the fridge's fillable volume, for example in a door bin. Door bins are not verified to have volume.

---

## 17. Grasp summary

| predicate | robot action | grasp needed? |
|---|---|---|
| inside / ontop / nextto / under / touching | move object | yes (or push); object/handle ≤ ~44 mm across for assisted grasp |
| not inside / not touching | move object away | yes (or push) |
| not open | push door/drawer shut | no |
| toggled_on / not toggled_on | fingertip press ≥ 5 steps, single contact episode | no |
| attached | align child's mount to parent's within 5 cm / 15° while touching | yes |
| real (sliced/diced) | touch sliceable with knife/axe | yes (tool) |
| not covered | sweep remover AABB+2 cm over every particle, or washer | yes (tool) or none (washer) |
| covered (spray) | toggle atomizer on, aim | yes (tool) + toggle |
| contains / filled | pour/scrape or create particles in container | yes |
| cooked / frozen / on_fire | place in/near source, close + toggle, wait | yes (object/tool) |

## 18. Not verified here

- Whether knife and axe assets expose the blade as a separate rigid link, and whether handle contact also slices.
- Diced-particle counts and radii, which determine whether `filled` can reach 20 %.
- Whether drawers or fridge door bins carry their own fillable volumes.
- Spray-cone dimensions of the atomizers.
- The exact number of visual dirt particles in each task instance.
- Whether the 200-particle removal limit ever resets.
- Canopy density of Christmas-tree and fruit-tree meshes, which matters for `under` and for spraying.
