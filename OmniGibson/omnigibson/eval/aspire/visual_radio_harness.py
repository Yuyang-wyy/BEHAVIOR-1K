"""Camera/proprioception-only radio adapter. No demonstration or object-state access."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch as th
from PIL import Image
from scipy.spatial.transform import Rotation

from omnigibson.eval.aspire.visual_perception import (
    ContactGraspNetClient, Sam3Client, contact_grasps_to_eef, mask_to_world_points, observed_box,
)


class EpisodeFinished(RuntimeError):
    pass


class VisualRadioHarness:
    def __init__(self, evaluator, output_dir, sam3_url="http://127.0.0.1:8114"):
        self.evaluator = evaluator
        self.robot = evaluator.robot
        self.joint_targets = self.robot.get_joint_positions().detach().cpu().numpy().copy()
        self.output_dir = Path(output_dir)
        self.sam3 = Sam3Client(sam3_url)
        self.graspnet = ContactGraspNetClient()
        self.motion_generators = {}
        self.steps = 0
        self.terminated = False
        self.truncated = False
        self.gripper_closed = {"left": False, "right": False}
        self.last_grasp = None
        self.grasp_arm = 1
        self.perception_index = 0

    def functions(self):
        names = ("get_env_observation", "get_observation", "save_current_observation", "get_robot_position",
                 "segment_sam3_text_prompt", "get_object_pose", "find_object_base_rotate",
                 "find_object_torso_rotate", "get_navigation_pose", "navigate_to_pose", "rotate_base",
                 "sample_grasp_pose", "sample_grasp_pose_from_points", "sample_contact_grasp_pose", "execute_grasp", "grasp_object",
                 "check_object_in_hand", "open_gripper", "close_gripper",
                 "get_current_eef_pose", "get_current_joint_positions", "solve_ik", "move_hand",
                 "move_to_joints", "lift_arm", "press_at_pixel", "mask_to_world_points")
        return {name: getattr(self, name) for name in names}

    def _trace(self, event, **fields):
        with (self.output_dir / "trace.jsonl").open("a") as stream:
            stream.write(json.dumps({"event": event, "step": self.steps, **fields}, default=lambda v: np.asarray(v).tolist()) + "\n")

    def _step(self, action):
        if self.terminated or self.truncated:
            raise EpisodeFinished("Episode already ended")
        obs, _, self.terminated, self.truncated, _ = self.evaluator.env.step(action, n_render_iterations=1, skip_obs=False)
        self.evaluator.obs = self.evaluator._preprocess_obs(obs)
        self.steps += 1
        if self.evaluator._video_path is not None:
            self.evaluator._write_video()
        if self.terminated or self.truncated:
            raise EpisodeFinished("Episode ended during motor execution")

    def _action(self, joints=None):
        if joints is not None:
            self.joint_targets = np.asarray(joints, dtype=float).copy()
        joints = th.as_tensor(self.joint_targets, dtype=th.float32)
        action = th.zeros(self.robot.action_dim)
        action[self.robot.trunk_action_idx] = joints[self.robot.trunk_control_idx]
        for arm in self.robot.arm_names:
            action[self.robot.arm_action_idx[arm]] = joints[self.robot.arm_control_idx[arm]]
            action[self.robot.gripper_action_idx[arm]] = -1.0 if self.gripper_closed[arm] else 1.0
        return action

    def get_env_observation(self, camera="head"):
        if camera not in self.evaluator.robot_camera_names:
            raise ValueError(f"Unknown camera role {camera!r}")
        name = self.evaluator.robot_camera_names[camera]
        rgb = self.evaluator.obs[f"{name}::rgb"].detach().cpu().numpy()[..., :3]
        depth = self.evaluator.obs[f"{name}::depth_linear"].detach().cpu().numpy().squeeze()
        return rgb, depth

    def get_observation(self, camera="head"):
        from omnigibson.utils import transform_utils as transform_utils

        rgb, depth = self.get_env_observation(camera)
        name = self.evaluator.robot_camera_names[camera].split("::", 1)[1]
        sensor = self.robot.sensors[name]
        view = np.asarray(sensor.camera_parameters["cameraViewTransform"]).reshape(4, 4)
        if np.allclose(view, 0):
            position, quat = sensor.get_position_orientation()
            world_from_camera = transform_utils.pose2mat((position, quat)).detach().cpu().numpy()
        else:
            world_from_camera = np.linalg.inv(view.T)
        return {"rgb": rgb, "depth": depth, "intrinsics": np.asarray(sensor.intrinsic_matrix),
                "world_from_camera": world_from_camera, "joints": self.get_current_joint_positions()}

    def save_current_observation(self, name, camera="head"):
        if not isinstance(name, str) or not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name):
            raise ValueError("Observation names must be simple identifiers")
        observation = self.get_observation(camera)
        np.savez_compressed(self.output_dir / f"{name}.npz", **observation)
        Image.fromarray(observation["rgb"]).save(self.output_dir / f"{name}.png")

    def segment_sam3_text_prompt(self, rgb, text_prompt):
        self.perception_index += 1
        stem = f"perception_{self.perception_index:03d}"
        Image.fromarray(np.asarray(rgb)).save(self.output_dir / f"{stem}_input.png")
        results = self.sam3.segment(rgb, text_prompt)
        self._trace("sam3", prompt=text_prompt, scores=[r["score"] for r in results], artifact=stem)
        if results:
            overlay = np.asarray(rgb).copy()
            mask = results[0]["mask"]
            overlay[mask] = (overlay[mask].astype(float) * 0.5 + np.array([0, 255, 100]) * 0.5).astype(np.uint8)
            Image.fromarray(overlay).save(self.output_dir / f"{stem}_mask.png")
            np.savez_compressed(self.output_dir / f"{stem}.npz", mask=mask, box=results[0]["box"], score=results[0]["score"])
        return results

    @staticmethod
    def mask_to_world_points(mask, depth, intrinsics, world_from_camera):
        return mask_to_world_points(mask, depth, intrinsics, world_from_camera)

    def get_object_pose(self, object_name, return_bbox_extent=False, camera="head"):
        observation = self.get_observation(camera)
        results = self.segment_sam3_text_prompt(observation["rgb"], object_name)
        if not results or results[0]["score"] < 0.1:
            raise ValueError(f"No confident visual detection for {object_name!r}")
        points = mask_to_world_points(results[0]["mask"], observation["depth"], observation["intrinsics"], observation["world_from_camera"])
        position, rotation, extent, points = observed_box(points)
        quat = Rotation.from_matrix(rotation).as_quat()[[3, 0, 1, 2]]
        self._trace("observed_pose", query=object_name, position=position, extent=extent, point_count=len(points))
        return position, quat, extent if return_bbox_extent else None, points, {"center": position, "rotation": rotation, "extent": extent}

    def get_robot_position(self):
        position, quat = self.robot.get_position_orientation()
        position, quat = position.detach().cpu().numpy(), quat.detach().cpu().numpy()
        return position, quat[[3, 0, 1, 2]], float(Rotation.from_quat(quat).as_euler("xyz")[2])

    def rotate_base(self, radians):
        if not np.isfinite(radians) or abs(radians) > 2 * math.pi:
            raise ValueError("Rotation must be finite and at most one revolution")
        _, _, yaw = self.get_robot_position()
        target = yaw + radians
        for _ in range(160):
            error = math.atan2(math.sin(target - self.get_robot_position()[2]), math.cos(target - self.get_robot_position()[2]))
            if abs(error) < 0.03:
                self._step(self._action())
                return True
            action = self._action()
            action[self.robot.base_action_idx] = th.tensor([0, 0, np.clip(error * 1.5, -0.5, 0.5)])
            self._step(action)
        return False

    def find_object_base_rotate(self, object_name):
        for _ in range(50):
            rgb, _ = self.get_env_observation()
            results = self.segment_sam3_text_prompt(rgb, object_name)
            if results and results[0]["score"] >= 0.1:
                return True
            self.rotate_base(math.pi / 6)
        return False

    def find_object_torso_rotate(self, object_name):
        return self.find_object_base_rotate(object_name)

    def get_navigation_pose(self, table_points, object_points):
        obj = np.median(np.asarray(object_points), axis=0)
        base = self.get_robot_position()[0]
        direction = obj[:2] - base[:2]
        direction /= max(np.linalg.norm(direction), 1e-6)
        xy = obj[:2] - 0.65 * direction
        return np.array([*xy, math.atan2(direction[1], direction[0])])

    def navigate_to_pose(self, pose):
        pose = np.asarray(pose, dtype=float)
        if pose.shape != (3,) or not np.isfinite(pose).all():
            raise ValueError("Navigation pose must be a finite x,y,yaw vector")
        start = self.get_robot_position()[0]
        if np.linalg.norm(pose[:2] - start[:2]) > 3:
            raise ValueError("Straight-line approach is limited to three metres")
        self._trace("navigation", target=pose)
        # ponytail: short RGB-D-docked approaches only; add obstacle-aware navigation for room-scale motion.
        docked = False
        for index in range(600):
            base, _, yaw = self.get_robot_position()
            delta = pose[:2] - base[:2]
            distance = np.linalg.norm(delta)
            if index % 50 == 0:
                self._trace("navigation_feedback", position=base, yaw=yaw, distance=float(distance))
            # Hysteresis prevents small base drift from interrupting the final rotation.
            docked = distance < (0.12 if docked else 0.08)
            heading = pose[2] if docked else math.atan2(delta[1], delta[0])
            error = math.atan2(math.sin(heading - yaw), math.cos(heading - yaw))
            if docked and abs(error) < 0.05:
                self._step(self._action())
                return True
            action = self._action()
            action[self.robot.base_action_idx] = th.tensor([
                min(distance * 0.6, 0.15) if abs(error) < 0.25 and not docked else 0.0,
                0.0, np.clip(error * 1.2, -0.4, 0.4),
            ], dtype=th.float32)
            self._step(action)
        return False

    def _init_ik(self, arm=1, lock_trunk=False, lock_last_trunk=False, self_collision_check=False):
        arm_name = "right" if arm == 1 else "left"
        if lock_trunk and lock_last_trunk:
            raise ValueError("Choose either full or distal trunk locking")
        key = (arm_name + ("_fixed_trunk" if lock_trunk else "_fixed_distal_trunk" if lock_last_trunk else "")
               + ("_self_collision" if self_collision_check else ""))
        if key in self.motion_generators:
            return self.motion_generators[key]
        import yaml
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection, CuRoboMotionGenerator

        source = self.robot.curobo_path[CuRoboEmbodimentSelection.ARM]
        config = yaml.safe_load(Path(source).read_text())
        config["robot_cfg"]["kinematics"]["ee_link"] = f"{arm_name}_eef_link"
        config["robot_cfg"]["kinematics"]["link_names"] = []
        locked_names = (list(self.robot.arm_joint_names["left" if arm == 1 else "right"])
                        + (list(self.robot.trunk_joint_names) if lock_trunk else
                           [self.robot.trunk_joint_names[-1]] if lock_last_trunk else []))
        current = self.robot.get_joint_positions()
        current = current.detach().cpu().numpy() if hasattr(current, "detach") else np.asarray(current)
        indices = {name: index for index, name in enumerate(self.robot.joints)}
        lock_joints = config["robot_cfg"]["kinematics"].setdefault("lock_joints", {})
        for name in locked_names:
            lock_joints[name] = float(current[indices[name]])
        path = self.output_dir / f"robot_{key}_ik.yaml"
        path.write_text(yaml.safe_dump(config))
        generator = CuRoboMotionGenerator(
            self.robot, robot_cfg_path={CuRoboEmbodimentSelection.ARM: str(path)},
            batch_size=1, use_cuda_graph=False,
            lock_joint_names=[],
            motion_cfg_kwargs=({"self_collision_check": False}
                               if (lock_trunk or lock_last_trunk) and not self_collision_check else None),
        )
        self.motion_generators[key] = generator
        return generator

    def solve_ik(self, position, quaternion_wxyz, arm=1, lock_trunk=False, lock_last_trunk=False,
                 self_collision_check=False):
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection

        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        position = np.asarray(position, dtype=float)
        quat = np.asarray(quaternion_wxyz, dtype=float)
        if position.shape != (3,) or quat.shape != (4,) or not np.isfinite(position).all() or not np.isfinite(quat).all() or np.linalg.norm(quat) < 1e-6:
            raise ValueError("Invalid IK pose")
        quat = quat / np.linalg.norm(quat)
        if (not isinstance(lock_trunk, bool) or not isinstance(lock_last_trunk, bool)
                or not isinstance(self_collision_check, bool)):
            raise ValueError("Trunk locks must be booleans")
        generator = self._init_ik(arm, lock_trunk, lock_last_trunk, self_collision_check)
        success, paths = generator.compute_trajectories(
            th.tensor(position[None], dtype=th.float32), th.tensor(quat[[1, 2, 3, 0]][None], dtype=th.float32),
            initial_joint_pos=self.robot.get_joint_positions(), max_attempts=3, timeout=2.0,
            skip_obstacle_update=True, ik_only=True, ik_world_collision_check=False,
            emb_sel=CuRoboEmbodimentSelection.ARM,
        )
        if not bool(success[0]) or paths[0] is None:
            self._trace("ik_failed", target=position)
            return None
        path = paths[0]
        values = path.position[-1] if path.position.ndim > 1 else path.position
        target = self.robot.get_joint_positions().detach().cpu().clone()
        indices = {name: index for index, name in enumerate(self.robot.joints)}
        for name, value in zip(path.joint_names, values.detach().cpu()):
            target[indices[name]] = value
        controlled = th.cat([self.robot.trunk_control_idx,
                             *[self.robot.arm_control_idx[arm_name] for arm_name in self.robot.arm_names]])
        if bool(th.any(target[controlled] < self.robot.joint_lower_limits[controlled] - 1e-4)) or bool(
                th.any(target[controlled] > self.robot.joint_upper_limits[controlled] + 1e-4)):
            self._trace("ik_failed", target=position, reason="joint_limits")
            return None
        return target.numpy()

    def get_current_joint_positions(self):
        return self.robot.get_joint_positions().detach().cpu().numpy().copy()

    def get_current_eef_pose(self, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        position, quat = self.robot.get_eef_pose(arm="right" if arm == 1 else "left")
        return position.detach().cpu().numpy(), quat.detach().cpu().numpy()[[3, 0, 1, 2]]

    def move_to_joints(self, joints, max_joint_step=0.015):
        target = np.asarray(joints, dtype=float)
        current = self.get_current_joint_positions()
        if target.shape != current.shape or not np.isfinite(target).all() or not 0 < max_joint_step <= 0.03:
            raise ValueError("Invalid motor target or interpolation step")
        controlled = th.cat([self.robot.trunk_control_idx, *[self.robot.arm_control_idx[arm] for arm in self.robot.arm_names]])
        values = th.as_tensor(target, dtype=th.float32)[controlled]
        if bool(th.any(values < self.robot.joint_lower_limits[controlled] - 1e-4)) or bool(th.any(values > self.robot.joint_upper_limits[controlled] + 1e-4)):
            raise ValueError("Motor target exceeds robot joint limits")
        steps = int(max(1, np.ceil(np.max(np.abs(target - current)) / max_joint_step)))
        if steps > 1000:
            raise ValueError("Requested motor motion exceeds the interpolation budget")
        for index in range(1, steps + 1):
            self._step(self._action(current + (target - current) * index / steps))
        settled = False
        for index in range(120):
            self._step(self._action(target))
            error = th.as_tensor(self.get_current_joint_positions(), dtype=th.float32)[controlled] - values
            if index >= 7 and float(th.max(th.abs(error))) < 0.01:
                settled = True
                break
        self._trace("joint_tracking", settled=settled,
                    joint_names=[list(self.robot.joints)[index] for index in controlled.tolist()],
                    target=values.numpy(), actual=self.get_current_joint_positions()[controlled.numpy()])
        return settled

    def move_hand(self, target_pose, arm=1, max_joint_step=0.015, lock_trunk=False,
                  lock_last_trunk=False, self_collision_check=False):
        joints = self.solve_ik(*target_pose, arm=arm, lock_trunk=lock_trunk,
                               lock_last_trunk=lock_last_trunk,
                               self_collision_check=self_collision_check)
        if joints is None:
            return False
        self.move_to_joints(joints, max_joint_step=max_joint_step)
        position, quat = self.get_current_eef_pose(arm)
        position_error = float(np.linalg.norm(position - np.asarray(target_pose[0])))
        requested = np.asarray(target_pose[1])[[1, 2, 3, 0]]
        orientation_error = float((Rotation.from_quat(requested).inv() * Rotation.from_quat(quat[[1, 2, 3, 0]])).magnitude())
        reached = position_error < 0.025 and orientation_error < 0.25
        self._trace("motor_tracking", target=target_pose[0], position_error=position_error,
                    orientation_error=orientation_error, reached=reached, arm=arm,
                    actual_position=position, actual_quaternion_wxyz=quat)
        return reached

    def open_gripper(self, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        self.gripper_closed["right" if arm == 1 else "left"] = False
        if arm == self.grasp_arm:
            self.last_grasp = None
        for _ in range(25):
            self._step(self._action())

    def close_gripper(self, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        self.gripper_closed["right" if arm == 1 else "left"] = True
        for _ in range(35):
            self._step(self._action())

    def sample_grasp_pose(self, object_name):
        obs = self.get_observation()
        detections = self.segment_sam3_text_prompt(obs["rgb"], object_name)
        if not detections or detections[0]["score"] < .1:
            raise ValueError("No confident target mask for grasp planning")
        mask = detections[0]["mask"]
        pregrasps, grasps = self.sample_contact_grasp_pose(mask)
        if grasps:
            return pregrasps, grasps
        self._trace("grasp_fallback", reason="Contact-GraspNet returned no grasps")
        points = mask_to_world_points(mask, obs["depth"], obs["intrinsics"], obs["world_from_camera"])
        return self.sample_grasp_pose_from_points(points)

    def sample_contact_grasp_pose(self, mask, camera="head", arm=1, max_candidates=8):
        if arm not in (0, 1) or not 1 <= max_candidates <= 16:
            raise ValueError("Invalid grasp arm or candidate budget")
        obs = self.get_observation(camera)
        grasps, scores, contacts = self.graspnet.plan(obs["depth"], obs["intrinsics"], mask)
        self.perception_index += 1
        stem = f"graspnet_{self.perception_index:03d}"
        self.save_current_observation(stem + "_input", camera)
        np.savez_compressed(self.output_dir / f"{stem}.npz", mask=mask, grasps_cv=grasps,
                            scores=scores, contacts_cv=contacts)
        selected = np.argsort(scores)[::-1][:max_candidates]
        tip = float(np.mean(list(self.robot.eef_to_fingertip_lengths["right" if arm == 1 else "left"].values())))
        pre, goal = contact_grasps_to_eef(grasps[selected], obs["world_from_camera"], tip)
        self._trace("contact_graspnet", count=len(goal), scores=scores[selected],
                    world_targets=goal[:, :3, 3], artifact=stem)
        def poses(transforms):
            return [(tf[:3, 3], Rotation.from_matrix(tf[:3, :3]).as_quat()[[3, 0, 1, 2]]) for tf in transforms]
        return poses(pre), poses(goal)

    def sample_grasp_pose_from_points(self, points, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        position, rotation, extent, points = observed_box(points)
        # ASPIRE's simple OBB/top-down candidate, using observed geometry only.
        yaw = math.atan2(rotation[1, 0], rotation[0, 0])
        pregrasps, grasps = [], []
        fingertip_length = float(np.mean(list(self.robot.eef_to_fingertip_lengths["right" if arm == 1 else "left"].values())))
        for angle in (yaw, yaw + math.pi / 2):
            quat = Rotation.from_euler("xyz", [math.pi, 0, angle]).as_quat()[[3, 0, 1, 2]]
            grasp = position.copy()
            grasp[2] = np.percentile(points[:, 2], 80) + fingertip_length - 0.025
            pregrasps.append((grasp + np.array([0, 0, 0.15]), quat))
            grasps.append((grasp, quat))
        arm_name = "right" if arm == 1 else "left"
        eef_position, eef_quat = self.get_current_eef_pose(arm)
        finger_origins = np.stack([link.get_position_orientation()[0].detach().cpu().numpy()
                                   for link in self.robot.finger_links[arm_name]])
        finger_local = (finger_origins - eef_position) @ Rotation.from_quat(eef_quat[[1, 2, 3, 0]]).as_matrix()
        self._trace("grasp_candidates", count=len(grasps), position=position, extent=extent, arm=arm,
                    calibrated_tip_offset=fingertip_length, own_finger_origins_in_eef=finger_local)
        return pregrasps, grasps

    def execute_grasp(self, pregrasp_pose, grasp_pose, arm=1, lift=0.08):
        """Execute motor commands only; caller must verify grasp from observations."""
        if arm not in (0, 1) or not 0 < lift <= 0.2:
            raise ValueError("Invalid grasp arm or lift distance")
        self.open_gripper(arm)
        if not self.move_hand(pregrasp_pose, arm) or not self.move_hand(grasp_pose, arm, max_joint_step=0.005):
            return False
        self.close_gripper(arm)
        return self.lift_arm(arm, distance=lift)

    def grasp_object(self, pregrasp_pose, grasp_pose, object_name, arm=1):
        before = self.get_object_pose(object_name)[0]
        completed = self.execute_grasp(pregrasp_pose, grasp_pose, arm)
        self.last_grasp = (object_name, before)
        self.grasp_arm = arm
        return completed

    def lift_arm(self, arm=1, distance=0.08, lock_trunk=False, lock_last_trunk=False):
        if not 0 < distance <= 0.2:
            raise ValueError("Lift distance must be in (0, 0.2]")
        position, quat = self.get_current_eef_pose(arm)
        return self.move_hand((position + np.array([0, 0, distance]), quat), arm,
                              max_joint_step=0.005, lock_trunk=lock_trunk,
                              lock_last_trunk=lock_last_trunk)

    def check_object_in_hand(self, arm=1):
        if arm != getattr(self, "grasp_arm", 1) or self.last_grasp is None:
            return False
        query, before = self.last_grasp
        try:
            after = self.get_object_pose(query)[0]
        except ValueError:
            return False
        eef, _ = self.get_current_eef_pose(arm)
        lifted = float(after[2] - before[2])
        near_hand = float(np.linalg.norm(after - eef))
        held = lifted > 0.035 and near_hand < 0.25
        self._trace("visual_grasp_check", lifted=lifted, hand_distance=near_hand, held=held)
        return held

    def press_at_pixel(self, x, y, camera="head", travel=0.015, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        arm_name = "right" if arm == 1 else "left"
        if self.last_grasp is not None and arm == self.grasp_arm and self.gripper_closed[arm_name]:
            raise ValueError("Use the free arm to press while holding the radio")
        if not 0 < travel <= 0.03:
            raise ValueError("Press travel must be in (0, 0.03]")
        observation = self.get_observation(camera)
        height, width = observation["depth"].shape
        x, y = int(x), int(y)
        if not 0 <= x < width or not 0 <= y < height:
            raise ValueError("Button pixel is outside the image")
        mask = np.zeros((height, width), dtype=bool)
        mask[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = True
        points = mask_to_world_points(mask, observation["depth"], observation["intrinsics"], observation["world_from_camera"])
        if len(points) < 3:
            raise ValueError("No valid depth at button pixel")
        point = np.median(points, axis=0)
        direction = point - observation["world_from_camera"][:3, 3]
        direction /= np.linalg.norm(direction)
        # Depth sees the camera-facing surface of the raised red control; use a
        # small RGB-D surface-to-center offset for the overlap press.
        point = point + direction * 0.08
        holder_tracking = None
        holder_arm = 1 - arm
        holder_name = "right" if holder_arm == 1 else "left"
        if self.gripper_closed[holder_name]:
            try:
                holder_position, holder_quat = self.get_current_eef_pose(holder_arm)
                holder_rotation = Rotation.from_quat(holder_quat[[1, 2, 3, 0]])
                holder_world_pose = (holder_position.copy(), holder_quat.copy())
                holder_tracking = (
                    holder_rotation.inv().apply(point - holder_position),
                    holder_rotation.inv().apply(direction),
                    holder_rotation,
                )
            except (AttributeError, KeyError, TypeError):
                pass
        reference = np.array([0, 0, 1]) if abs(direction[2]) < 0.9 else np.array([0, 1, 0])
        axis_x = np.cross(reference, direction)
        axis_x /= np.linalg.norm(axis_x)
        axis_y = np.cross(direction, axis_x)
        base_rotation = np.column_stack([axis_x, axis_y, direction])
        fingertip_length = float(np.mean(list(self.robot.eef_to_fingertip_lengths[arm_name].values())))
        current_rotation = None
        try:
            eef_position, eef_quat = self.get_current_eef_pose(arm)
            finger_origins = np.stack([
                link.get_position_orientation()[0].detach().cpu().numpy()
                for link in self.robot.finger_links[arm_name]
            ])
            eef_rotation = Rotation.from_quat(eef_quat[[1, 2, 3, 0]])
            current_rotation = eef_rotation.as_matrix()
            finger_offset_local = eef_rotation.inv().apply(finger_origins.mean(axis=0) - eef_position)
        except (AttributeError, KeyError, TypeError):
            finger_offset_local = None
        candidates = []
        initial_lock = ({"lock_last_trunk": True}
                        if holder_tracking is not None else {"lock_trunk": True})
        current_joints = self.get_current_joint_positions()
        rotations = [
            (wrist_roll, base_rotation @ Rotation.from_euler("z", wrist_roll).as_matrix())
            for wrist_roll in (math.pi / 2, 0.0, -math.pi / 2, math.pi / 4,
                               -math.pi / 4, 3 * math.pi / 4,
                               math.pi, -3 * math.pi / 4)
        ]
        if current_rotation is not None and arm == 1:
            rotations.insert(0, (None, current_rotation))
        for wrist_roll, rotation in rotations:
            quat = Rotation.from_matrix(rotation).as_quat()[[3, 0, 1, 2]]
            offset = (Rotation.from_quat(quat[[1, 2, 3, 0]]).apply(finger_offset_local)
                      if finger_offset_local is not None
                      else rotation @ np.array([0, 0, fingertip_length]))
            approach_distance = 0.14 if holder_tracking is not None else 0.06
            approach = point - direction * approach_distance - offset
            target_joints = self.solve_ik(approach, quat, arm=arm, **initial_lock)
            if target_joints is not None:
                joint_delta = np.abs(target_joints - current_joints)
                candidates.append((float(joint_delta.max()), float(np.linalg.norm(joint_delta)),
                                   quat, offset, wrist_roll))
                break
        selected = candidates[0] if candidates else None
        if selected is None:
            self._trace("visual_press_ik_failed", pixel=[x, y], point=point, direction=direction)
            return False
        max_joint_delta, joint_delta_norm, quat, offset, wrist_roll = selected
        self._trace("visual_press", pixel=[x, y], point=point, direction=direction,
                    wrist_roll=wrist_roll, holder_tracking=holder_tracking is not None,
                    max_joint_delta=max_joint_delta, joint_delta_norm=joint_delta_norm)
        self.close_gripper(arm)
        approach_pose = (point - direction * 0.06 - offset, quat)
        if not self.move_hand(approach_pose, arm, max_joint_step=0.01, **initial_lock):
            return False
        if holder_tracking is not None:
            if not self.move_hand(holder_world_pose, holder_arm, max_joint_step=0.01,
                                  lock_trunk=True):
                self._trace("visual_press_holder_restore_partial", pixel=[x, y])
        final_lock = initial_lock
        if holder_tracking is not None:
            point_in_holder, direction_in_holder, initial_holder_rotation = holder_tracking
            press_rotation_in_holder = (initial_holder_rotation.inv()
                                        * Rotation.from_quat(quat[[1, 2, 3, 0]]))
            fixed_trunk_reached = False
            for correction in range(3):
                holder_position, holder_quat = self.get_current_eef_pose(holder_arm)
                holder_rotation = Rotation.from_quat(holder_quat[[1, 2, 3, 0]])
                point = holder_position + holder_rotation.apply(point_in_holder)
                direction = holder_rotation.apply(direction_in_holder)
                press_rotation = holder_rotation * press_rotation_in_holder
                quat = press_rotation.as_quat()[[3, 0, 1, 2]]
                offset = (press_rotation.apply(finger_offset_local) if finger_offset_local is not None
                          else press_rotation.apply(np.array([0, 0, fingertip_length])))
                precontact_pose = (point - direction * 0.03 - offset, quat)
                final_lock = {"lock_trunk": True}
                if self.solve_ik(*precontact_pose, arm=arm, **final_lock) is not None:
                    if not self.move_hand(precontact_pose, arm, max_joint_step=0.01, **final_lock):
                        return False
                    fixed_trunk_reached = True
                    break
                self._trace("visual_press_holder_correction", pixel=[x, y], point=point,
                            direction=direction, correction=correction)
                if not self.move_hand(precontact_pose, arm, max_joint_step=0.015, **initial_lock):
                    return False
                if not self.move_hand(holder_world_pose, holder_arm, max_joint_step=0.01,
                                      lock_trunk=True):
                    self._trace("visual_press_holder_restore_partial", pixel=[x, y],
                                correction=correction)
            if not fixed_trunk_reached:
                self._trace("visual_press_ik_failed", pixel=[x, y], point=point,
                            direction=direction, phase="fixed_trunk_precontact")
                return False
        # ponytail: three poses preserve the approach/press/retract motion while
        # avoiding nine full IK settle cycles inside the episode budget.
        for distance in np.linspace(-0.03, min(0.02, travel), 3):
            target_pose = (point + direction * distance - offset, quat)
            reached = self.move_hand(target_pose, arm, max_joint_step=0.01, **final_lock)
            if not reached:
                actual_position, actual_quat = self.get_current_eef_pose(arm)
                actual_rotation = Rotation.from_quat(actual_quat[[1, 2, 3, 0]])
                requested_rotation = Rotation.from_quat(quat[[1, 2, 3, 0]])
                near = (np.linalg.norm(actual_position - target_pose[0]) < .08
                        and (requested_rotation.inv() * actual_rotation).magnitude() < .3)
                if not near:
                    return False
        if hasattr(self.robot, "finger_links"):
            finger_positions = np.stack([
                link.get_position_orientation()[0].detach().cpu().numpy()
                for link in self.robot.finger_links[arm_name]
            ])
            self._trace("visual_press_contact", min_finger_point_distance=float(
                np.min(np.linalg.norm(finger_positions - point, axis=1))))
        # BEHAVIOR toggles only after several consecutive finger-overlap steps.
        for _ in range(12):
            self._step(self._action())
        self.save_current_observation("after_press", camera)
        return True  # Motion completed; NOT a task-success assertion.
