"""Run one BEHAVIOR episode with Comet, letting a planner switch the language prompt between skills.

The episode is stepped by the official `Evaluator.step()` with the stock websocket
policy client, so physics, the time limit, metrics and video are identical to
`omnigibson.eval.eval`. The only addition is a `_prompt` key in each observation;
the patched Comet server (`openpi/shared/eval_b1k_wrapper.py`) switches to that
prompt and drops its queued actions. An empty prompt means the task sentence.

Two ways to drive it:

* plan mode: `--plan plan.json` runs a fixed list of prompt segments, then a tail.
  With no plan (or an empty one) this is the plain task-sentence baseline.
* interactive mode (no --plan): an outside planner writes commands into
  `<session>/cmd/NNNN.json` (see planner_client.py) and reads `<session>/out/NNNN.json`.

Commands (JSON):
  {"op": "run", "prompt": "pick up the rose from the bottom cabinet", "steps": 600,
   "until": ["grasp_right", "release_any", "base_stopped", "success"]}
      prompt null/"" = task sentence. Stops at the first `until` event or after `steps`.
  {"op": "observe"}                 save head + wrist images, no stepping
  {"op": "status"}                  proprioception summary, no stepping
  {"op": "end"}                     keep the current prompt until the time limit (official semantics)
  {"op": "end", "finish": "stop"}   score the episode right now instead (not comparable to official eval)

Everything the planner is shown is challenge-legal (RGB, proprioception, step count)
unless --show-goal-status is given. Per-literal goal status (privileged) is always
written to trace.jsonl and result.json for offline analysis.
"""
from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

GRASP_EVENTS = ("grasp_left", "grasp_right", "grasp_any")
RELEASE_EVENTS = ("release_left", "release_right", "release_any")
LEGAL_EVENTS = GRASP_EVENTS + RELEASE_EVENTS + ("base_stopped", "base_moving", "success")
PRIVILEGED_EVENTS = ("literal_change",)


def fmt_literal(pred) -> str:
    terms = [str(t) for t in pred.terms]
    if terms and terms[0] == "not":
        return "(not (" + " ".join(terms[1:]) + "))"
    return "(" + " ".join(terms) + ")"


class GoalTracker:
    """Per-literal goal status, computed exactly like metrics/task_metric.py (privileged, dev only)."""

    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.metric = next(m for m in evaluator.metrics if hasattr(m, "initial_predicate_states"))
        self.best_option = 0

    def snapshot(self, full=True):
        task = self.evaluator.env.task
        options = task.ground_goal_state_options
        initial = self.metric.initial_predicate_states
        indices = range(len(options)) if (full or len(options) <= 64) else [self.best_option]
        best = None
        for oi in indices:
            now = [bool(p.evaluate(task._evaluate_predicate)) for p in options[oi]]
            score = sum(int(n and not i) for n, i in zip(now, initial[oi])) / len(options[oi])
            if best is None or score > best[0]:
                best = (score, oi, now)
        score, oi, now = best
        self.best_option = oi
        literals = [{"literal": fmt_literal(p), "now": n, "at_start": bool(i)}
                    for p, n, i in zip(options[oi], now, initial[oi])]
        return {"partial_q": round(score, 4), "success": bool(task.success), "option": oi,
                "n_options": len(options), "literals": literals}


class Proprio:
    """Challenge-legal robot-state summary from the flattened observation."""

    def __init__(self, evaluator):
        from omnigibson.eval.utils.eval_utils import PROPRIOCEPTION_INDICES
        self.idx = PROPRIOCEPTION_INDICES["R1Pro"]
        self.evaluator = evaluator
        self.key = next(k for k in evaluator.obs if k.endswith("::proprio"))

    def read(self):
        p = self.evaluator.obs[self.key]
        p = p.numpy() if hasattr(p, "numpy") else p
        return {
            "gripper_left_width": round(float(p[self.idx["gripper_left_qpos"]].sum()), 4),
            "gripper_right_width": round(float(p[self.idx["gripper_right_qpos"]].sum()), 4),
            "base_speed": round(float((p[self.idx["base_qvel"]][:2] ** 2).sum() ** 0.5), 3),
            "base_yaw_rate": round(float(p[self.idx["base_qvel"]][2]), 3),
            "trunk_qpos": [round(float(x), 3) for x in p[self.idx["trunk_qpos"]]],
            "arm_left_speed": round(float((p[self.idx["arm_left_qvel"]] ** 2).sum() ** 0.5), 3),
            "arm_right_speed": round(float((p[self.idx["arm_right_qvel"]] ** 2).sum() ** 0.5), 3),
        }


class EventDetector:
    """Skill-boundary events from proprioception only.

    grasp_<arm>:   the jaw has closed (width fell below `closed_below` and stayed still for `window` steps).
                   Fires for any closure: thin items such as rose stems read ~0.0, the same as an empty jaw,
                   so whether something is actually held must be judged from the wrist image.
    release_<arm>: the jaw reopened past `open_above` after a closure.
    base_stopped / base_moving: base speed below / above thresholds for `window` steps.
    R1Pro jaw width = sum of the two finger joints: 0.10 fully open, ~0.0 closed.
    """

    def __init__(self, window=15, closed_below=0.09, open_above=0.095, stable=0.001):
        self.window, self.closed_below, self.open_above, self.stable = window, closed_below, open_above, stable
        self.hist = {"left": [], "right": [], "base": []}
        self.closed = {"left": False, "right": False}

    def update(self, pr):
        events = []
        for arm in ("left", "right"):
            w = pr[f"gripper_{arm}_width"]
            h = self.hist[arm]
            h.append(w)
            del h[:-self.window]
            if not self.closed[arm]:
                if len(h) == self.window and max(h) < self.closed_below and max(h) - min(h) < self.stable:
                    self.closed[arm] = True
                    events += [f"grasp_{arm}", "grasp_any"]
            elif w >= self.open_above:
                self.closed[arm] = False
                events += [f"release_{arm}", "release_any"]
        b = self.hist["base"]
        b.append(pr["base_speed"])
        del b[:-self.window]
        if len(b) == self.window:
            if max(b) < 0.02:
                events.append("base_stopped")
            elif min(b) > 0.05:
                events.append("base_moving")
        return events

    def jaw_state(self):
        return {arm: ("closed" if c else "open") for arm, c in self.closed.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True)
    ap.add_argument("--instance-index", type=int, required=True, help="public index 0-19 (instance 301-320)")
    ap.add_argument("--mode", default="public_test")
    ap.add_argument("--seed", type=int, default=0, help="rollout seed (official eval default 0)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--session", type=Path, required=True)
    ap.add_argument("--plan", type=Path, default=None)
    ap.add_argument("--max-steps", type=int, default=None, help="default: official 1.5x human mean")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--show-goal-status", action="store_true",
                    help="include privileged per-literal status in planner outputs (analysis only)")
    ap.add_argument("--trace-every", type=int, default=30)
    ap.add_argument("--check-every", type=int, default=150, help="interactive: steps per checkpoint (150 = 5 s)")
    ap.add_argument("--robot-config", default=None)
    args = ap.parse_args()

    import numpy as np
    import cv2
    from omegaconf import OmegaConf
    import omnigibson as og
    from omnigibson.utils import transform_utils as T
    from omnigibson.macros import gm
    from omnigibson.eval.evaluator import Evaluator, resolve_instance_ids
    from omnigibson.eval.utils.eval_utils import seed_everything

    gm.HEADLESS = True
    session = args.session
    (session / "cmd").mkdir(parents=True, exist_ok=False)
    (session / "out").mkdir()
    (session / "images").mkdir()
    (session / "json").mkdir()
    root = Path(__file__).resolve().parents[2]
    robot_cfg = OmegaConf.load(args.robot_config or root / "OmniGibson/omnigibson/eval/r1pro.yaml")
    base_seed = 0
    seed_everything(base_seed)
    instance_id = int(resolve_instance_ids(args.task, [args.instance_index], mode=args.mode)[0])
    cfg = OmegaConf.create({
        "env_wrapper": {"_target_": "omnigibson.eval.wrappers.RGBDFullResWrapper"},
        "policy_name": "websocket",
        "model": {"_target_": "omnigibson.eval.policies.WebsocketPolicy", "host": args.host, "port": args.port},
        "headless": True, "partial_scene_load": True, "max_steps": args.max_steps,
        "write_video": not args.no_video, "write_side_video": False,
        "mode": args.mode, "seed": base_seed, "task": {"name": args.task}, "robot": robot_cfg,
    })
    plan = json.loads(args.plan.read_text()) if args.plan else None
    header = {"task": args.task, "instance_id": instance_id, "instance_index": args.instance_index,
              "seed": args.seed, "mode": args.mode, "plan": plan, "plan_file": str(args.plan) if args.plan else None,
              "show_goal_status": args.show_goal_status, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (session / "session.json").write_text(json.dumps(header, indent=1))
    trace = (session / "trace.jsonl").open("a")

    def log(event, **fields):
        trace.write(json.dumps({"event": event, **fields}, default=str) + "\n")
        trace.flush()

    with Evaluator(cfg) as evaluator:
        evaluator.reset(seed=base_seed)
        evaluator.load_task_instance(instance_id)
        evaluator.reset(seed=args.seed)
        video_path = session / f"{args.task}_{instance_id}_0.mp4"
        if not args.no_video:
            evaluator.start_recording(str(video_path))

        state = {"prompt": None, "steps": 0, "done": False, "terminated": False, "truncated": False}
        max_steps = next((getattr(c, "_max_steps") for c in evaluator.env.task._termination_conditions.values()
                          if hasattr(c, "_max_steps")), None)

        original_preprocess = evaluator._preprocess_obs

        def preprocess(obs):
            out = original_preprocess(obs)
            out["_prompt"] = state["prompt"] or ""
            if state.get("clear_queue"):
                out["_clear_queue"] = True
            return out

        evaluator._preprocess_obs = preprocess
        evaluator.obs["_prompt"] = ""
        goals = GoalTracker(evaluator)
        proprio = Proprio(evaluator)
        detector = EventDetector()
        segments = []
        commands = []
        mon = {"left_hover": 0, "right_hover": 0, "base_idle": 0, "since_jaw_event": 0}

        def monitor_update(pr, ev):
            for arm in ("left", "right"):
                still = pr[f"arm_{arm}_speed"] < 0.05
                open_ = pr[f"gripper_{arm}_width"] > 0.095
                mon[f"{arm}_hover"] = mon[f"{arm}_hover"] + 1 if (still and open_) else 0
            mon["base_idle"] = mon["base_idle"] + 1 if pr["base_speed"] < 0.02 else 0
            mon["since_jaw_event"] = 0 if any(e.startswith(("grasp_", "release_")) for e in ev) else mon["since_jaw_event"] + 1

        def monitor_report():
            return {k + "_s": round(v / 30, 1) for k, v in mon.items()}
        cameras = {k: evaluator.robot_camera_names[k] + "::rgb" for k in ("head", "left_wrist", "right_wrist")}

        def save_images(tag):
            paths = {}
            for cam, key in cameras.items():
                if key not in evaluator.obs:
                    continue
                img = evaluator.obs[key]
                img = img.numpy() if hasattr(img, "numpy") else np.asarray(img)
                img = img[..., :3].astype(np.uint8)
                path = session / "images" / f"{tag}_{cam}.png"
                bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(path), bgr)
                paths[cam] = str(path)
                # pointing aid: native-resolution copy with a labelled pixel grid every 40 px
                g = bgr.copy()
                H, W = g.shape[:2]
                for x in range(0, W, 40):
                    cv2.line(g, (x, 0), (x, H - 1), (255, 255, 0) if x % 200 else (0, 255, 255), 1)
                    cv2.putText(g, str(x), (x + 2, 12), 0, 0.35, (0, 255, 255), 1)
                for y in range(0, H, 40):
                    cv2.line(g, (0, y), (W - 1, y), (255, 255, 0) if y % 200 else (0, 255, 255), 1)
                    cv2.putText(g, str(y), (2, y + 12), 0, 0.35, (0, 255, 255), 1)
                gp = session / "images" / f"{tag}_{cam}_grid.png"
                cv2.imwrite(str(gp), g)
                paths[cam + "_grid"] = str(gp)
            # one composite: wrists stacked left, head right (same layout as the eval video)
            try:
                head = cv2.resize(cv2.imread(paths["head"]), (448, 448))
                lw = cv2.resize(cv2.imread(paths["left_wrist"]), (224, 224))
                rw = cv2.resize(cv2.imread(paths["right_wrist"]), (224, 224))
                comp = np.hstack([np.vstack([lw, rw]), head])
                cp = session / "images" / f"{tag}_panel.png"
                cv2.imwrite(str(cp), comp)
                paths["panel"] = str(cp)
            except Exception:
                pass
            return paths

        # ---------------- scripted base control (planner takeover); legal inputs only ----------------
        import math
        import torch as th
        from omnigibson.eval.utils.eval_utils import PROPRIOCEPTION_INDICES
        PI = PROPRIOCEPTION_INDICES["R1Pro"]
        comet_policy = evaluator.policy
        dt = 1.0 / 30.0
        VEL_SCALE, YAW_SCALE = 0.75, 1.0          # r1pro.yaml base command_output_limits
        MAX_V, MAX_W = 0.35, 0.6
        YAW_GAIN_CCW, YAW_GAIN_CW = 0.82, 0.92

        class _Scripted:
            needs_fresh_observation = True
            rollout_status = None

            def __init__(self, fn):
                self.fn = fn

            def forward(self, obs, *a, **k):
                return self.fn(obs)

        def last_gripper_cmds():
            a = evaluator.robot_action
            if isinstance(a, th.Tensor) and a.numel() >= 23:
                a = a.reshape(-1)
                return float(a[14]), float(a[22])
            return 1.0, 1.0   # nothing commanded yet: the robot starts with open jaws

        grip_override = {}

        def hold_action(vx=0.0, vy=0.0, wz=0.0):
            p = evaluator.obs[proprio.key]
            p = p.numpy() if hasattr(p, "numpy") else np.asarray(p)
            gl, gr = last_gripper_cmds()
            gl = grip_override.get("left", gl)
            gr = grip_override.get("right", gr)
            a = th.zeros(23, dtype=th.float32)
            a[0] = max(-1.0, min(1.0, vx / VEL_SCALE))
            a[1] = max(-1.0, min(1.0, vy / VEL_SCALE))
            a[2] = max(-1.0, min(1.0, wz / YAW_SCALE))
            a[3:7] = th.as_tensor(p[PI["trunk_qpos"]], dtype=th.float32)
            a[7:14] = th.as_tensor(p[PI["arm_left_qpos"]], dtype=th.float32)
            a[14] = gl
            a[15:22] = th.as_tensor(p[PI["arm_right_qpos"]], dtype=th.float32)
            a[22] = gr
            return a

        def scripted_steps(n_max, controller, action_fn=None):
            """Step the evaluator with a scripted action; controller(pose) -> (vx, vy, wz, done)."""
            action_fn = action_fn or hold_action
            pose = [0.0, 0.0, 0.0]   # x, y, yaw in the frame where the takeover started (body-velocity odometry)
            cmd = {"v": (0.0, 0.0, 0.0)}
            evaluator.policy = _Scripted(lambda obs: action_fn(*cmd["v"]))
            used, finished = 0, False
            try:
                while used < n_max and not state["done"]:
                    vx, vy, wz, finished = controller(pose)
                    if finished:
                        break
                    cmd["v"] = (vx, vy, wz)
                    terminated, truncated = evaluator.step()
                    state["steps"] += 1
                    used += 1
                    p = evaluator.obs[proprio.key]
                    p = p.numpy() if hasattr(p, "numpy") else np.asarray(p)
                    bvx, bvy, bwz = [float(x) for x in p[PI["base_qvel"]]]
                    c, s_ = math.cos(pose[2]), math.sin(pose[2])
                    pose[0] += (c * bvx - s_ * bvy) * dt
                    pose[1] += (s_ * bvx + c * bvy) * dt
                    # proprio yaw rate over-reads the real rotation; factors measured against sim ground
                    # truth on 2026-09-23 (8 turns, rose 311): 0.82 counter-clockwise, 0.92 clockwise
                    pose[2] += bwz * dt * (YAW_GAIN_CCW if bwz > 0 else YAW_GAIN_CW)
                    detector.update(proprio.read())
                    if state["steps"] % args.trace_every == 0:
                        g = goals.snapshot(full=False)
                        log("tick", step=state["steps"], prompt="<planner base control>", proprio=proprio.read(),
                            partial_q=g["partial_q"], changed=[])
                    if terminated or truncated:
                        state.update(done=True, terminated=bool(terminated), truncated=bool(truncated))
                # settle: zero velocity for a short while
                cmd["v"] = (0.0, 0.0, 0.0)
                for _ in range(15):
                    if state["done"]:
                        break
                    terminated, truncated = evaluator.step()
                    state["steps"] += 1
                    used += 1
                    if terminated or truncated:
                        state.update(done=True, terminated=bool(terminated), truncated=bool(truncated))
            finally:
                evaluator.policy = comet_policy
                state["clear_queue"] = True        # Comet must re-plan from the new state
                evaluator.obs["_clear_queue"] = True
            return used, finished, pose

        import math  # noqa: F811

        def move_base(forward=0.0, left=0.0, turn_deg=0.0, max_steps=900, gentle=False):
            target = (float(forward), float(left), math.radians(float(turn_deg)))
            vmax, wmax = (MAX_V * 0.45, MAX_W * 0.5) if gentle else (MAX_V, MAX_W)
            prog = {"best": float("inf"), "since": 0}

            def ctrl(pose):
                ex, ey, eth = target[0] - pose[0], target[1] - pose[1], target[2] - pose[2]
                dist = math.hypot(ex, ey)
                if dist < 0.015 and abs(eth) < math.radians(2.0):
                    return 0, 0, 0, True
                err = dist + 0.3 * abs(eth)
                if err < prog["best"] - 0.005:
                    prog["best"], prog["since"] = err, 0
                else:
                    prog["since"] += 1
                if prog["since"] > 90:
                    return 0, 0, 0, True        # blocked: no progress for 3 s
                c, s_ = math.cos(pose[2]), math.sin(pose[2])
                rx, ry = c * ex + s_ * ey, -s_ * ex + c * ey      # error in the robot frame
                scale = min(1.0, vmax / max(1e-6, 1.5 * dist))
                return 1.5 * rx * scale, 1.5 * ry * scale, max(-wmax, min(wmax, 2.0 * eth)), False

            used, finished, pose = scripted_steps(max_steps, ctrl)
            reached = math.hypot(target[0] - pose[0], target[1] - pose[1]) < 0.05 and abs(target[2] - pose[2]) < math.radians(4)
            return {"base_steps": used, "reached": reached, "blocked": not reached and prog["since"] > 90,
                    "moved": {"forward": round(pose[0], 3), "left": round(pose[1], 3), "turn_deg": round(math.degrees(pose[2]), 1)}}

        def grip(arm, close=True, steps=45):
            """Planner takeover of one jaw: arms, trunk and base held still; -1 closes, +1 opens."""
            if arm not in ("left", "right"):
                raise ValueError("arm must be left or right")
            before = proprio.read()[f"gripper_{arm}_width"]
            grip_override[arm] = -1.0 if close else 1.0
            try:
                used, _, _ = scripted_steps(int(steps), lambda pose: (0.0, 0.0, 0.0, False))
            finally:
                grip_override.clear()
            after = proprio.read()[f"gripper_{arm}_width"]
            return {"arm": arm, "close": close, "steps": used, "width_before": before, "width_after": after}

        # ---------------- Show-Harness-style micro-control of one arm ----------------
        # Differential IK on the robot's own kinematics (arm joints only; trunk and base held).
        # Dev note: the Jacobian is read from the simulated articulation, which equals URDF kinematics
        # at the current joint encoders; a deployed version would compute it from the URDF instead.
        from omnigibson.utils.usd_utils import ControllableObjectViewAPI as CV
        robot = evaluator.robot
        root_path = robot.articulation_root_path
        arm_override = {}

        def hold_action_arm(vx=0.0, vy=0.0, wz=0.0):
            a = hold_action(vx, vy, wz)
            if "trunk" in arm_override:
                a[3:7] = arm_override["trunk"]
            for arm, q in arm_override.items():
                if arm == "trunk":
                    continue
                if arm == "left":
                    a[7:14] = q
                else:
                    a[15:22] = q
            return a

        def eef_rel(arm):
            link = robot.eef_link_names[arm]
            pos, quat = CV.get_all_link_relative_position_orientation(root_path, link)
            return th.as_tensor(np.asarray(pos[0]), dtype=th.float32).clone(), th.as_tensor(np.asarray(quat[0]), dtype=th.float32).clone()

        trunk_idx = th.as_tensor(np.asarray(robot.trunk_control_idx), dtype=th.long)
        q_lo = th.as_tensor(np.asarray(robot.joint_lower_limits), dtype=th.float64)
        q_hi = th.as_tensor(np.asarray(robot.joint_upper_limits), dtype=th.float64)

        def ik_step(arm, target_pos, target_mat, gain=1.0, max_dq=0.05, use_trunk=False, rot_weight=0.3):
            link = robot.eef_link_names[arm]
            q = th.as_tensor(np.asarray(CV.get_all_joint_positions(root_path)[0]), dtype=th.float64)
            jac = th.as_tensor(np.asarray(CV.get_all_relative_jacobians(root_path)[0]), dtype=th.float64)
            row = CV.get_link_index(root_path, link) - 1
            off = jac.shape[-1] - q.shape[-1]
            arm_idx = th.as_tensor(np.asarray(robot.arm_control_idx[arm]), dtype=th.long)
            idx = th.cat([trunk_idx, arm_idx]) if use_trunk else arm_idx
            J = jac[row][:, idx + off]
            pos, quat = eef_rel(arm)
            R = T.quat2mat(quat).double()
            e_pos = (target_pos.double() - pos.double())
            e_rot = 0.5 * (th.linalg.cross(R[:, 0], target_mat[:, 0].double()) + th.linalg.cross(R[:, 1], target_mat[:, 1].double())
                           + th.linalg.cross(R[:, 2], target_mat[:, 2].double()))
            err = th.cat([e_pos, rot_weight * e_rot])
            J = J.clone()
            J[3:] *= rot_weight
            lam = 0.05
            dq = J.T @ th.linalg.solve(J @ J.T + lam ** 2 * th.eye(6, dtype=J.dtype), gain * err)
            dq = th.clamp(dq, -max_dq, max_dq)
            qn = th.clamp(q[idx] + dq, q_lo[idx] + 1e-3, q_hi[idx] - 1e-3).float()
            if use_trunk:
                return (qn[len(trunk_idx):], qn[:len(trunk_idx)]), float(e_pos.norm()), float(e_rot.norm())
            return (qn, None), float(e_pos.norm()), float(e_rot.norm())

        def move_hand(arm, forward=0.0, left=0.0, up=0.0, yaw_deg=0.0, pitch_deg=0.0, max_steps=120, tol=0.004, use_trunk=True,
                      quat=None):
            """Move one end effector by a delta in the robot base frame (metres / degrees about base axes)."""
            if arm not in ("left", "right"):
                raise ValueError("arm must be left or right")
            from omnigibson.utils import transform_utils as T2
            pos0, quat0 = eef_rel(arm)
            R0 = T2.quat2mat(quat0)
            dR = T2.euler2mat(th.tensor([0.0, math.radians(pitch_deg), math.radians(yaw_deg)]))
            target_pos = pos0 + th.tensor([forward, left, up], dtype=th.float32)
            target_mat = (dR @ R0).float() if quat is None else T2.quat2mat(th.as_tensor(quat, dtype=th.float32)).float()
            info = {"err": None, "k": 0}
            dist = float(th.linalg.norm(target_pos - pos0))
            n_way = max(1, int(dist / 0.01))            # a waypoint every 1 cm
            max_steps = max(max_steps, n_way + 90)

            def ctrl(pose):
                info["k"] += 1
                frac = min(1.0, info["k"] / n_way)
                way = pos0 + frac * (target_pos - pos0)
                (qcmd, qtrunk), ep, er = ik_step(arm, way, target_mat, use_trunk=use_trunk)
                if frac < 1.0:
                    ep = ep + float(th.linalg.norm(target_pos - way))
                arm_override[arm] = qcmd
                if qtrunk is not None:
                    arm_override["trunk"] = qtrunk
                info["err"] = (ep, er)
                if ep < tol and er < math.radians(1.5):
                    return 0, 0, 0, True
                return 0.0, 0.0, 0.0, False

            try:
                used, finished, _ = scripted_steps(max_steps, ctrl, action_fn=hold_action_arm)
            finally:
                arm_override.clear()
            pos1, _ = eef_rel(arm)
            moved = (pos1 - pos0).tolist()
            return {"arm": arm, "steps": used, "reached": bool(finished), "trunk_used": use_trunk,
                    "requested": {"forward": forward, "left": left, "up": up, "yaw_deg": yaw_deg, "pitch_deg": pitch_deg},
                    "moved": {"forward": round(moved[0], 3), "left": round(moved[1], 3), "up": round(moved[2], 3)},
                    "residual_m": round(info["err"][0], 4) if info["err"] else None,
                    "hand_pos": [round(x, 3) for x in pos1.tolist()]}

        from omnigibson.eval.utils.eval_utils import CAMERA_INTRINSICS
        cam_order = [name for name in evaluator.robot_camera_names.values()
                     if name.split("::")[1] in robot.sensors]

        def pixel_to_base(cam, u, v, win=4):
            """Back-project pixel (u right, v down) of camera `cam` to a point in the robot base frame.
            Uses only legal inputs: the depth image, fixed intrinsics and the official cam_rel_poses."""
            name = evaluator.robot_camera_names[cam]
            d = evaluator.obs[name + "::depth_linear"]
            d = d.numpy() if hasattr(d, "numpy") else np.asarray(d)
            H, W = d.shape[:2]
            u, v = int(round(u)), int(round(v))
            patch = d[max(0, v - win):v + win + 1, max(0, u - win):u + win + 1]
            patch = patch[np.isfinite(patch) & (patch > 0)]
            if patch.size == 0:
                raise ValueError(f"no valid depth near pixel ({u},{v}) in {cam}")
            z = float(np.min(patch))          # nearest surface in the window: the object, not the floor behind it
            K = CAMERA_INTRINSICS["R1Pro"][cam].astype(np.float64)
            sx, sy = W / (2 * K[0, 2]), H / (2 * K[1, 2])   # intrinsics are for the native size; rescale if needed
            fx, fy, cx, cy = K[0, 0] * sx, K[1, 1] * sy, K[0, 2] * sx, K[1, 2] * sy
            x = (u - cx) / fx * z
            y = (v - cy) / fy * z
            p_cam = np.array([x, -y, -z])     # OpenGL camera frame: +x right, +y up, looking along -z
            poses = evaluator.obs[f"{robot.name}::cam_rel_poses"]
            poses = poses.numpy() if hasattr(poses, "numpy") else np.asarray(poses)
            k = cam_order.index(name)
            pos, quat = poses[7 * k:7 * k + 3], poses[7 * k + 3:7 * k + 7]
            Rm = T.quat2mat(th.as_tensor(quat, dtype=th.float32)).numpy()
            return (Rm @ p_cam + pos), z

        def reach(arm, cam, u, v, above=0.10, forward_off=0.0, left_off=0.0, max_steps=240, use_trunk=True):
            p, z = pixel_to_base(cam, u, v)
            cur, _ = eef_rel(arm)
            delta = np.array(p) + np.array([forward_off, left_off, above]) - cur.numpy()
            r = move_hand(arm, float(delta[0]), float(delta[1]), float(delta[2]), max_steps=max_steps, use_trunk=use_trunk)
            r["target_point_base"] = [round(float(x), 3) for x in p]
            r["pixel_depth_m"] = round(z, 3)
            return r

        def cloud(cam, stride=4):
            """Base-frame point cloud of one camera from depth (legal inputs only). Returns (pts Nx3, uv Nx2)."""
            name = evaluator.robot_camera_names[cam]
            d = evaluator.obs[name + "::depth_linear"]
            d = d.numpy() if hasattr(d, "numpy") else np.asarray(d)
            H, W = d.shape[:2]
            vv, uu = np.mgrid[0:H:stride, 0:W:stride]
            z = d[vv, uu]
            ok = np.isfinite(z) & (z > 0.05) & (z < 3.0)
            uu, vv, z = uu[ok], vv[ok], z[ok]
            K = CAMERA_INTRINSICS["R1Pro"][cam].astype(np.float64)
            sx, sy = W / (2 * K[0, 2]), H / (2 * K[1, 2])
            fx, fy, cx, cy = K[0, 0] * sx, K[1, 1] * sy, K[0, 2] * sx, K[1, 2] * sy
            pc = np.stack([(uu - cx) / fx * z, -(vv - cy) / fy * z, -z], axis=1)
            poses = evaluator.obs[f"{robot.name}::cam_rel_poses"]
            poses = poses.numpy() if hasattr(poses, "numpy") else np.asarray(poses)
            k = cam_order.index(name)
            Rm = T.quat2mat(th.as_tensor(poses[7 * k + 3:7 * k + 7], dtype=th.float32)).numpy()
            return pc @ Rm.T + poses[7 * k:7 * k + 3], np.stack([uu, vv], axis=1)

        def detect_floor_objects(cams=("left_wrist", "right_wrist", "head"), zmin=0.012, zmax=0.17, max_range=1.2, min_range=0.36):
            """Small objects resting on the floor: points 1.2-17 cm above the floor plane, clustered in 3D (2 cm grid)."""
            found = []
            # robot's own fingers/hands (robot geometry, legal): drop points near them so a hovering hand
            # does not merge with the object under it
            bp, bq = robot.get_position_orientation()
            own = []
            for a_ in ("left", "right"):
                for link in list(robot.finger_links[a_]) + [robot.eef_links[a_]]:
                    lp, _ = link.get_position_orientation()
                    rel, _ = T.relative_pose_transform(lp, th.tensor([0, 0, 0, 1.0]), bp, bq)
                    own.append(rel.numpy())
            own = np.array(own)
            for cam in cams:
                pts, uv = cloud(cam, stride=3 if cam != "head" else 4)
                if len(own):
                    dmin = np.min(np.linalg.norm(pts[:, None, :] - own[None, :, :], axis=2), axis=1)
                    pts, uv = pts[dmin > 0.06], uv[dmin > 0.06]
                floor_z = np.percentile(pts[:, 2], 5) if (pts[:, 2] < 0.05).sum() > 50 else 0.0
                floor_z = min(floor_z, 0.02)
                rng = np.hypot(pts[:, 0], pts[:, 1])
                # min_range drops the robot's own base, wheels and arms seen from the wrist cameras
                m = (pts[:, 2] > floor_z + zmin) & (pts[:, 2] < floor_z + zmax) & (rng < max_range) & (rng > min_range)
                P = pts[m]
                if len(P) < 15:
                    continue
                cells = {}
                for i, c in enumerate(map(tuple, np.floor(P[:, :2] / 0.02).astype(int))):
                    cells.setdefault(c, []).append(i)
                seen, comps = set(), []
                for c in cells:
                    if c in seen:
                        continue
                    stack, comp = [c], []
                    seen.add(c)
                    while stack:
                        a = stack.pop()
                        comp += cells[a]
                        for dx in (-1, 0, 1):
                            for dy in (-1, 0, 1):
                                b = (a[0] + dx, a[1] + dy)
                                if b in cells and b not in seen:
                                    seen.add(b)
                                    stack.append(b)
                    comps.append(P[comp])
                for C in comps:
                    ext = C[:, :2].max(0) - C[:, :2].min(0)
                    if len(C) < 15 or ext.max() > 0.30 or ext.max() < 0.03:
                        continue   # too big (furniture, bin) or noise
                    xy = C[:, :2] - C[:, :2].mean(0)
                    w, V = np.linalg.eigh(xy.T @ xy / len(xy))
                    long_axis = V[:, 1]
                    found.append({"range_m": round(float(np.hypot(*C[:, :2].mean(0))), 3), "cam": cam, "center": C.mean(0).round(3).tolist(), "top_z": round(float(C[:, 2].max()), 3),
                                  "floor_z": round(float(floor_z), 3), "extent_xy": ext.round(3).tolist(), "n": int(len(C)),
                                  "long_axis_deg": round(float(np.degrees(np.arctan2(long_axis[1], long_axis[0]))), 1),
                                  "elongation": round(float(np.sqrt(max(w[1], 1e-9) / max(w[0], 1e-9))), 2)})
            # merge detections of the same object seen by several cameras (prefer wrist views)
            merged = []
            for f in sorted(found, key=lambda f: (f["cam"] == "head", -f["n"])):
                if all(np.hypot(f["center"][0] - g["center"][0], f["center"][1] - g["center"][1]) > 0.06 for g in merged):
                    merged.append(f)
            return merged

        def floor_tilt_deg():
            """Robot lean from the floor plane in head depth (points below 0.35 m, iterative refit, >=300 inliers)."""
            pts, _ = cloud("head", stride=4)
            floor = pts[pts[:, 2] < 0.35]
            coef = None
            for _ in range(4):
                if len(floor) < 300:
                    return None
                A = np.c_[floor[:, 0], floor[:, 1], np.ones(len(floor))]
                coef = np.linalg.lstsq(A, floor[:, 2], rcond=None)[0]
                res = np.abs(pts[:, 0] * coef[0] + pts[:, 1] * coef[1] + coef[2] - pts[:, 2])
                floor = pts[res < 0.03]
            if len(floor) < 300:
                return None
            return round(float(np.degrees(np.arctan(np.hypot(coef[0], coef[1])))), 1)

        def finger_axis_deg(arm):
            bp, bq = robot.get_position_orientation()   # robot-geometry query (URDF-equivalent)
            pts = []
            for link in robot.finger_links[arm]:
                lp, _ = link.get_position_orientation()
                rel, _ = T.relative_pose_transform(lp, th.tensor([0, 0, 0, 1.0]), bp, bq)
                pts.append(rel.numpy())
            d = pts[1] - pts[0]
            return float(np.degrees(np.arctan2(d[1], d[0])))

        GATE = {"max_size": 0.16, "min_h": 0.05, "max_h": 0.16}

        def graspable(o):
            """Size/reach gate shared by the supervisor and the retry (tunable per task via the `config` op)."""
            h = o["top_z"] - o["floor_z"]
            if max(o["extent_xy"]) > GATE["max_size"] or h >= GATE["max_h"] or h < GATE["min_h"] or o["n"] < 60:
                return False
            if not (0.38 <= o["range_m"] <= 0.85):
                return False
            if h < 0.10 and (o["range_m"] > 0.70 or o["n"] < 150):   # lying objects: must reach low, need a good axis
                return False
            return True

        def jaw_width(arm):
            return proprio.read()[f"gripper_{arm}_width"]

        def auto_grasp(arm, target=None, lift=0.2):
            """Detect a floor object near `arm`, grasp it across its short axis, lift. Returns a report."""
            other = "right" if arm == "left" else "left"
            rep = {"arm": arm, "steps_start": state["steps"], "stages": []}
            if target is None:
                objs = detect_floor_objects()
                if not objs:
                    rep["result"] = "no object detected"
                    return rep
                hand, _ = eef_rel(arm)
                objs.sort(key=lambda o: np.hypot(o["center"][0] - float(hand[0]), o["center"][1] - float(hand[1])))
                target = objs[0]
                rep["detections"] = objs[:4]
            rep["target"] = target
            # the arm cannot reach steeply down near the base: back up until the object is ~0.58 m ahead
            if target.get("range_m", 1.0) < 0.50:
                dx = float(target["center"][0]) - 0.58
                mb = move_base(forward=dx, max_steps=300, gentle=jaw_width(other) < 0.09)
                rep["stages"].append(("back_off", round(dx, 3), mb["reached"]))
                again = [o for o in detect_floor_objects() if graspable(o)
                         and np.hypot(o["center"][0] - (target["center"][0] - dx), o["center"][1] - target["center"][1]) < 0.15]
                if not again:
                    rep["result"] = "lost after back-off"
                    return rep
                target = max(again, key=lambda o: o["n"])
                rep["target_after_back_off"] = target
                rep["stages"].append(("raise_other", move_hand(other, up=0.2, use_trunk=False)["reached"]))
            if jaw_width(arm) < 0.095:
                grip(arm, close=False)
            cx, cy, cz = target["center"]
            above = max(target["top_z"], 0.05) + 0.12
            cur, _ = eef_rel(arm)
            r = move_hand(arm, cx - float(cur[0]), cy - float(cur[1]), above - float(cur[2]), max_steps=260)
            rep["stages"].append(("reach", r["reached"], r["residual_m"]))
            # rotate so the finger line is perpendicular to the object's long axis (only if elongated)
            if target["elongation"] > 1.5 and max(target["extent_xy"]) >= 0.10:
                want = target["long_axis_deg"] + 90.0
                have = finger_axis_deg(arm)
                dyaw = (want - have + 90.0) % 180.0 - 90.0      # finger line is symmetric under 180 deg
                r = move_hand(arm, yaw_deg=dyaw)
                rep["stages"].append(("rotate", round(dyaw, 1), r["reached"]))
            # descend: eef about 3 cm above the object's centre height, never below 4.5 cm off the floor
            mid_z = 0.5 * (target["floor_z"] + target["top_z"])     # visible points are the top; the centre is lower
            grasp_z = max(mid_z + 0.026, target["floor_z"] + 0.045)
            cur, _ = eef_rel(arm)
            r = move_hand(arm, cx - float(cur[0]), cy - float(cur[1]), grasp_z - float(cur[2]), max_steps=200)
            rep["stages"].append(("descend", r["reached"], r["residual_m"]))
            g = grip(arm, close=True)
            rep["stages"].append(("close", g["width_after"]))
            if not (0.01 < g["width_after"] < 0.095):   # closed on air, or blocked open
                grip(arm, close=False)
                move_hand(arm, up=0.12)
                rep["result"] = "miss"
                return rep
            r = move_hand(arm, up=float(lift))
            rep["stages"].append(("lift", r["reached"]))
            rep["width_after_lift"] = jaw_width(arm)
            rep["result"] = "held" if 0.01 < rep["width_after_lift"] < 0.095 else "dropped"
            rep["steps_used"] = state["steps"] - rep["steps_start"]
            return rep

        CONTAINER_PARAMS = {"rmin": 0.06, "rmax": 0.24, "zlo": -0.08, "zhi": 0.08}

        def detect_held_container(holder, cam="head", **kw):
            """Mouth of a container hanging from `holder`'s jaw, from head depth.

            Rim and upper-wall points lie in a band around the hand's height; the robot's own arm is above that band
            and the container's interior/bottom below it. Mouth centre = centre of the band's xy bounding box."""
            p = {**CONTAINER_PARAMS, **{k: v for k, v in kw.items() if v is not None}}
            hand, _ = eef_rel(holder)
            h = hand.numpy()
            pts, _ = cloud(cam, stride=2)
            d = np.hypot(pts[:, 0] - h[0], pts[:, 1] - h[1])
            m = (d > p["rmin"]) & (d < p["rmax"]) & (pts[:, 2] > h[2] + p["zlo"]) & (pts[:, 2] < h[2] + p["zhi"])
            P = pts[m]
            if len(P) < 60:
                return None
            lo, hi = np.percentile(P[:, :2], 3, axis=0), np.percentile(P[:, :2], 97, axis=0)
            c = (lo + hi) / 2
            return {"mouth_center": [round(float(c[0]), 3), round(float(c[1]), 3), round(float(np.percentile(P[:, 2], 90)), 3)],
                    "extent_xy": (hi - lo).round(3).tolist(), "n": int(len(P)), "params": p,
                    "hand": [round(float(x), 3) for x in h.tolist()]}

        TRUNK_UPRIGHT = th.tensor([1.023, -1.444, -0.47, 0.0])   # R1Pro reset posture (from the start of every episode)

        def trunk_to(target=None, max_rate=0.02, max_steps=240):
            """Move the trunk joints to `target` (default: upright start posture) with both arms held at their joints."""
            target = TRUNK_UPRIGHT if target is None else th.as_tensor(target, dtype=th.float32)
            info = {"k": 0}

            def ctrl(pose):
                q = th.as_tensor(np.asarray(CV.get_all_joint_positions(root_path)[0]), dtype=th.float32)[trunk_idx]
                err = target - q
                if float(err.abs().max()) < 0.01:
                    return 0, 0, 0, True
                arm_override["trunk"] = q + th.clamp(err, -max_rate * 3, max_rate * 3)
                return 0.0, 0.0, 0.0, False

            try:
                used, finished, _ = scripted_steps(max_steps, ctrl, action_fn=hold_action_arm)
            finally:
                arm_override.clear()
            return {"steps": used, "reached": bool(finished)}

        # Release posture measured from 104 human can releases in picking_up_trash demos (left hand holds the can,
        # right hand holds the bin rim). Base frame, metres. Mirrored in y when the roles are swapped.
        DEMO_PLACE = {"trunk": [1.074, -1.539, -0.856, 0.0], "holder_eef": [0.645, -0.191, 0.546],
                      "object_minus_holder": [-0.04, 0.186, 0.071],
                      "holder_quat": [-0.084, 0.983, -0.028, 0.159], "object_quat": [0.022, 0.888, -0.402, 0.223]}

        def mirror_quat(q):
            """Mirror a base-frame orientation through the robot's xz plane (left <-> right)."""
            Rm = T.quat2mat(th.as_tensor(q, dtype=th.float32)).numpy()
            M = np.diag([1.0, -1.0, 1.0])
            Rn = M @ Rm @ M
            return T.mat2quat(th.as_tensor(Rn, dtype=th.float32)).tolist()

        def auto_place_demo(arm):
            holder = "right" if arm == "left" else "left"
            sgn = 1.0 if arm == "left" else -1.0
            rep = {"arm": arm, "holder": holder, "steps_start": state["steps"], "stages": []}
            rep["stages"].append(("trunk", trunk_to(DEMO_PLACE["trunk"])["reached"]))
            hx, hy, hz = DEMO_PLACE["holder_eef"]
            hy *= sgn
            cur, _ = eef_rel(holder)
            hq = DEMO_PLACE["holder_quat"] if sgn > 0 else mirror_quat(DEMO_PLACE["holder_quat"])
            r = move_hand(holder, hx - float(cur[0]), hy - float(cur[1]), hz - float(cur[2]), use_trunk=False, max_steps=240, quat=hq)
            rep["stages"].append(("holder", r["reached"], r["residual_m"]))
            if (r["residual_m"] or 0) > 0.02:            # arm alone can't: let the trunk help (moves both held objects)
                cur, _ = eef_rel(holder)
                r = move_hand(holder, hx - float(cur[0]), hy - float(cur[1]), hz - float(cur[2]), use_trunk=True, max_steps=240, quat=hq)
                rep["stages"].append(("holder_trunk", r["reached"], r["residual_m"]))
            c = detect_held_container(holder)
            rep["container"] = c
            hcur, _ = eef_rel(holder)
            if c is not None and max(c["extent_xy"]) > 0.12:
                mx, my, mz = c["mouth_center"]
                tx, ty, tz = mx, my, mz + 0.13          # can centre ~3 cm under the eef, can half-height ~6 cm
                rep["aim"] = "vision"
            else:                                        # fall back to the demo offset from the holder hand
                ox, oy, oz = DEMO_PLACE["object_minus_holder"]
                tx, ty, tz = float(hcur[0]) + ox, float(hcur[1]) + sgn * oy, float(hcur[2]) + oz
                rep["aim"] = "demo_offset"
            cur, _ = eef_rel(arm)
            oq = DEMO_PLACE["object_quat"] if sgn > 0 else mirror_quat(DEMO_PLACE["object_quat"])
            r = move_hand(arm, tx - float(cur[0]), ty - float(cur[1]), tz - float(cur[2]), use_trunk=False, max_steps=240, quat=oq)
            rep["stages"].append(("object", r["reached"], r["residual_m"]))
            g = grip(arm, close=False, steps=30)
            scripted_steps(30, lambda pose: (0.0, 0.0, 0.0, False))
            rep["stages"].append(("release", g["width_after"]))
            rep["result"] = "released"
            rep["steps_used"] = state["steps"] - rep["steps_start"]
            # privileged, trace only (never returned to the supervisor): did it land inside?
            gs = goals.snapshot()
            rep["_dev_inside_after"] = [l["literal"] for l in gs["literals"] if l["now"]]
            return rep

        def own_points_mask(pts, radius=0.09):
            """True for points near the robot's own hand/finger links (robot geometry)."""
            bp, bq = robot.get_position_orientation()
            own = []
            for a_ in ("left", "right"):
                for link in list(robot.finger_links[a_]) + [robot.eef_links[a_]]:
                    lp, _ = link.get_position_orientation()
                    rel, _ = T.relative_pose_transform(lp, th.tensor([0, 0, 0, 1.0]), bp, bq)
                    own.append(rel.numpy())
            own = np.array(own)
            return np.min(np.linalg.norm(pts[:, None, :] - own[None, :, :], axis=2), axis=1) < radius

        def detect_floor_container(min_size=0.20, max_size=0.45, max_range=3.5):
            """A bucket/box standing on the floor: head-depth cluster 12-45 cm tall with a large footprint."""
            pts, _ = cloud("head", stride=2)
            pts = pts[~own_points_mask(pts, 0.12)]
            rng = np.hypot(pts[:, 0], pts[:, 1])
            m = (pts[:, 2] > 0.04) & (pts[:, 2] < 0.45) & (rng > 0.3) & (rng < max_range)
            P = pts[m]
            if len(P) < 100:
                return None
            cells = {}
            for i, c in enumerate(map(tuple, np.floor(P[:, :2] / 0.03).astype(int))):
                cells.setdefault(c, []).append(i)
            seen, best = set(), None
            for c in cells:
                if c in seen:
                    continue
                stack, comp = [c], []
                seen.add(c)
                while stack:
                    a = stack.pop()
                    comp += cells[a]
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            b = (a[0] + dx, a[1] + dy)
                            if b in cells and b not in seen:
                                seen.add(b); stack.append(b)
                C = P[comp]
                ext = C[:, :2].max(0) - C[:, :2].min(0)
                h = C[:, 2].max()
                if not (min_size <= ext.max() <= max_size and 0.12 <= h <= 0.45 and len(C) > 40):
                    continue
                if best is None or len(C) > best["n"]:
                    best = {"center": C[:, :2].mean(0).round(3).tolist() + [round(float(h), 3)],
                            "extent_xy": ext.round(3).tolist(), "top_z": round(float(h), 3), "n": int(len(C))}
            return best

        def drop_into_floor_container(arm, c, standoff=0.62, leg=0.5, max_range=1.0):
            """Carry the held object to a floor container and release it 16 cm above the rim."""
            rep = {"arm": arm, "container": c, "stages": [], "steps_start": state["steps"]}
            if float(np.hypot(c["center"][0], c["center"][1])) > max_range:
                rep["result"] = "too far"; return rep
            cur, _ = eef_rel(arm)
            if float(cur[2]) < 0.45:                         # never drive with the load near the floor
                r = move_hand(arm, up=0.50 - float(cur[2]), use_trunk=True, max_steps=200)
                rep["stages"].append(("raise", r["reached"]))
            for _ in range(8):
                cx, cy, top = c["center"]
                rng = float(np.hypot(cx, cy))
                ang = math.degrees(math.atan2(cy, cx))
                if rng <= standoff + 0.12 and abs(ang) < 20:
                    break
                if abs(ang) > 8:
                    move_base(turn_deg=ang, max_steps=300, gentle=True)
                if rng > standoff + 0.12:
                    ahead = send_free_space()
                    if ahead is not None and ahead < 0.55:
                        rep["result"] = f"blocked (free {ahead} m)"; return rep
                    move_base(forward=min(leg, rng - standoff), max_steps=300, gentle=True)
                c2 = detect_floor_container()
                if c2 is None:
                    rep["result"] = "container lost"; return rep
                c = c2
            rep["stages"].append(("approach_done", [round(x, 2) for x in c["center"]]))
            cx, cy, top = c["center"]
            cur, _ = eef_rel(arm)
            r = move_hand(arm, cx - float(cur[0]), cy - float(cur[1]), (top + 0.16) - float(cur[2]), use_trunk=True, max_steps=260)
            rep["stages"].append(("over", r["reached"], r["residual_m"]))
            if (r["residual_m"] or 1) > 0.06:
                rep["result"] = "cannot reach"; return rep
            g = grip(arm, close=False, steps=30)
            scripted_steps(30, lambda pose: (0.0, 0.0, 0.0, False))
            rep["stages"].append(("release", g["width_after"]))
            rep["result"] = "released"
            rep["steps_used"] = state["steps"] - rep["steps_start"]
            gs = goals.snapshot()
            rep["_dev_inside_after"] = [l["literal"] for l in gs["literals"] if l["now"]]
            return rep

        def send_free_space():
            name = evaluator.robot_camera_names["head"]
            d = evaluator.obs[name + "::depth_linear"]
            d = d.numpy() if hasattr(d, "numpy") else np.asarray(d)
            H, W = d.shape[:2]
            v = d[H // 3: H * 2 // 3, W // 3: W * 2 // 3]
            v = v[np.isfinite(v) & (v > 0)]
            return round(float(np.percentile(v, 10)), 2) if v.size else None

        def auto_place(arm, stage=(0.55, -0.02, 0.40)):
            """Put the object held by `arm` into the container held by the other hand."""
            holder = "right" if arm == "left" else "left"
            rep = {"arm": arm, "holder": holder, "steps_start": state["steps"], "stages": []}
            rep["stages"].append(("trunk_upright", trunk_to()["reached"]))
            sx, sy, sz = stage
            if holder == "left":
                sy = -sy
            cur, _ = eef_rel(holder)
            r = move_hand(holder, sx - float(cur[0]), sy - float(cur[1]), sz - float(cur[2]), use_trunk=False, max_steps=200)
            rep["stages"].append(("stage_container", r["reached"], r["residual_m"]))
            c = detect_held_container(holder)
            rep["container"] = c
            if c is None:
                rep["result"] = "container not seen"
                return rep
            mx, my, mz = c["mouth_center"]
            cur, _ = eef_rel(arm)
            r = move_hand(arm, mx - float(cur[0]), my - float(cur[1]), (mz + 0.14) - float(cur[2]), use_trunk=False, max_steps=240)
            rep["stages"].append(("over_mouth", r["reached"], r["residual_m"]))
            if not r["reached"] and r["residual_m"] and r["residual_m"] > 0.05:
                # meet halfway: bring the container under the object instead
                obj, _ = eef_rel(arm)
                hcur, _ = eef_rel(holder)
                dx, dy = float(obj[0]) - mx, float(obj[1]) - my
                r2 = move_hand(holder, dx, dy, 0.0, use_trunk=False, max_steps=200)
                rep["stages"].append(("container_to_object", r2["reached"], r2["residual_m"]))
            g = grip(arm, close=False, steps=30)
            scripted_steps(30, lambda pose: (0.0, 0.0, 0.0, False))
            rep["stages"].append(("release", g["width_after"]))
            rep["result"] = "released"
            rep["steps_used"] = state["steps"] - rep["steps_start"]
            return rep

        snapshots = {}

        def save_snapshot(name):
            flat = og.sim.dump_state(serialized=True)
            bp, bq = robot.get_position_orientation()
            snap = {"sim": flat, "steps": state["steps"], "env_step": evaluator.env._current_step,
                    "prompt": state["prompt"], "detector": {"closed": dict(detector.closed)},
                    "task": args.task, "instance_id": instance_id,
                    "base_pose": [bp.tolist(), bq.tolist()],
                    "last_action": (evaluator.robot_action.reshape(-1).tolist()
                                    if isinstance(evaluator.robot_action, th.Tensor) else None)}
            snapshots[name] = snap
            (session / "snapshots").mkdir(exist_ok=True)
            path = session / "snapshots" / f"{name}.pt"
            th.save(snap, path)
            return {"saved": name, "step": state["steps"], "path": str(path)}

        def load_snapshot(name):
            if name in snapshots:
                snap = snapshots[name]
            else:   # a path to a .pt saved by any session of the same task instance
                snap = th.load(name, weights_only=False)
                if snap["task"] != args.task or snap["instance_id"] != instance_id:
                    raise ValueError(f"snapshot is for {snap['task']} {snap['instance_id']}")
            og.sim.load_state(snap["sim"], serialized=True)
            # one physics step so kinematics and pose-dependent states (Inside, OnTop, cameras) catch up
            og.sim.step()
            bp, bq = robot.get_position_orientation()
            if "base_pose" in snap:
                err = float(np.linalg.norm(np.array(snap["base_pose"][0][:2]) - bp[:2].numpy()))
                log("load_check", base_pose_error_m=round(err, 4))
            state["steps"] = snap["steps"]
            evaluator.env._current_step = snap["env_step"]
            state["prompt"] = snap["prompt"]
            detector.closed = dict(snap["detector"]["closed"])
            for k in detector.hist:
                detector.hist[k] = []
            state["clear_queue"] = True
            evaluator.obs["_clear_queue"] = True
            # refresh the observation after the state jump: render a few frames so the RTX sensors update
            for _ in range(4):
                og.sim.render()
            raw, _ = evaluator.env.get_obs()
            evaluator.obs = evaluator._preprocess_obs(evaluator._sync_lights_and_get_obs(raw))
            if snap.get("last_action") is not None:
                evaluator.robot_action = th.tensor(snap["last_action"], dtype=th.float32)
            else:   # older snapshot: infer jaw commands from the restored finger widths
                pr0 = proprio.read()
                a0 = th.zeros(23)
                a0[14] = -1.0 if pr0["gripper_left_width"] < 0.09 else 1.0
                a0[22] = -1.0 if pr0["gripper_right_width"] < 0.09 else 1.0
                evaluator.robot_action = a0
            evaluator.robot_action = hold_action()   # current joints, gripper commands from the snapshot
            return {"loaded": name, "step": state["steps"]}

        def run(prompt, steps, until=(), label=""):
            until = set(until or ())
            bad = until - set(LEGAL_EVENTS) - set(PRIVILEGED_EVENTS)
            if bad:
                raise ValueError(f"unknown until events {sorted(bad)}; legal: {LEGAL_EVENTS}")
            if until & set(PRIVILEGED_EVENTS) and not args.show_goal_status:
                raise ValueError("literal_change stops need --show-goal-status (privileged)")
            new_prompt = prompt or None
            if new_prompt != state["prompt"]:
                log("prompt", step=state["steps"], prompt=new_prompt)
            state["prompt"] = new_prompt
            evaluator.obs["_prompt"] = state["prompt"] or ""
            start = state["steps"]
            reason = "step budget"
            events_seen = []
            moved = False
            last_goal = goals.snapshot(full=False)
            last_true = {l["literal"]: l["now"] for l in last_goal["literals"]}
            for _ in range(int(steps)):
                if state["done"]:
                    reason = "episode over"
                    break
                terminated, truncated = evaluator.step()
                state["steps"] += 1
                if state.get("clear_queue"):
                    state["clear_queue"] = False
                    evaluator.obs.pop("_clear_queue", None)
                pr = proprio.read()
                ev = detector.update(pr)
                monitor_update(pr, ev)
                if "base_moving" in ev:
                    moved = True
                if not moved:  # "stopped" only counts after the base moved during this command
                    ev = [e for e in ev if e != "base_stopped"]
                if ev:
                    events_seen += [{"step": state["steps"], "event": e} for e in ev if e not in ("base_stopped", "base_moving")]
                if terminated or truncated:
                    state.update(done=True, terminated=bool(terminated), truncated=bool(truncated))
                    reason = "success" if evaluator.env.task.success else ("time limit" if truncated else "terminated")
                    break
                changed = []
                if state["steps"] % args.trace_every == 0:
                    g = goals.snapshot(full=False)
                    now_true = {l["literal"]: l["now"] for l in g["literals"]}
                    changed = [k for k, v in now_true.items() if last_true.get(k) != v]
                    last_true = now_true
                    log("tick", step=state["steps"], prompt=state["prompt"], proprio=pr, partial_q=g["partial_q"],
                        changed=changed)
                hit = until & set(ev)
                if "literal_change" in until and changed:
                    hit = {"literal_change"}
                if hit:
                    reason = "event: " + ",".join(sorted(hit))
                    break
            g = goals.snapshot(full=True)
            seg = {"label": label, "prompt": state["prompt"], "start": start, "end": state["steps"],
                   "reason": reason, "events": events_seen[-20:], "partial_q_after": g["partial_q"],
                   "true_literals_after": [l["literal"] for l in g["literals"] if l["now"]]}
            segments.append(seg)
            log("segment", **seg)
            out = {"steps_used": state["steps"] - start, "reason": reason, "step": state["steps"],
                   "step_limit": max_steps, "episode_over": state["done"], "prompt": state["prompt"],
                   "proprio": proprio.read(), "jaws": detector.jaw_state(), "events": events_seen[-20:],
                   "images": save_images(f"{len(segments):03d}_s{state['steps']}")}
            if args.show_goal_status:
                out["goal"] = g
            return out

        def wrist_depth():
            out = {}
            for cam in ("left_wrist", "right_wrist"):
                key = evaluator.robot_camera_names[cam] + "::depth_linear"
                if key not in evaluator.obs:
                    continue
                d = evaluator.obs[key]
                d = d.numpy() if hasattr(d, "numpy") else np.asarray(d)
                h, w = d.shape[:2]
                c = d[h * 2 // 5:h * 3 // 5, w * 2 // 5:w * 3 // 5]
                c = c[np.isfinite(c) & (c > 0)]
                out[cam] = round(float(np.median(c)), 3) if c.size else None
            return out

        def checkpoint(tag, extra=None):
            try:
                log("literals", step=state["steps"], true=[l["literal"] for l in goals.snapshot(full=False)["literals"] if l["now"]])
            except Exception:
                pass
            out = {"monitor": monitor_report(), "wrist_center_depth_m": wrist_depth(),"step": state["steps"], "step_limit": max_steps, "seconds_left": round(((max_steps or 0) - state["steps"]) / 30, 1),
                   "episode_over": state["done"], "prompt": state["prompt"] or "<global task sentence>",
                   "proprio": proprio.read(), "jaws": detector.jaw_state(), "images": save_images(tag)}
            if extra:
                out.update(extra)
            if args.show_goal_status:
                out["goal"] = goals.snapshot()
            return out

        def look(step_deg=45.0, count=8, return_to_start=True):
            views, total = [], 0.0
            for i in range(int(count)):
                r = move_base(0, 0, step_deg, max_steps=300)
                total += r["moved"]["turn_deg"]
                img = save_images(f"look_s{state['steps']}_{i}")
                views.append({"turned_deg": round(total, 1), "head": img.get("head")})
                if state["done"]:
                    break
            if return_to_start and abs(total) % 360 > 5 and not state["done"]:
                move_base(0, 0, -total, max_steps=600)
            # mosaic of head views with their bearings
            tiles = []
            for v in views:
                im = cv2.resize(cv2.imread(v["head"]), (320, 320))
                cv2.putText(im, f"{v['turned_deg']:+.0f} deg", (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                tiles.append(im)
            while len(tiles) % 4:
                tiles.append(np.zeros_like(tiles[0]))
            mosaic = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
            mp = session / "images" / f"look_s{state['steps']}_mosaic.png"
            cv2.imwrite(str(mp), mosaic)
            return {"views": views, "mosaic": str(mp), "returned_to_start": return_to_start}

        def execute(cmd):
            op = cmd.get("op")
            if cmd.get("why"):
                log("decision", step=state["steps"], op=op, why=cmd["why"], cmd=cmd)
            n = int(cmd.get("steps", args.check_every))
            if op == "continue":
                r = run(state["prompt"], n, cmd.get("until"), "continue")
                return {**checkpoint(f"{len(segments):03d}_s{state['steps']}"), "reason": r["reason"], "events": r["events"]}
            if op == "global":
                r = run(None, n, cmd.get("until"), "global")
                return {**checkpoint(f"{len(segments):03d}_s{state['steps']}"), "reason": r["reason"], "events": r["events"]}
            if op == "skill":
                if not cmd.get("prompt"):
                    raise ValueError("skill needs a prompt")
                r = run(cmd["prompt"], n, cmd.get("until"), "skill")
                return {**checkpoint(f"{len(segments):03d}_s{state['steps']}"), "reason": r["reason"], "events": r["events"]}
            if op == "base":
                from omnigibson.utils import transform_utils as T3
                p0, q0 = evaluator.robot.get_position_orientation()
                r = move_base(cmd.get("forward", 0.0), cmd.get("left", 0.0), cmd.get("turn_deg", 0.0), int(cmd.get("max_steps", 900)),
                              gentle=bool(cmd.get("gentle", False)))
                p1, q1 = evaluator.robot.get_position_orientation()
                yaw0 = float(T3.quat2euler(q0)[2]); yaw1 = float(T3.quat2euler(q1)[2])
                d = (p1 - p0)[:2]
                true_fwd = float(math.cos(yaw0) * d[0] + math.sin(yaw0) * d[1])
                true_left = float(-math.sin(yaw0) * d[0] + math.cos(yaw0) * d[1])
                true_turn = math.degrees(math.atan2(math.sin(yaw1 - yaw0), math.cos(yaw1 - yaw0)))
                # privileged ground truth: written to the trace only, for checking odometry
                log("base", step=state["steps"], **r, true_moved={"forward": round(true_fwd, 3), "left": round(true_left, 3),
                                                                 "turn_deg": round(true_turn, 1)})
                return checkpoint(f"base_s{state['steps']}", {"base": r})
            if op == "hand":
                r = move_hand(cmd.get("arm", "right"), float(cmd.get("forward", 0)), float(cmd.get("left", 0)),
                              float(cmd.get("up", 0)), float(cmd.get("yaw_deg", 0)), float(cmd.get("pitch_deg", 0)),
                              int(cmd.get("max_steps", 120)), use_trunk=bool(cmd.get("trunk", True)), quat=cmd.get("quat"))
                log("hand", step=state["steps"], **r)
                return checkpoint(f"hand_s{state['steps']}", {"hand": r})
            if op == "objinfo":
                # privileged, dev/bench scoring only: AABB centres of task objects in world frame + goal status
                from omnigibson.object_states import AABB
                out = {}
                for inst, obj in evaluator.env.task.object_scope.items():
                    if obj is None or not hasattr(obj, "states") or AABB not in obj.states or "agent" in inst or "floor" in inst:
                        continue
                    lo, hi = obj.states[AABB].get_value()
                    out[inst] = {"center": [round(float(x), 3) for x in ((lo + hi) / 2).tolist()],
                                 "min_z": round(float(lo[2]), 3)}
                log("objinfo", step=state["steps"], objects=out)
                return {"ok": True, "step": state["steps"], "objects": out, "goal": goals.snapshot()}
            if op == "fingers":
                # robot-geometry query (URDF-equivalent): finger link origins relative to the eef, in the base frame
                bp, bq = robot.get_position_orientation()
                out = {}
                for a in ("left", "right"):
                    e, _ = eef_rel(a)
                    pts = []
                    for link in robot.finger_links[a]:
                        lp, _ = link.get_position_orientation()
                        rel, _ = T.relative_pose_transform(lp, th.tensor([0, 0, 0, 1.0]), bp, bq)
                        pts.append([round(float(x), 3) for x in rel.tolist()])
                    mid = np.mean(np.array(pts), axis=0)
                    out[a] = {"eef": [round(float(x), 3) for x in e.tolist()], "finger_links": pts,
                              "finger_mid_minus_eef": [round(float(x), 3) for x in (mid - e.numpy()).tolist()]}
                return {"ok": True, **out}
            if op == "point":
                p, z = pixel_to_base(cmd["cam"], cmd["u"], cmd["v"])
                cur = {a: [round(float(x), 3) for x in eef_rel(a)[0].tolist()] for a in ("left", "right")}
                # privileged dev check, trace only: nearest task object's true AABB centre in the base frame
                try:
                    from omnigibson.object_states import AABB
                    bp, bq = robot.get_position_orientation()
                    best = None
                    for inst, obj in evaluator.env.task.object_scope.items():
                        if obj is None or not hasattr(obj, "states") or AABB not in obj.states or "agent" in inst or "floor" in inst:
                            continue
                        lo, hi = obj.states[AABB].get_value()
                        c_rel, _ = T.relative_pose_transform((lo + hi) / 2, th.tensor([0, 0, 0, 1.0]), bp, bq)
                        dist = float(np.linalg.norm(c_rel.numpy() - p))
                        if best is None or dist < best[0]:
                            best = (dist, inst, [round(float(x), 3) for x in c_rel.tolist()], [round(float(x), 3) for x in (hi - lo).tolist()])
                    log("point_check", step=state["steps"], cam=cmd["cam"], u=cmd["u"], v=cmd["v"], point=[float(x) for x in p],
                        nearest=best)
                except Exception as e:
                    log("point_check_error", error=str(e))
                return {"ok": True, "point_base": [round(float(x), 3) for x in p], "depth_m": round(z, 3), "hands": cur,
                        "step": state["steps"]}
            if op == "reach":
                r = reach(cmd.get("arm", "right"), cmd["cam"], float(cmd["u"]), float(cmd["v"]), float(cmd.get("above", 0.10)),
                          float(cmd.get("forward_off", 0.0)), float(cmd.get("left_off", 0.0)), use_trunk=bool(cmd.get("trunk", True)))
                log("reach", step=state["steps"], **{k: v for k, v in r.items()})
                return checkpoint(f"reach_s{state['steps']}", {"hand": r})
            if op == "free_space":
                name = evaluator.robot_camera_names["head"]
                d = evaluator.obs[name + "::depth_linear"]
                d = d.numpy() if hasattr(d, "numpy") else np.asarray(d)
                H, W = d.shape[:2]
                band = d[H // 4: H * 3 // 4]
                out = {}
                for k, sl in (("left", slice(0, W // 3)), ("center", slice(W // 3, 2 * W // 3)), ("right", slice(2 * W // 3, W))):
                    v = band[:, sl]
                    v = v[np.isfinite(v) & (v > 0)]
                    out[k] = round(float(np.median(v)), 2) if v.size else None
                return {"ok": True, "step": state["steps"], "head_depth_median": out}
            if op == "container":
                return {"ok": True, "step": state["steps"], "container": detect_held_container(
                    cmd.get("holder", "right"), rmin=cmd.get("rmin"), rmax=cmd.get("rmax"), zlo=cmd.get("zlo"), zhi=cmd.get("zhi"))}
            if op == "trunk":
                r = trunk_to(cmd.get("target"))
                return checkpoint(f"trunk_s{state['steps']}", {"trunk": r})
            if op == "auto_place":
                r = (auto_place_demo if cmd.get("method", "demo") == "demo" else auto_place)(cmd.get("arm", "left"))
                log("auto_place", step=state["steps"], **r)
                r = {k: v for k, v in r.items() if not k.startswith("_dev")}
                return checkpoint(f"aplace_s{state['steps']}", {"auto_place": r})
            if op == "floor_container":
                return {"ok": True, "step": state["steps"], "container": detect_floor_container()}
            if op == "drop_in":
                c = detect_floor_container()
                if c is None:
                    return checkpoint(f"dropin_s{state['steps']}", {"drop_in": {"result": "no container seen"}})
                r = drop_into_floor_container(cmd.get("arm", "left"), c)
                log("drop_in", step=state["steps"], **r)
                r = {k: v for k, v in r.items() if not k.startswith("_dev")}
                return checkpoint(f"dropin_s{state['steps']}", {"drop_in": r})
            if op == "config":
                for k in ("max_size", "min_h", "max_h"):
                    if cmd.get(k) is not None:
                        GATE[k] = float(cmd[k])
                log("config", gate=dict(GATE))
                return {"ok": True, "step": state["steps"], "gate": dict(GATE)}
            if op == "detect":
                objs = detect_floor_objects()
                for o in objs:
                    o["graspable"] = graspable(o)
                tilt = floor_tilt_deg()
                _, bq_ = robot.get_position_orientation()     # privileged, trace only: true lean for calibration
                zb = T.quat2mat(bq_)[:, 2]
                true_tilt = round(float(np.degrees(np.arccos(float(zb[2])))), 1)
                log("detect", step=state["steps"], objects=objs, tilt_deg=tilt, true_tilt_deg=true_tilt)
                return {"ok": True, "step": state["steps"], "objects": objs, "tilt_deg": tilt}
            if op == "auto_grasp":
                arm_ = cmd.get("arm", "left")
                r = auto_grasp(arm_, cmd.get("target"), lift=float(cmd.get("lift", 0.2)))
                if r.get("result") == "miss" and cmd.get("retry", True) and not state["done"]:
                    t0 = r.get("target", {}).get("center", [0, 0, 0])
                    near = [o for o in detect_floor_objects()
                            if np.hypot(o["center"][0] - t0[0], o["center"][1] - t0[1]) < 0.15 and graspable(o)]
                    if near:
                        r2 = auto_grasp(arm_, max(near, key=lambda o: o["n"]), lift=float(cmd.get("lift", 0.2)))
                        r2["first_attempt"] = r
                        r = r2
                log("auto_grasp", step=state["steps"], **r)
                return checkpoint(f"agrasp_s{state['steps']}", {"auto_grasp": r})
            if op == "save":
                return save_snapshot(cmd.get("name", f"s{state['steps']}"))
            if op == "load":
                r = load_snapshot(cmd["name"])
                log("load", step=state["steps"], name=cmd["name"])
                return checkpoint(f"load_s{state['steps']}", {"load": r})
            if op == "grip":
                r = grip(cmd.get("arm", "right"), bool(cmd.get("close", True)), int(cmd.get("steps", 45)))
                log("grip", step=state["steps"], **r)
                return checkpoint(f"grip_s{state['steps']}", {"grip": r})
            if op == "look":
                r = look(cmd.get("step_deg", 45.0), cmd.get("count", 8), cmd.get("return", True))
                log("look", step=state["steps"], mosaic=r["mosaic"])
                return checkpoint(f"look_s{state['steps']}", {"look": r})
            if op == "run":
                return run(cmd.get("prompt"), cmd.get("steps", 300), cmd.get("until"), cmd.get("label", ""))
            if op == "observe":
                return {"step": state["steps"], "images": save_images(f"obs_s{state['steps']}"), "proprio": proprio.read()}
            if op == "status":
                out = {"step": state["steps"], "step_limit": max_steps, "prompt": state["prompt"],
                       "proprio": proprio.read(), "episode_over": state["done"]}
                if args.show_goal_status:
                    out["goal"] = goals.snapshot()
                return out
            if op == "end":
                if cmd.get("finish", "run_out") == "run_out" and not state["done"]:
                    return run(state["prompt"], 10 ** 7, (), "run_out")
                return {"step": state["steps"], "ended": True}
            raise ValueError(f"unknown op {op!r}")

        (session / "READY").write_text(json.dumps({"step": 0, "instance_id": instance_id, "step_limit": max_steps}))
        log("start", **header, step_limit=max_steps, goal=goals.snapshot())
        save_images("000_start")
        print("READY", session, "instance", instance_id, "limit", max_steps, flush=True)
        try:
            if plan is not None:
                for i, seg in enumerate(plan.get("segments", [])):
                    if state["done"]:
                        break
                    rec = run(seg.get("prompt"), seg.get("steps", 300), seg.get("until"), seg.get("label", f"plan_{i}"))
                    commands.append({"index": i, "cmd": seg, "out": {k: v for k, v in rec.items() if k != "images"}})
                tail = plan.get("tail", "task")
                if not state["done"] and tail != "stop":
                    run(None if tail == "task" else state["prompt"], 10 ** 7, (), f"tail_{tail}")
            else:
                index = 0
                while True:
                    path = session / "cmd" / f"{index:04d}.json"
                    if not path.exists():
                        time.sleep(0.2)
                        continue
                    time.sleep(0.05)
                    cmd = json.loads(path.read_text())
                    try:
                        out = {"ok": True, **execute(cmd)}
                    except Exception:
                        out = {"ok": False, "error": traceback.format_exc()[-3000:], "step": state["steps"]}
                    (session / "out" / f"{index:04d}.json").write_text(json.dumps(out, indent=1, default=str))
                    commands.append({"index": index, "cmd": cmd, "out": {k: v for k, v in out.items() if k != "images"}})
                    index += 1
                    if cmd.get("op") == "end" or state["done"]:
                        break
        finally:
            metrics = {}
            for metric in evaluator.metrics:
                metrics.update(metric.aggregate(evaluator.env))
            success = bool(evaluator.env.task.success)
            final_goal = goals.snapshot()
            result = {"task": args.task, "instance_id": instance_id, "rollout_id": 0, "seed": args.seed,
                      "mode": args.mode, "steps": state["steps"], "success": success, **metrics,
                      "harness": {"ended_by": ("episode" if state["done"] else "planner"),
                                  "terminated": state["terminated"], "truncated": state["truncated"],
                                  "step_limit": max_steps, "segments": segments, "commands": commands,
                                  "goal_final": final_goal, "plan": plan}}
            text = json.dumps(result, indent=2, default=float)
            (session / "result.json").write_text(text)
            (session / "json" / f"{args.task}_{instance_id}_0.json").write_text(text)
            log("end", step=state["steps"], success=success, q=metrics.get("q_score"), goal=final_goal)
            try:
                evaluator.finish_rollout(success=success, metadata={"task": args.task, "instance_id": instance_id})
            except Exception:
                pass
            if not args.no_video:
                evaluator.stop_recording()
            (session / "DONE").write_text(json.dumps({"step": state["steps"], "success": success,
                                                      "q": metrics.get("q_score")}))
            print("RESULT", json.dumps({"steps": state["steps"], "success": success, "q": metrics.get("q_score"),
                                        "partial_q_tracker": final_goal["partial_q"]}), flush=True)


if __name__ == "__main__":
    main()
