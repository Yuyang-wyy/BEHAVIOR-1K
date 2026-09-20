# Visual radio adaptation

This is a local ASPIRE-style adaptation, not a reproduction of the published
evaluation protocol. The legacy `policy.py` / `replay_policy.py` path is a
demonstration-replay diagnostic and must not be counted as code-policy success.

`visual_policy.py` starts from the sequence in the local ASPIRE
`aspire/sim/cap/envs/tasks/r1pro/r1pro_pickup_radio.py:ORACLE_CODE`. That example
targets pickup, not turning on the radio. The local button-grounding extension
has one historical successful rollout, but is not yet reliably reproduced.

## Inputs and limits

The visual adapter exposes RGB-D, robot geometry, SAM3 segmentation, observed
geometry, robot-only IK, and motor commands. Historical versions used exact
simulator camera, base, EEF, and finger world poses; those results used oracle
localization. The current adapter instead consumes the official observation's
`cam_rel_poses` (xyzw quaternion order), relative EEF proprioception, and physical joint encoders. It
integrates body-frame base velocity in an episode-local odometry frame and uses
the static robot URDF for finger geometry. Virtual base coordinates are zeroed
before local-frame IK. The legacy key `world_from_camera` now denotes this
odometry frame, not simulator world coordinates. This removes the known global
pose input; it does not establish a successful reproduction or official approval.
The adapter
does not load demonstrations, inspect scene/object assets, resolve simulator
objects, read contacts/attachments, or locate simulator toggle markers.
Robot kinematics/configuration are used for IK. CuRobo world-obstacle updates
and ground-truth world collision checks are disabled; short straight-line
navigation and interpolated IK are not obstacle-aware motion planning.

The default `eval/r1pro.yaml` uses `grasping_mode: assisted`. Results obtained
with this configuration must not be described as pure physical-grasp results.
Grasp mode and observation provenance must accompany any reported score.

The existing local ASPIRE Contact-GraspNet code/checkpoint is reused via its
loopback service. `sample_contact_grasp_pose(mask)` plans learned grasps from
current camera depth; `sample_grasp_pose(query)` obtains the mask from SAM3.
The point-cloud-only helper remains geometric, not a learned grasp network.

The task evaluator alone reads task success after execution; that value is
not a policy input. Visual grasp checks are heuristics and can be wrong.
`press_at_pixel` returning true means motion completed, not that the task passed.

## Current turning-on-radio policy, 2026-09-20

`press_marker_policy.py` supersedes `learned_press_policy.py`. Measured over
the full public set (instances 301-320, one seed each,
`seed = 2026092500 + instance - 300`, assisted grasping, `codex-pixels`,
6000 steps): **7/20**, against **0/20** for `learned_press_policy.py` on the
same 20 instances with pristine sources. Full table, caveats and rendered
rollouts in `/home/ywang/Behavior/radio_generalization_20260920/`.

Two harness defects were behind most of the old failures:

1. `VisualRadioHarness._finger_positions` indexed URDF-keyed finger offsets
   with scene-prefixed link names, so it raised `KeyError` on every call.
   `get_current_finger_center` propagated it; `press_at_pixel` *swallowed* it
   and then aimed as if the fingertip were on the EEF +Z axis. The real
   finger-1 origin is `(0.0001, 0.0135, -0.0231)` m in the EEF frame, so every
   press was systematically 13.5 mm off to the side.
2. `navigate_to_pose` had no stalled-approach guard and burned its entire
   800-step allowance against obstacles it cannot plan around.

The 13.5 mm matters because `radio/wxnicr` carries one `togglebutton` meta
link with sphere `size = 0.011179`, and `ToggledOn` requires a finger link to
be in contact with the radio **and** to overlap that sphere for
`CAN_TOGGLE_STEPS = 5` consecutive steps. The aiming error was wider than the
target.

The BDDL goal is only `toggled_on`, so the new policy never grasps: it scans
for the red body, docks by repeated visual re-grounding, grounds the raised red
control cap in RGB-D by metric size, roundness and dark surround, and pushes one
closed fingertip along the face normal, orbiting when the cap faces away.

```bash
PYTHONPATH=$PWD/OmniGibson \
OMNIGIBSON_HEADLESS=1 OMNI_KIT_ACCEPT_EULA=YES OMNIGIBSON_GPU_ID=0 \
/home/ywang/miniconda3/envs/behavior/bin/python \
scripts/aspire_radio/run_visual_policy.py \
  --policy scripts/aspire_radio/press_marker_policy.py \
  --instance 301 --seed 2026092501 --mode public_test \
  --grasping-mode assisted --grounding codex-pixels --max-steps 6000 \
  --output-dir outputs/behavior/aspire-campaigns/radio/press-marker-301
```

Known and unfixed, both documented with evidence in that directory: the press
can topple the radio instead of toggling it, and the pure-Python connected
component pass over the red mask is unbounded and once hung a rollout for
90 minutes. `press_marker_policy_v10.py` is a variant with a tighter detector
(image-border rejection, cap-height gate, search anchored to the tracked
radio); it scored 5/20, so its filters are worth merging into the simpler
search but the merge has not been validated.

The detector keys on the same rendered red blob that
`learned_press_policy.find_button` already used, which is the `ToggledOn`
visual marker mesh. Its *position* is read as a shape in the camera image; its
colour state is the goal predicate itself and is deliberately never tested.
Three constants (marker span range, the 0.18 m long-axis threshold, pressing
horizontally) come from offline inspection of this asset, which every public
instance shares; they are search-ordering priors, not runtime asset access.

## Historical turning-on-radio policy

`learned_press_policy.py` was the ASPIRE-style visual code policy for
`turning_on_radio` until 2026-09-20; it scores 0/20 on the public set and is
kept for reference. Its online sequence is:

1. Navigate from current RGB-D to the table using visual red-radio geometry.
2. Try a visible button directly on the table. The BDDL goal requires only
   `toggled_on`, so grasping is a fallback, not a scoring prerequisite.
3. Otherwise ground the radio from current RGB-D, sample Contact-GraspNet
   candidates, and execute a right-arm grasp. Verify that the radio follows
   a separate 8 cm closed-gripper lift; proximity and apparent height alone
   produced false positives in earlier runs.
4. Preserve the right-arm holder while moving the free left arm to the
   observed radio control. The press adapter tracks the holder, restores its
   saved trunk/holder joint posture after torso-enabled approach, and relies on
   normal physical finger overlap for the task toggle.
5. Reacquire the visible red control before press attempts. The policy never
   reads `ToggledOn`, contacts, object registry, simulator markers, or
   demonstration action arrays online. Its hardcoded staging posture includes
   an offline demonstration-derived prior; it is not a replayed action sequence.

The policy samples Contact-GraspNet twice from the same current RGB-D frame to
reduce candidate variance. This is a robustness measure, not a success oracle.
Success is reported only from the evaluator's final `task_success` and
`q_score`, not from a motor return value.

### Verified evidence

The historical evaluator-confirmed success is instance `302`, seed `2026091609`:

```text
task_success=true
status=success
q_score.final=1.0
demonstration_actions=false
ground_truth_object_state=false
```

Evidence is in
`outputs/behavior/aspire-campaigns/radio/public-test-20260919-final7/`:
`result.json`, `trace.jsonl`, and `rollout.mp4`. The run contains rendered
evidence of the right-hand hold and left-hand control approach.
The two false flags describe specific excluded inputs, not the absence of all
privileged inputs. The simulator-derived robot/camera transforms above remain
a limitation of this result.

Grasp and presentation remain stochastic across repeated rollouts; failed
attempts must remain in the report. A single successful rollout is not evidence
of a stable success rate.

### Reproduction command

```bash
PYTHONPATH=$PWD/OmniGibson \
OMNIGIBSON_HEADLESS=1 OMNI_KIT_ACCEPT_EULA=YES OMNIGIBSON_GPU_ID=0 \
/home/ywang/miniconda3/envs/behavior/bin/python \
scripts/aspire_radio/run_visual_policy.py \
  --policy scripts/aspire_radio/learned_press_policy.py \
  --instance 302 --seed 2026091609 \
  --output-dir outputs/behavior/aspire-campaigns/radio/public-test-new-302 \
  --mode public_test --grounding codex-pixels --max-steps 6000 --record-video
```

### Public-instance results

| Instance | Seed | Task success | Q | Output |
| --- | ---: | ---: | ---: | --- |
| 302 | 2026091609 | 1 | 1.0 | `public-test-20260919-final7` |
| 301 | 2026091608 | 0 | 0.0 | `public-test-20260920-301` |
| 303 | 2026091610 | 0 | 0.0 | `public-test-20260920-303` |
| 304 | 2026091611 | 0 | 0.0 | `public-test-20260920-304` |
| 303 (rerun) | 2026091610 | 0 | 0.0 | `public-test-20260920-303-roll2` |

These are debugging runs across policy revisions, not a fixed-version batch.
The selected `302` success must not be combined with three later failures to
claim a `25%` success rate. Later `302` attempts (`final8` and `final9`) also
failed. In the `301`, `303`, and `304` failures,
the visual grasp heuristic returned true but the press block ended with
`press_motor_completed=false`; their traces repeatedly show partial holder
restoration followed by `fixed_trunk_precontact` IK failure. The `303-roll2`
rerun failed earlier during grasp verification. These results are retained as
historical diagnostics rather than being hidden by retry selection.

The current press harness additionally tries multiple wrist rolls during the
fixed-torso contact solve. Unit coverage remains `19 passed` in
`visual_policy_test.py`; this change still needs another successful public
rollout before it should be described as improving the matrix above.

### Fixed-version baseline, 2026-09-20

Revision `746176312`, seed `2026092000`, max 6000 steps, default assisted grasp,
with the oracle robot/camera transforms described above: **0/3 successes**.

| Instance | Steps | Task success | Q | Failure |
| --- | ---: | ---: | ---: | --- |
| 305 | 2942 | 0 | 0.0 | Button not visible after presentation |
| 306 | 3386 | 0 | 0.0 | Press did not complete the task |
| 307 | 1125 | 0 | 0.0 | No visually verified grasp |

Artifacts are under `/home/ywang/Behavior/artifacts/public-test-20260920-baseline-{305,306,307}`.
The `public-test-20260920-baseline-repro` sibling directory retains source hashes,
commands, logs, and exit codes. These are all attempts in this three-instance
batch; none succeeded. The remaining public instances have not been evaluated
with this fixed version.

The next posture experiment uses the medoid of all 200 training pre-toggle
postures (raw episode 600, action frame 1280). For each training episode, take
the action 16 frames before its first positive sampled `toggled` label, then
minimize summed Euclidean distance over trunk and both arm joint targets.
This preserves an actual demonstrated joint configuration, unlike independently
taking each joint's median. It is an offline prior and still requires fresh
visual grounding and evaluator-confirmed validation after grasping.

Training references also show a first-grasp base-to-radio distance median of
0.794 m and 90th percentile of 0.929 m. The current docking radius is 0.80 m;
the old 1.194 m radius unnecessarily moved reachable approaches farther away.
Table clearance is preserved when selecting a reachable edge.

Onboard-input diagnostic `public-test-20260920-probe-302` visually verified a
held radio: the probe moved the hand 0.07938 m up and the observed radio
0.07935 m up. It still ended with Q=0 because subsequent holder staging did
not settle. This is a grasp diagnostic, not a task success. The preceding
`public-test-20260920-onboard-302` exposed the old false-positive grasp check:
its saved images showed the radio remaining on the table.

The AST/import guard prevents common accidental privileged calls. It is NOT
a hardened Python security sandbox. Workers run without provider credentials
in their environment; stronger protection requires host/container isolation.

Both arm IK adapters lock the other arm's joints and preserve independent
gripper commands. The offline RGB reference shows right-hand holding and
left-hand pressing. The starting SAM3 policy follows that sequence; successful
grasp has development visual evidence, and button operation has one historical success.
Optional torso-locked IK prevents hand setup from changing the head-camera pitch;
contact attempts lock the torso, while some approach and correction paths allow
torso movement. Motor holds retain command targets, not measured drift.

## Run

From the BEHAVIOR-1K root, use the existing `behavior` Python environment:

```bash
export PYTHONPATH="$PWD/OmniGibson"
export OMNIGIBSON_HEADLESS=1 OMNI_KIT_ACCEPT_EULA=YES OMNIGIBSON_GPU_ID=0
PYTHON=/home/ywang/miniconda3/envs/behavior/bin/python
```

SAM3 is installed in the existing ASPIRE reference venv, not the simulator
conda env. Start its server using an authorized local weight file:

```bash
../references/ASPIRE/aspire/sim/cap/third_party/b1k/.venv/bin/python \
  scripts/aspire_radio/start_sam3.py --checkpoint /path/to/sam3.pt
```

Start the already installed Contact-GraspNet service in the same reference venv:

```bash
PYTHONPATH=../references/ASPIRE \
  ../references/ASPIRE/aspire/sim/cap/third_party/b1k/.venv/bin/python \
  -m aspire.sim.cap.serving.launch_contact_graspnet_server --host 127.0.0.1 --port 8115
```

Its checkpoint is already local; no download is needed. Learned inference has
been tested on saved current RGB-D; reliable task success is not yet established.

Run the bounded external Codex loop on one development instance:

```bash
$PYTHON scripts/aspire_radio/refine_visual_policy.py \
  --instance 26 --max-attempts 3 --output-dir outputs/radio-visual-new-run
```

Each failure produces RGB-D/calibration snapshots, masks, trace, video, and a
terminal result. The external Codex CLI receives allowed evidence and sampled
video frames, emits a revised policy, and accumulates evidence-labelled notes.
Each trial resets the same instance and executes code, NOT recorded actions.
The runner stops on success, infrastructure failure, or its attempt/time budget.
Directories cannot be reused. A node lock prevents two visual workers overlapping.
The runner currently permits only development instance IDs 26-35; these are
not asserted to be equivalent to ASPIRE's published simulator seed partition.

If SAM3 weights are unavailable, an explicit Codex-pixel development experiment
can still test the manipulation loop:

```bash
$PYTHON scripts/aspire_radio/refine_visual_policy.py --grounding codex-pixels \
  --instance 26 --max-attempts 3 --output-dir outputs/radio-codex-pixels-new-run
```

This mode captures the fresh initial camera view before asking Codex to build
each instance's policy. Codex grounds pixels in RGB, and executable code
backprojects current depth/calibration. It is NOT SAM3 segmentation, never
silently replaces the default SAM3 path, and cannot establish SAM3 replication.
The point-cloud grasp helper and motor-only `execute_grasp` API do not claim a
successful grasp. Verification must come from subsequent allowed observations.

Offline training reference extraction reads only episode/video metadata, skill
timing for keyframe selection, and RGB video, not action data:

```bash
$PYTHON scripts/aspire_radio/reference_keyframes.py --episode 31 \
  --output-dir outputs/radio-reference-ep31-new
```

Pass that directory with `--reference-dir` to attach action-free grasp/press RGB
keyframes to each Codex proposal. They are labelled as training references, never
as current localization images. To continue a complete revision/rollout loop from
an existing visual attempt, use `--from-evidence /path/to/attempt` with the matching
`--policy`. Replay-baseline evidence and a mismatched instance are rejected.

For a camera-only smoke test (no SAM3 or manipulation):

```bash
$PYTHON scripts/aspire_radio/run_visual_policy.py --capture-only \
  --instance 26 --output-dir outputs/radio-visual-capture-new
```

For one actual Codex revision from that allowed evidence, without evaluation:

```bash
$PYTHON scripts/aspire_radio/refine_visual_policy.py \
  --refine-only outputs/radio-visual-capture-new --output-dir outputs/radio-visual-revision-new
```

CPU checks (the SAM3 wire test uses a mock server, not model inference):

```bash
$PYTHON -m pytest OmniGibson/omnigibson/eval/aspire/code_policy_executor_test.py \
  OmniGibson/omnigibson/eval/aspire/visual_policy_test.py -q
```
