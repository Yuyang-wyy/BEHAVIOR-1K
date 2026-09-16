# Visual radio adaptation

This is a local ASPIRE-style adaptation, not a reproduction of the published
evaluation protocol. The legacy `policy.py` / `replay_policy.py` path is a
demonstration-replay diagnostic and must not be counted as code-policy success.

`visual_policy.py` starts from the sequence in the local ASPIRE
`aspire/sim/cap/envs/tasks/r1pro/r1pro_pickup_radio.py:ORACLE_CODE`. That example
targets pickup, not turning on the radio. The final button-grounding block is
an unvalidated extension for the current `turning_on_radio` benchmark.

## Inputs and limits

The visual adapter exposes RGB-D, camera calibration, robot proprioception,
SAM3 segmentation, observed geometry, robot-only IK, and motor commands. It
does not load demonstrations, inspect scene/object assets, resolve simulator
objects, read contacts/attachments, or locate simulator toggle markers.
Robot kinematics/configuration are used for IK. CuRobo world-obstacle updates
and ground-truth world collision checks are disabled; short straight-line
navigation and interpolated IK are not obstacle-aware motion planning.

The existing local ASPIRE Contact-GraspNet code/checkpoint is reused via its
loopback service. `sample_contact_grasp_pose(mask)` plans learned grasps from
current camera depth; `sample_grasp_pose(query)` obtains the mask from SAM3.
The point-cloud-only helper remains geometric, not a learned grasp network.

The task evaluator alone reads task success after execution; that value is
not a policy input. Visual grasp checks are heuristics and can be wrong.
`press_at_pixel` returning true means motion completed, not that the task passed.

The AST/import guard prevents common accidental privileged calls. It is NOT
a hardened Python security sandbox. Workers run without provider credentials
in their environment; stronger protection requires host/container isolation.

Both arm IK adapters lock the other arm's joints and preserve independent
gripper commands. The offline RGB reference shows right-hand holding and
left-hand pressing. The starting SAM3 policy follows that sequence; successful
grasp has development visual evidence, but button operation is not yet established.
Optional torso-locked IK prevents hand setup from changing the head-camera pitch;
pressing always locks the torso. Motor holds retain command targets, not measured drift.

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
been tested on saved current RGB-D, but task success is not yet established.

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
