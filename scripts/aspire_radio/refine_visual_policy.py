"""Bounded external-Codex observation -> code -> rollout -> revision loop."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import av
import requests

from omnigibson.eval.aspire.public_policy import validate_policy


API_REFERENCE = """
Only these functions are injected into each policy (numpy/math/scipy.spatial.transform imports allowed):
get_observation(camera='head') -> dict rgb(uint8), depth(image-plane metres), intrinsics(3x3),
    world_from_camera(4x4 OpenGL camera frame), joints(full robot encoder vector).
get_env_observation(camera='head') -> rgb,depth.
save_current_observation(name,camera='head') -> save RGB-D/calibration and PNG as evidence.
segment_sam3_text_prompt(rgb,text_prompt) -> list of dict(mask HxW bool,box xyxy,score,label).
mask_to_world_points(mask,depth,intrinsics,world_from_camera) -> Nx3 world points.
get_object_pose(query,return_bbox_extent=False,camera='head') -> position,quaternion WXYZ,
    extent or None,visible points,box dict(center,rotation,extent). Estimated from SAM3+depth.
find_object_base_rotate(query),find_object_torso_rotate(query) -> visual search bool.
get_robot_position() -> position,WXYZ,yaw. rotate_base(radians) -> bool.
get_navigation_pose(table_points,object_points) -> x,y,yaw. navigate_to_pose(pose) -> bool.
sample_grasp_pose(query) -> SAM3 mask + Contact-GraspNet candidates (geometric fallback only if
    the network returns zero grasps, not if its service is unavailable). Poses are world XYZ,WXYZ.
sample_contact_grasp_pose(mask,camera='head',arm=1,max_candidates=8) -> pregrasp list,grasp list
    from the CURRENT RGB-D using the existing ASPIRE Contact-GraspNet model/service. The adapter
    converts model CV/panda frame to own EEF, including robot fingertip offset and jaw-axis alignment.
sample_grasp_pose_from_points(points,arm=1) -> candidates from a CURRENT observed target cloud.
    Current minimal sampler returns TWO TOP-DOWN candidates: EEF local Z points world-down,
    pregrasp is grasp + [0,0,.15], candidate yaw follows upright XY PCA, then yaw+pi/2.
    Rejecting every vertical approach cannot select a different candidate. For a side approach,
    construct world position and WXYZ orientation yourself using the observed cloud and numpy/Rotation.
execute_grasp(pregrasp,grasp,arm=1,lift=.08) -> motor completion only; verify from fresh images.
grasp_object(pregrasp,grasp,query,arm=1) -> approach,close,lift; bool motion completion.
check_object_in_hand(arm=1) -> visual lift/hand-distance check, not simulator contact or attachment.
open_gripper(arm=1),close_gripper(arm=1),lift_arm(arm=1,distance=.08,lock_trunk=False).
get_current_eef_pose(arm=1) -> world XYZ,WXYZ. get_current_joint_positions() -> encoder vector.
solve_ik(position,quaternion_wxyz,arm=1,lock_trunk=False,lock_last_trunk=False,self_collision_check=False)
    -> full robot joint target or None.
move_to_joints(target,max_joint_step=.015),
move_hand((position,WXYZ),arm=1,max_joint_step=.015,lock_trunk=False,lock_last_trunk=False,
    self_collision_check=False) -> bool.
    lock_trunk=True prevents torso motion/head-camera reorientation, useful for raising hands before
    navigation and pressing with the free arm. Motor holds preserve COMMAND targets, not encoder drift.
press_at_pixel(x,y,camera='head',travel=.015,arm=1) -> bool motion completion, NOT task success.
    Keeps torso fixed so a held radio is not moved by free-arm IK. Supply a freshly observed pixel.
No object registry, ground-truth geometry, simulator marker/contact, demonstration action arrays,
asset inspection, task-instance-specific lookup, filesystem access, or reward query is allowed.
Use # Code block N sections. RESULT must contain observed evidence, not an invented success claim.
"""

RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"policy": {"type": "string"}, "diagnosis": {"type": "string"}, "lesson": {"type": "string"}},
    "required": ["policy", "diagnosis", "lesson"],
}


def run_process(command, *, cwd, timeout, log_path, env=None, stdin=None):
    with log_path.open("w") as log:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True, text=True)
        try:
            process.communicate(input=stdin, timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    return process.returncode


def worker_environment(root):
    # Provider credentials stay in the coordinator/Codex process, not the policy worker.
    env = {key: value for key, value in os.environ.items()
           if not any(word in key.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "ACCESS_KEY", "CREDENTIAL"))
           and not key.upper().startswith(("OPENAI_", "CODEX_", "HF_", "AZURE_", "ANTHROPIC_"))}
    env.update({"OMNIGIBSON_HEADLESS": "1", "OMNI_KIT_ACCEPT_EULA": "YES", "OMNIGIBSON_GPU_ID": "0",
                "PYTHONPATH": str(root / "OmniGibson")})
    return env


def evidence_for_codex(directory, output_dir):
    evidence = {}
    if (directory / "result.json").exists():
        evidence["result"] = json.loads((directory / "result.json").read_text())
    if (directory / "trace.jsonl").exists():
        evidence["trace"] = (directory / "trace.jsonl").read_text()[-24000:]
    images = sorted(directory.glob("*.png"), key=lambda path: (path.stat().st_mtime_ns, path.name))
    initial = [path for path in images if path.name in {"initial_head.png", "initial.png"}][:1]
    before = [path for path in images if path.name.startswith(("before_", "pregrasp", "after_approach"))][-1:]
    after = [path for path in images if path.name.startswith("after_") and not path.name.startswith("after_approach")][-3:]
    masks = [path for path in images if path.name.endswith("_mask.png")][-1:]
    selected = initial + before + after + masks
    video = directory / "rollout.mp4"
    if video.exists():
        with av.open(str(video)) as container:
            count = sum(1 for _ in container.decode(video=0))
        indices = {int((count - 1) * fraction) for fraction in (.5, 1)} if count else set()
        with av.open(str(video)) as container:
            for index, frame in enumerate(container.decode(video=0)):
                if index in indices:
                    path = output_dir / f"video_frame_{index:05d}.png"
                    frame.to_image().save(path)
                    selected.append(path)
    return evidence, list(dict.fromkeys(selected))


def propose_policy(previous_policy, evidence_dir, output_dir, skills, timeout, *, grounding="sam3", reference_images=()):
    output_dir.mkdir(parents=True, exist_ok=False)
    schema_path = output_dir / "response-schema.json"
    schema_path.write_text(json.dumps(RESPONSE_SCHEMA))
    evidence, images = evidence_for_codex(evidence_dir, output_dir)
    current_image_count = len(images)
    images += list(reference_images)
    perception_instruction = (
        "Prefer fresh SAM3 localization. If SAM3 is unavailable, diagnose infrastructure; do not invent detections. "
        if grounding == "sam3" else
        "Explicit Codex-pixel experiment: SAM3 is unavailable. Ground the radio, handle and control in attached RGB "
        "images yourself; encode those observed pixel regions in code and backproject CURRENT depth/calibration. "
        "Do not call segment_sam3_text_prompt, get_object_pose, find_object_base_rotate, "
        "find_object_torso_rotate, sample_grasp_pose or check_object_in_hand: they require SAM3. "
        "Use mask_to_world_points, sample_contact_grasp_pose (existing learned grasp model), "
        "sample_grasp_pose_from_points (geometric only) and execute_grasp instead. "
        "No image observation proves a grasp in a future reset episode; do not invent verified booleans. "
    )
    prompt = (
        "You are the external reasoning/code-refinement model for an ASPIRE-style R1Pro simulation. "
        "Goal: turn on the red radio. The public task goal is toggled_on only; pickup is an optional "
        "means, not a requirement. Reply only using the requested JSON schema. "
        "Do not use shell, tools, inspect files, invoke agents, or change the harness. All allowed evidence "
        "is embedded below or attached as images. Revise executable Python policy, not action replay. "
        "Do not introduce constants derived from simulator assets or instance IDs. Pixel coordinates may "
        "be grounded in the attached CURRENT images. " + perception_instruction +
        "Never use ground truth. "
        "Images labelled TRAINING REFERENCE show appearance and behavior only. Never transfer their "
        "pixel coordinates, poses or actions to the current trial; ground executable coordinates in CURRENT images. "
        "Write a reusable lesson only if supported by evidence, and label untested proposals as untested.\n"
        + API_REFERENCE + "\nWorking skills:\n" + skills + "\nPrevious policy:\n" + previous_policy
        + "\nObserved rollout evidence:\n" + json.dumps(evidence, default=str)
        + "\nAttached image order:\n" + "\n".join(
            ("CURRENT: " if index < current_image_count else "TRAINING REFERENCE: ") + path.name
            for index, path in enumerate(images))
    )
    (output_dir / "prompt.txt").write_text(prompt)
    response_path = output_dir / "response.json"
    command = ["codex", "exec", "--sandbox", "read-only", "--skip-git-repo-check", "--ephemeral", "--json",
               "--output-schema", str(schema_path.resolve()), "--output-last-message", str(response_path.resolve())]
    if images:
        command += ["--image", ",".join(str(path.resolve()) for path in images)]
    command.append("-")
    code = run_process(command, cwd=output_dir, timeout=timeout, log_path=output_dir / "codex-events.jsonl", stdin=prompt)
    if code or not response_path.exists():
        raise RuntimeError(f"Codex proposal failed (exit {code}); see {output_dir / 'codex-events.jsonl'}")
    proposal = json.loads(response_path.read_text())
    validate_policy(proposal["policy"])
    (output_dir / "candidate.py").write_text(proposal["policy"])
    return proposal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--instance", type=int, default=26)
    parser.add_argument("--seed", type=int, default=2026091500)
    parser.add_argument("--policy", type=Path, default=Path(__file__).with_name("visual_policy.py"))
    parser.add_argument("--sam3-url", default="http://127.0.0.1:8114")
    parser.add_argument("--grounding", choices=("sam3", "codex-pixels"), default="sam3")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--trial-timeout", type=int, default=600)
    parser.add_argument("--codex-timeout", type=int, default=300)
    evidence_group = parser.add_mutually_exclusive_group()
    evidence_group.add_argument("--refine-only", type=Path, help="One Codex revision from existing visual evidence; no simulation")
    evidence_group.add_argument("--from-evidence", type=Path, help="Start the complete revision/rollout loop from an existing visual attempt")
    parser.add_argument("--reference-dir", type=Path, help="Action-free RGB keyframes from reference_keyframes.py")
    args = parser.parse_args()
    if not 26 <= args.instance <= 35:
        parser.error("This development runner is restricted to instances 26-35; no held-out evaluation")
    if min(args.max_attempts, args.trial_timeout, args.codex_timeout) <= 0:
        parser.error("Attempt and time budgets must be positive")
    root = Path(__file__).resolve().parents[2]
    policy = args.policy.read_text()
    validate_policy(policy)
    reference_images = []
    if args.reference_dir:
        provenance = json.loads((args.reference_dir / "provenance.json").read_text())
        if provenance.get("action_columns_read") is not False or provenance.get("training_reference_only") is not True:
            parser.error("Reference directory must contain action-free training RGB provenance")
        heads = list(args.reference_dir.glob("zed_link*_frame_*.png"))
        if not heads:
            parser.error("Reference directory contains no head-camera RGB keyframes")
        for skill in provenance["skills"]:
            description = " ".join(skill["description"])
            if "pick" in description or "press" in description:
                start, end = skill["frames"]
                targets = [end - 1] if "pick" in description else [(start + end) // 2, end - 1]
                for frame in targets:
                    image = min(heads, key=lambda path: abs(int(path.stem.rsplit("_", 1)[1]) - frame))
                    if image not in reference_images:
                        reference_images.append(image)
    initial_evidence = args.refine_only or args.from_evidence
    if initial_evidence:
        payload = json.loads((initial_evidence / "result.json").read_text())
        if payload.get("ground_truth_object_state") is not False or payload.get("demonstration_actions") is not False:
            parser.error("Refinement evidence must come from the visual runner, not the replay baseline")
        if payload["instance"] != args.instance:
            parser.error("Evidence instance differs from the requested development instance")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    state = {"method": f"local ASPIRE adaptation, external Codex + {args.grounding}, not paper-protocol replication",
             "grounding_backend": args.grounding,
             "instance": args.instance, "seed": args.seed, "max_attempts": args.max_attempts,
             "trial_timeout": args.trial_timeout, "codex_timeout": args.codex_timeout,
             "initial_policy_sha256": hashlib.sha256(policy.encode()).hexdigest(),
             "status": "running", "task_success": False, "attempts": []}
    state["training_reference_images"] = [str(path) for path in reference_images]
    def save_state():
        (args.output_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    save_state()
    skills = ("No generalized frozen skill library yet. Reuse working parts of the supplied code when the "
              "prior rollout supports them; append missing goal-completion behavior instead of restarting a "
              "successful grasp. Development evidence does not guarantee a grasp in a future reset.")
    if args.grounding == "codex-pixels":
        skills += ("\nTraining RGB reference ep31 shows right-hand handle grip/presentation, then LEFT-hand pressing "
                   "of the front circular control. This is an offline visual lesson, not an action replay. "
                   "Do not command the holding hand to chase the button. Both arms support solve_ik/move_hand/press_at_pixel.")
    def run_trial(policy_path, directory, *, capture_only=False):
        command = [sys.executable, str(Path(__file__).with_name("run_visual_policy.py")),
                   "--policy", str(policy_path.resolve()), "--instance", str(args.instance), "--seed", str(args.seed),
                   "--output-dir", str(directory.resolve()), "--sam3-url", args.sam3_url,
                   "--grounding", args.grounding, "--record-video"]
        if capture_only:
            command.append("--capture-only")
        return run_process(command, cwd=root, env=worker_environment(root), timeout=args.trial_timeout,
                           log_path=args.output_dir / f"{directory.name}.log")
    try:
        if args.refine_only:
            proposal = propose_policy(policy, args.refine_only, args.output_dir / "revision_001", skills,
                                      args.codex_timeout, grounding=args.grounding, reference_images=reference_images)
            (args.output_dir / "policy.py").write_text(proposal["policy"])
            state["status"] = "revision_only_not_evaluated"
            save_state()
            print(json.dumps(state, indent=2))
            return
        if args.grounding == "sam3":
            try:
                response = requests.get(args.sam3_url.rstrip("/") + "/openapi.json", timeout=5)
                response.raise_for_status()
                if "/segment" not in response.json().get("paths", {}):
                    raise ValueError("Service does not expose the ASPIRE SAM3 /segment API")
            except (requests.RequestException, ValueError) as error:
                state.update(status="perception_unavailable", error=str(error))
                save_state()
                print(json.dumps(state, indent=2))
                return
        if args.from_evidence:
            state["initial_evidence"] = str(args.from_evidence)
            save_state()
            proposal = propose_policy(policy, args.from_evidence, args.output_dir / "revision_initial", skills,
                                      args.codex_timeout, grounding=args.grounding, reference_images=reference_images)
            policy = proposal["policy"]
        elif args.grounding == "codex-pixels":
            current = args.output_dir / "policy.py"
            current.write_text(policy)
            capture = args.output_dir / "capture_initial"
            code = run_trial(current, capture, capture_only=True)
            if not (capture / "result.json").exists() or json.loads((capture / "result.json").read_text())["status"] != "capture_only":
                raise RuntimeError(f"Initial camera capture failed (exit {code})")
            state["initial_capture"] = str(capture)
            save_state()
            proposal = propose_policy(policy, capture, args.output_dir / "revision_initial", skills,
                                      args.codex_timeout, grounding=args.grounding, reference_images=reference_images)
            policy = proposal["policy"]
        for number in range(1, args.max_attempts + 1):
            current = args.output_dir / "policy.py"
            current.write_text(policy)
            directory = args.output_dir / f"attempt_{number:03d}"
            print(f"Executing visual code attempt {number}/{args.max_attempts}", flush=True)
            returncode = run_trial(current, directory)
            if not (directory / "result.json").exists():
                raise RuntimeError(f"Trial exited {returncode} without terminal artifacts")
            result = json.loads((directory / "result.json").read_text())
            state["attempts"].append({"attempt": number, "status": result["status"], "exit_code": returncode,
                                      "task_success": result["task_success"], "artifacts": str(directory)})
            save_state()
            if result["task_success"]:
                state.update(status="success", task_success=True)
                break
            if result["status"] in {"infrastructure_error", "perception_unavailable"}:
                state["status"] = result["status"]
                break
            if number == args.max_attempts:
                state["status"] = "budget_exhausted"
                break
            proposal = propose_policy(policy, directory, args.output_dir / f"revision_{number:03d}", skills,
                                      args.codex_timeout, grounding=args.grounding, reference_images=reference_images)
            policy = proposal["policy"]
            if proposal["lesson"]:
                skills += f"\nEvidence attempt {number}: {proposal['lesson']}"
                (args.output_dir / "skills-working.md").write_text(skills + "\n")
        save_state()
    except BaseException as error:
        state.update(status="runner_error", error=f"{type(error).__name__}: {error}")
        save_state()
        raise
    print(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
