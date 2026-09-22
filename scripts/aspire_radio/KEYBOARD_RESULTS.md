# clean_a_keyboard: raising the success rate

All numbers are `task_success` from the evaluator on the 20 public test instances
301-320 (`--mode public_test`), one seed per instance (`2026092200 + inst - 300`),
assisted grasping, and — from v15 on — the **official step limit of 5814**
(`1.5 x` the human demo length, from `load_human_stats`). Earlier batches used 6000;
no success in them came after step 5814. A trial that hangs (see below) is killed
after 1500 s and counts as a failure.

Runs are **not deterministic** for the same instance and seed, so one sweep of 20
is a rough estimate: the same instance flips between versions that barely differ.

## Results (full 20-instance batches)

| policy | successes / 20 | tool held | solved instances |
|---|---|---|---|
| v1 `wipe_keyboard_policy.py` | **1/20** | 1 | 320 |
| v15 | **2/20** | 3 | 301, 315 |
| v20 | **3/20** | 11 | 309, 311, 313 |
| v22 | 1/20 | 14 | 301 |
| v28 | **3/20** | 14 | 305, 311, 318 |
| v31 | **3/20** | 14 | 309, 311, 313 |
| v34 | 1/20 | 12 | 313 |
| v35 | **3/20** | 12 | 301, 313, 315 |
| v38 | **4/20** | 11 | 305, 310, 311, 315 |
| v39 | 2/20 | 12 | 309, 311 |

**Fresh seeds.** v35 re-run on seeds never used for tuning (`2026093100 + inst - 300`)
scored **1/20** (instance 313; two trials hung in PhysX and count as failures),
against 3/20 on the tuning seeds. The honest estimate for v35 is ~5-10%, not 15%.

v40 on the same fresh seeds also scored **1/20** (instance 315); four local
trials hung in PhysX and were killed by the timeout. Fresh-seed v35 and v40 are
indistinguishable.

v31 is the first batch in which the path planner never reported "no path" (0/20;
earlier batches had several per run). The local half of the split
(302-314 even, 315, 317) is consistently harder: 0/10 in both v28 and v31.

Partial batches (v17-v19, v21, v23-v27, v29, v32, v33) were stopped once a flaw
was found; they are not counted. Four different versions reach 3/20 on different
instance sets, which says the true rate of the better versions is around 15% and
that one seed per instance cannot rank them. Instances solved by at least one version: 301, 305, 309, 311,
313, 315, 318, 320 (8 of 20).

## What was wrong, in order of discovery

1. **Hand-rolled RGB-D backprojection was mirrored.** Camera poses are OpenGL
   (+Y up, -Z forward); without the `[1, -1, -1]` flip every point cloud was
   reflected through the camera. `mask_to_world_points` is the reference.
2. **The task is not what the repo BDDL says.** The public instances hold only a
   keyboard, a pipe cleaner, a desk and dust. Dust removal by the pipe cleaner is
   ADJACENCY with condition `[]` (always): touching is enough, all 20 particles
   must go, and every particle inside the tool's root-link visual AABB grown by
   0.02 m is removed each step.
3. **The tool is rescaled.** `task_custom_lists.json` sets the pipe cleaner (model
   yccyjo) to **0.40 x 0.10 x 0.10 m**: a thin cyan handle that fits the 0.044 m
   jaws, and bristles 0.10 m across. Using the library's unscaled size (0.037 m)
   put the bristles 2 cm into the keys, which shoved or flung the keyboard.
4. **Grasping.** Grasps work with the tool 0.69-0.94 m from the base. The grasp
   helper's second candidate closes along the rod and can never fit; the wrist
   camera, not the head, sees the handle at the pre-grasp pose. When the base
   stalls too far away, tilting the grasp about the rod's own axis reaches ~0.1 m
   further (v28 first solved instance 305 this way).
5. **Carrying.** Restoring the trunk swings the held tool under the desk; any large
   motion of the loaded arm tipped the robot. Drive with the hand where the
   grasp's lift left it.
6. **Sweeping.** Rod laid along the keyboard, swept across it from one stance at
   0.68 m; the hand pitches about the rod's axis for reach. Height by touch: step
   down over the keyboard until the hand stops following, then lift. A rod driven
   into the keys leaves the arm in a state from which every IK plan fails;
   `move_to_joints` to the last good configuration escapes.
7. **Navigation.** A grid planner on the single current view (older views are
   smeared by ~15% rotation-odometry drift) with relaxing fallbacks; never the
   desk-edge docker, which drove into desks.
8. **Hangs are inside PhysX.** A faulthandler dump showed a trial blocked in
   `simulation_context.step` during `navigate_to_pose`. Trials run under `timeout`.

9. **The keyboard fix goes stale on the way.** Across 19 held v35 trials, the
   keyboard was re-seen from the sweeping stance in 4 (3 successes); in the 15
   others every stroke went to the drifted scan fix and removed nothing but once.
   v36/v37 re-find it right after the grasp on a ring of the scan's tool-keyboard
   distance around the grasp spot, and search all round at the stance.
10. **Every held move costs ~150 steps.** The harness ends each move with up to
    120 settle steps that stop only when every joint is within 0.01 rad; with
    the tool's weight the wrist sags 0.01-0.015 rad, so no held move ever
    settles. The 1 cm touch probe from 12 cm up cost ~1400 steps on its own.
11. **The grip is off-centre.** The detector sees only the cyan grip; the
    evaluator log shows the tool's box centre 0.12 m from the hand along the rod,
    toward the grey brush.
12. **Reach.** Where the desk edge stops the base, the lengthwise rod's far
    strokes are out of reach (5 of 18 fresh-seed v35 trials skipped every
    stroke). v38 turns the rod to point away from the robot and sweeps along the
    keyboard: the box spans the keyboard's width from a hand 0-0.14 m short of
    its centre line.

13. **The robot tips or climbs while carrying the tool.** The evaluator log
    (base link height, logged since v37) shows the base rising 8-59 cm and
    staying up for hundreds of steps in 9 of 15 v39/v40 local trials, mostly
    during the carry after the grasp. The camera pose assumes a level base, so
    every point cloud from then on is tilted (one stance view: 19 degrees; after
    levelling it by the fitted floor plane the keyboard was found at once). The
    stance views of 6 of 7 remote v40 trials look at walls or the floor, rolled
    30-45 degrees. This, not detection, is now the main failure: v40 scored 0/10
    on the fresh-seed remote half.

## Remaining failure classes (v28)

* **Never reaching the tool** (6/20): the planner finds no path from the start view
  and the straight approach stalls >1 m away.
* **Keyboard pushed or not re-found** during the sweep: the usable height window
  is ~1.6 cm while the rod's height varies ~1.5 cm through a stroke.
* **Out of steps** with 1-4 particles left (instances 301, 302, 313, 315).

## Honesty notes

* The policy uses RGB-D, proprioception, the official relative camera calibration,
  static finger geometry and body-velocity odometry only. Instance files,
  `task_custom_lists.json` and simulator state were read **only** while
  debugging; the evaluator-side diagnostics (`debug_remaining_particles`,
  `ASPIRE_DEBUG_AABB`) are written by the runner and never passed to the policy.
* Shape gates, the tool's size and the cyan colour of the tool are
  asset/task-derived constants, the same caveat as the radio work.
