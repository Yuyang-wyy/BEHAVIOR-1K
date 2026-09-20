"""Camera/proprioception-only radio adapter. No demonstration or object-state access."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import torch as th
from PIL import Image
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

from omnigibson.eval.aspire.visual_perception import (
    ContactGraspNetClient, Sam3Client, contact_grasps_to_eef, mask_to_world_points, observed_box,
)
from omnigibson.utils.aspire_kinematics import FingerGeometry, PlanarOdometry


class EpisodeFinished(RuntimeError):
    pass


class VisualRadioHarness:
    def __init__(self, evaluator, output_dir, sam3_url="http://127.0.0.1:8114"):
        self.evaluator = evaluator
        self.robot = evaluator.robot
        sizes = {"base_qvel": 3, "trunk_qpos": len(self.robot.trunk_control_idx),
                 "trunk_qvel": len(self.robot.trunk_control_idx)}
        for arm in self.robot.arm_names:
            sizes.update({f"eef_{arm}_pos": 3, f"eef_{arm}_quat": 4})
            for suffix in ("qpos", "qvel"):
                sizes[f"arm_{arm}_{suffix}"] = len(self.robot.arm_control_idx[arm])
                sizes[f"gripper_{arm}_{suffix}"] = len(self.robot.gripper_control_idx[arm])
        offset = 0
        self.proprio_slices = {}
        for name in evaluator.cfg.robot.proprio_obs:
            if name not in sizes:
                raise ValueError(f"Unsupported policy proprioception field: {name}")
            self.proprio_slices[name] = slice(offset, offset + sizes[name])
            offset += sizes[name]
        self.odometry = PlanarOdometry()
        self.finger_geometry = FingerGeometry(self.robot.urdf_path)
        self.joint_targets = self.get_current_joint_positions()
        self.output_dir = Path(output_dir)
        self.sam3 = Sam3Client(sam3_url)
        self.graspnet = ContactGraspNetClient()
        self.motion_generators = {}
        self.motion_generator_locks = {}
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
                 "get_current_eef_pose", "get_current_finger_center", "get_current_joint_positions", "solve_ik", "move_hand",
                 "move_to_joints", "move_to_posture", "lift_arm", "press_at_pixel", "mask_to_world_points")
        return {name: getattr(self, name) for name in names}

    def _trace(self, event, **fields):
        with (self.output_dir / "trace.jsonl").open("a") as stream:
            stream.write(json.dumps({"event": event, "step": self.steps, **fields}, default=lambda v: np.asarray(v).tolist()) + "\n")

    def _step(self, action):
        if self.terminated or self.truncated:
            raise EpisodeFinished("Episode already ended")
        previous_velocity = self._proprio("base_qvel")
        obs, reward, self.terminated, self.truncated, info = self.evaluator.env.step(
            action, n_render_iterations=1, skip_obs=False
        )
        self.evaluator.obs = self.evaluator._preprocess_obs(obs)
        self.odometry.update((previous_velocity + self._proprio("base_qvel")) / 2,
                             1.0 / self.evaluator.env.env_config["action_frequency"])
        for metric in self.evaluator.metrics:
            metric.step(self.evaluator.env, action, self.evaluator.obs, reward,
                        self.terminated, self.truncated, info)
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
        rgb, depth = self.get_env_observation(camera)
        name = self.evaluator.robot_camera_names[camera].split("::", 1)[1]
        sensor = self.robot.sensors[name]
        camera_index = list(self.evaluator.robot_camera_names).index(camera)
        relative = self.evaluator.obs[f"{self.robot.name}::cam_rel_poses"].detach().cpu().numpy()
        relative = relative.reshape(-1, 7)[camera_index]
        world_from_camera = self.odometry.odom_from_base @ self._pose_matrix(relative[:3], relative[3:])
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
        pose = self.odometry.odom_from_base
        quat = Rotation.from_matrix(pose[:3, :3]).as_quat()
        return pose[:3, 3], quat[[3, 0, 1, 2]], math.atan2(pose[1, 0], pose[0, 0])

    @staticmethod
    def _pose_matrix(position, quat_xyzw):
        pose = np.eye(4)
        pose[:3, :3] = Rotation.from_quat(np.asarray(quat_xyzw)).as_matrix()
        pose[:3, 3] = position
        return pose

    def _proprio(self, name):
        values = self.evaluator.obs[f"{self.robot.name}::proprio"].detach().cpu().numpy()
        return values[self.proprio_slices[name]].copy()

    def rotate_base(self, radians):
        if not np.isfinite(radians) or abs(radians) > 2 * math.pi:
            raise ValueError("Rotation must be finite and at most one revolution")
        # Use only commanded body velocity for visual search. Closing the loop
        # against simulator yaw would reintroduce a forbidden global pose input.
        steps = max(1, int(round(abs(radians) / 0.75 *
                                 self.evaluator.env.env_config["action_frequency"])))
        for _ in range(steps):
            action = self._action()
            action[self.robot.base_action_idx] = th.tensor(
                [0, 0, np.sign(radians) * 0.75], dtype=th.float32
            )
            self._step(action)
        self._step(self._action())
        return True

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
        table_xy = np.asarray(table_points, dtype=float)[:, :2]
        object_xy = np.median(np.asarray(object_points, dtype=float), axis=0)[:2]
        if len(table_xy) < 3 or not np.isfinite(table_xy).all() or not np.isfinite(object_xy).all():
            raise ValueError("Navigation requires finite table and object point clouds")
        polygon = table_xy[ConvexHull(table_xy).vertices]
        table_center = polygon.mean(axis=0)
        base_xy = self.get_robot_position()[0][:2]
        candidates = []
        for index, start in enumerate(polygon):
            end = polygon[(index + 1) % len(polygon)]
            edge = end - start
            point = start + np.clip(np.dot(object_xy - start, edge) / (np.dot(edge, edge) + 1e-8), 0, 1) * edge
            edge /= np.linalg.norm(edge) + 1e-8
            normal = np.array([-edge[1], edge[0]])
            outward = normal if np.dot(normal, table_center - point) < 0 else -normal
            target = point + .40 * outward
            object_distance = float(np.linalg.norm(target - object_xy))
            candidates.append((object_distance, float(np.linalg.norm(target - base_xy)), target))
        # The 90th percentile training grasp distance is .929 m. Preserve the
        # table clearance instead of moving an unreachable dock through it.
        reachable = [candidate for candidate in candidates if candidate[0] <= .93]
        _, _, target = min(reachable, key=lambda candidate: candidate[1]) if reachable else min(
            candidates, key=lambda candidate: candidate[:2])
        self._trace("navigation_geometry", target=target, object_center=object_xy,
                    object_distance=float(np.linalg.norm(target - object_xy)))
        return np.array([*target, math.atan2(object_xy[1] - target[1], object_xy[0] - target[0])])

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
        for index in range(800):
            base, _, yaw = self.get_robot_position()
            delta = pose[:2] - base[:2]
            distance = np.linalg.norm(delta)
            if index % 50 == 0:
                self._trace("navigation_feedback", position=base, yaw=yaw, distance=float(distance))
            # Hysteresis prevents small base drift from interrupting the final rotation.
            docked = distance < (0.14 if docked else 0.11)
            heading = pose[2] if docked else math.atan2(delta[1], delta[0])
            error = math.atan2(math.sin(heading - yaw), math.cos(heading - yaw))
            if docked and abs(error) < 0.05:
                self._step(self._action())
                return True
            action = self._action()
            action[self.robot.base_action_idx] = th.tensor([
                min(distance * 0.8, 0.25) if abs(error) < 0.25 and not docked else 0.0,
                0.0, np.clip(error * 1.5, -0.6, 0.6),
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
            # CuRobo refreshes locked-joint transforms from initial_joint_pos
            # on every solve; encoder drift does not require rebuilding it.
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
        current = self.get_current_joint_positions()
        indices = {name: index for index, name in enumerate(self.robot.joints)}
        lock_joints = config["robot_cfg"]["kinematics"].setdefault("lock_joints", {})
        for name in lock_joints:
            if name.startswith("base_footprint_"):
                lock_joints[name] = 0.0
        captured_locks = {}
        for name in locked_names:
            captured_locks[name] = lock_joints[name] = float(current[indices[name]])
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
        if not hasattr(self, "motion_generator_locks"):
            self.motion_generator_locks = {}
        self.motion_generator_locks[key] = captured_locks
        return generator

    def solve_ik(self, position, quaternion_wxyz, arm=1, lock_trunk=False, lock_last_trunk=False,
                 self_collision_check=False, trajectory=False):
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection

        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        arm_name = "right" if arm == 1 else "left"
        position = np.asarray(position, dtype=float)
        quat = np.asarray(quaternion_wxyz, dtype=float)
        if position.shape != (3,) or quat.shape != (4,) or not np.isfinite(position).all() or not np.isfinite(quat).all() or np.linalg.norm(quat) < 1e-6:
            raise ValueError("Invalid IK pose")
        quat = quat / np.linalg.norm(quat)
        if (not isinstance(lock_trunk, bool) or not isinstance(lock_last_trunk, bool)
                or not isinstance(self_collision_check, bool)):
            raise ValueError("Trunk locks must be booleans")
        generator = self._init_ik(arm, lock_trunk, lock_last_trunk, self_collision_check)
        local_pose = np.linalg.inv(self.odometry.odom_from_base) @ self._pose_matrix(
            position, quat[[1, 2, 3, 0]])
        local_quat = Rotation.from_matrix(local_pose[:3, :3]).as_quat()
        success, paths = generator.compute_trajectories(
            th.tensor(local_pose[None, :3, 3], dtype=th.float32), th.tensor(local_quat[None], dtype=th.float32),
            initial_joint_pos=th.tensor(self.get_current_joint_positions(), dtype=th.float32),
            is_local=True, max_attempts=3, timeout=2.0,
            skip_obstacle_update=True, ik_only=not trajectory, ik_world_collision_check=False,
            emb_sel=CuRoboEmbodimentSelection.ARM,
        )
        if not bool(success[0]) or paths[0] is None:
            self._trace("ik_failed", target=position)
            return None
        path = paths[0]
        path_values = path.position if path.position.ndim > 1 else path.position[None]
        values = path_values[-1]
        current = th.tensor(self.get_current_joint_positions(), dtype=th.float32)
        target = current.clone()
        indices = {name: index for index, name in enumerate(self.robot.joints)}
        for name, value in zip(path.joint_names, values.detach().cpu()):
            target[indices[name]] = value
        key = (arm_name + ("_fixed_trunk" if lock_trunk else "_fixed_distal_trunk" if lock_last_trunk else "")
               + ("_self_collision" if self_collision_check else ""))
        # Cached generators retain the lock values from construction, but the
        # other arm may have moved since then. Preserve its current joints in
        # the command instead of replaying those stale cached values.
        for name in getattr(self, "motion_generator_locks", {}).get(key, {}):
            target[indices[name]] = current[indices[name]]
        if trajectory:
            planned = []
            for waypoint in path_values.detach().cpu():
                full = current.clone()
                for name, value in zip(path.joint_names, waypoint):
                    full[indices[name]] = value
                for name in getattr(self, "motion_generator_locks", {}).get(key, {}):
                    full[indices[name]] = current[indices[name]]
                planned.append(full.numpy())
            self._planned_joint_path = np.asarray(planned)
        controlled = th.cat([self.robot.trunk_control_idx,
                             *[self.robot.arm_control_idx[arm_name] for arm_name in self.robot.arm_names]])
        if bool(th.any(target[controlled] < self.robot.joint_lower_limits[controlled] - 1e-4)) or bool(
                th.any(target[controlled] > self.robot.joint_upper_limits[controlled] + 1e-4)):
            self._trace("ik_failed", target=position, reason="joint_limits")
            return None
        return target.numpy()

    def get_current_joint_positions(self):
        # Virtual base coordinates are not encoders and must never enter policy
        # observations or local-frame IK. Motor commands only use real joints.
        joints = np.zeros(len(self.robot.joints), dtype=float)
        joints[self.robot.trunk_control_idx.detach().cpu().numpy()] = self._proprio("trunk_qpos")
        for arm in self.robot.arm_names:
            joints[self.robot.arm_control_idx[arm].detach().cpu().numpy()] = self._proprio(f"arm_{arm}_qpos")
            joints[self.robot.gripper_control_idx[arm].detach().cpu().numpy()] = self._proprio(f"gripper_{arm}_qpos")
        return joints

    def get_current_eef_pose(self, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        arm_name = "right" if arm == 1 else "left"
        pose = self.odometry.odom_from_base @ self._pose_matrix(
            self._proprio(f"eef_{arm_name}_pos"), self._proprio(f"eef_{arm_name}_quat"))
        return pose[:3, 3], Rotation.from_matrix(pose[:3, :3]).as_quat()[[3, 0, 1, 2]]

    def _finger_positions(self, arm):
        joints = dict(zip(self.robot.joints, self.get_current_joint_positions()))
        offsets = self.finger_geometry.update(joints)
        position, quat = self.get_current_eef_pose(arm)
        rotation = Rotation.from_quat(quat[[1, 2, 3, 0]])
        arm_name = "right" if arm == 1 else "left"
        return np.stack([position + rotation.apply(offsets[link.name][:3, 3])
                         for link in self.robot.finger_links[arm_name]])

    def get_current_finger_center(self, arm=1):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        return self._finger_positions(arm).mean(axis=0)

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

    def move_to_posture(self, arm, arm_joints, trunk_joints=None, max_joint_step=0.015):
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        arm_name = "right" if arm == 1 else "left"
        arm_joints = np.asarray(arm_joints, dtype=float)
        arm_indices = self.robot.arm_control_idx[arm_name].detach().cpu().numpy()
        if arm_joints.shape != arm_indices.shape or not np.isfinite(arm_joints).all():
            raise ValueError("Arm posture has the wrong shape or non-finite values")
        target = self.get_current_joint_positions()
        target[arm_indices] = arm_joints
        if trunk_joints is not None:
            trunk_joints = np.asarray(trunk_joints, dtype=float)
            trunk_indices = self.robot.trunk_control_idx.detach().cpu().numpy()
            if trunk_joints.shape != trunk_indices.shape or not np.isfinite(trunk_joints).all():
                raise ValueError("Trunk posture has the wrong shape or non-finite values")
            target[trunk_indices] = trunk_joints
        self.move_to_joints(target, max_joint_step=max_joint_step)
        # Contact loads can deflect the holding arm while the requested free
        # arm/trunk posture has settled. Verify the joints this command changes.
        actual = self.get_current_joint_positions()
        arm_ok = np.max(np.abs(actual[arm_indices] - target[arm_indices])) < .02
        trunk_ok = trunk_joints is None or np.max(np.abs(actual[trunk_indices] - target[trunk_indices])) < .08
        return bool(arm_ok and trunk_ok)

    def move_hand(self, target_pose, arm=1, max_joint_step=0.015, lock_trunk=False,
                  lock_last_trunk=False, self_collision_check=False):
        self._planned_joint_path = None
        joints = self.solve_ik(*target_pose, arm=arm, lock_trunk=lock_trunk,
                               lock_last_trunk=lock_last_trunk,
                               self_collision_check=self_collision_check,
                               trajectory=True)
        if joints is None:
            return False
        if self._planned_joint_path is not None and len(self._planned_joint_path) > 1:
            self.move_to_joint_path(self._planned_joint_path, max_joint_step=max_joint_step)
        else:
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

    def move_to_joint_path(self, path, max_joint_step=0.015):
        path = np.asarray(path, dtype=float)
        if path.ndim != 2 or path.shape[1] != len(self.robot.joints) or not np.isfinite(path).all():
            raise ValueError("Invalid joint trajectory")
        for waypoint in path:
            self._step(self._action(waypoint))
        self.move_to_joints(path[-1], max_joint_step=max_joint_step)
        return True

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
        finger_origins = self._finger_positions(arm)
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

    def press_at_pixel(self, x, y, camera="head", travel=0.015, arm=1, surface_offset=0.08,
                       direction_override=None, allow_torso=False, fixed_torso=False):
        if getattr(self, "terminated", False) or getattr(self, "truncated", False):
            return False
        if arm not in (0, 1):
            raise ValueError("Arm must be 0 (left) or 1 (right)")
        arm_name = "right" if arm == 1 else "left"
        if self.last_grasp is not None and arm == self.grasp_arm and self.gripper_closed[arm_name]:
            raise ValueError("Use the free arm to press while holding the radio")
        if not 0 < travel <= 0.03:
            raise ValueError("Press travel must be in (0, 0.03]")
        if not 0 <= surface_offset <= 0.12:
            raise ValueError("Surface offset must be in [0, 0.12]")
        if not isinstance(allow_torso, bool) or not isinstance(fixed_torso, bool):
            raise ValueError("Torso options must be booleans")
        if allow_torso and fixed_torso:
            raise ValueError("Choose either free or fixed torso motion")
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
        if direction_override is not None:
            direction = np.asarray(direction_override, dtype=float)
            if direction.shape != (3,) or not np.isfinite(direction).all() or np.linalg.norm(direction) < 1e-6:
                raise ValueError("Direction override must be a finite 3-vector")
            direction /= np.linalg.norm(direction)
        # Depth sees the camera-facing surface of the raised red control; use a
        # small RGB-D surface-to-center offset for the overlap press.
        point = point + direction * surface_offset
        holder_tracking = None
        holder_restore_target = None
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
                holder_restore_target = self.get_current_joint_positions()
            except (AttributeError, KeyError, TypeError):
                pass
        reference = np.array([0, 0, 1]) if abs(direction[2]) < 0.9 else np.array([0, 1, 0])
        axis_x = np.cross(reference, direction)
        axis_x /= np.linalg.norm(axis_x)
        axis_y = np.cross(direction, axis_x)
        base_rotation = np.column_stack([axis_x, axis_y, direction])
        fingertip_length = float(np.mean(list(self.robot.eef_to_fingertip_lengths[arm_name].values())))
        # Successful demonstrations press with a closed free gripper and one
        # fingertip, rather than centering the button in the gap between jaws.
        self.close_gripper(arm)
        current_rotation = None
        target_finger = None
        try:
            eef_position, eef_quat = self.get_current_eef_pose(arm)
            finger = self.robot.finger_links[arm_name][0]
            finger_origin = self._finger_positions(arm)[0]
            eef_rotation = Rotation.from_quat(eef_quat[[1, 2, 3, 0]])
            current_rotation = eef_rotation.as_matrix()
            finger_offset_local = eef_rotation.inv().apply(finger_origin - eef_position)
            finger_offset_local[2] = self.robot.eef_to_fingertip_lengths[arm_name][finger.name]
            target_finger = finger.name
        except (AttributeError, KeyError, TypeError):
            finger_offset_local = None
        candidates = []
        if allow_torso:
            initial_lock = {}
        elif holder_tracking is not None and not fixed_torso:
            initial_lock = {"lock_last_trunk": True}
        else:
            initial_lock = {"lock_trunk": True}
        current_joints = self.get_current_joint_positions()
        rotations = [
            (wrist_roll, base_rotation @ Rotation.from_euler("z", wrist_roll).as_matrix())
            for wrist_roll in (math.pi / 2, 0.0, -math.pi / 2, math.pi / 4,
                               -math.pi / 4, 3 * math.pi / 4,
                               math.pi, -3 * math.pi / 4)
        ]
        if current_rotation is not None:
            rotations.insert(0, (None, current_rotation))
        for wrist_roll, rotation in rotations:
            quat = Rotation.from_matrix(rotation).as_quat()[[3, 0, 1, 2]]
            offset = (Rotation.from_quat(quat[[1, 2, 3, 0]]).apply(finger_offset_local)
                      if finger_offset_local is not None
                      else rotation @ np.array([0, 0, fingertip_length]))
            approach_distance = 0.14 if holder_tracking is not None and not fixed_torso else 0.06
            approach = point - direction * approach_distance - offset
            for _ in range(6):
                target_joints = self.solve_ik(approach, quat, arm=arm, **initial_lock)
                if target_joints is not None:
                    joint_delta = np.abs(target_joints - current_joints)
                    candidates.append((float(joint_delta.max()), float(np.linalg.norm(joint_delta)),
                                       quat, offset, wrist_roll, target_joints))
            if candidates:
                break
        selected = min(candidates, key=lambda candidate: candidate[:2], default=None)
        if selected is None:
            self._trace("visual_press_ik_failed", pixel=[x, y], point=point, direction=direction)
            return False
        max_joint_delta, joint_delta_norm, quat, offset, wrist_roll, approach_joints = selected
        self._trace("visual_press", pixel=[x, y], point=point, direction=direction,
                    wrist_roll=wrist_roll, holder_tracking=holder_tracking is not None,
                    target_finger=target_finger, max_joint_delta=max_joint_delta,
                    joint_delta_norm=joint_delta_norm)
        self.move_to_joints(approach_joints, max_joint_step=0.02)
        if holder_tracking is not None:
            if holder_restore_target is not None and hasattr(self.robot, "arm_control_idx"):
                # Restoring the saved trunk and holder joints is more reliable
                # than solving a new IK target after the free approach moved it.
                restore_target = holder_restore_target.copy()
                current = self.get_current_joint_positions()
                holder_indices = self.robot.arm_control_idx[holder_name].detach().cpu().numpy()
                trunk_indices = self.robot.trunk_control_idx.detach().cpu().numpy()
                current[holder_indices] = restore_target[holder_indices]
                current[trunk_indices] = restore_target[trunk_indices]
                restored = self.move_to_joints(current, max_joint_step=0.01)
            else:
                restored = self.move_hand(holder_world_pose, holder_arm, max_joint_step=0.01,
                                          lock_trunk=True)
            if not restored:
                self._trace("visual_press_holder_restore_partial", pixel=[x, y])
                return False
        final_lock = initial_lock
        if holder_tracking is not None:
            point_in_holder, direction_in_holder, initial_holder_rotation = holder_tracking
            fixed_trunk_reached = False
            holder_position, holder_quat = self.get_current_eef_pose(holder_arm)
            holder_rotation = Rotation.from_quat(holder_quat[[1, 2, 3, 0]])
            point = holder_position + holder_rotation.apply(point_in_holder)
            direction = holder_rotation.apply(direction_in_holder)
            # Keep the held object fixed after the bounded joint restoration.
            final_lock = {"lock_trunk": True}
            holder_delta = holder_rotation * initial_holder_rotation.inv()
            contact_rolls = (wrist_roll, math.pi / 2, 0.0, -math.pi / 2, math.pi / 4,
                             -math.pi / 4, 3 * math.pi / 4, math.pi,
                             -3 * math.pi / 4)
            for contact_roll in contact_rolls:
                if contact_roll is None and current_rotation is None:
                    continue
                contact_rotation = (holder_delta * (Rotation.from_matrix(current_rotation)
                                                     if contact_roll is None else
                                                     Rotation.from_matrix(base_rotation)
                                                     * Rotation.from_euler("z", contact_roll)))
                contact_quat = contact_rotation.as_quat()[[3, 0, 1, 2]]
                contact_offset = (contact_rotation.apply(finger_offset_local)
                                  if finger_offset_local is not None
                                  else contact_rotation.apply(np.array([0, 0, fingertip_length])))
                precontact_pose = (point - direction * 0.03 - contact_offset, contact_quat)
                candidate = self.solve_ik(*precontact_pose, arm=arm, **final_lock)
                if candidate is not None:
                    if not self.move_to_joints(candidate, max_joint_step=0.01):
                        return False
                    quat, offset = contact_quat, contact_offset
                    fixed_trunk_reached = True
                    break
            if not fixed_trunk_reached:
                self._trace("visual_press_ik_failed", pixel=[x, y], point=point,
                            direction=direction, phase="fixed_trunk_precontact")
                return False
        # ponytail: three poses preserve the approach/press/retract motion while
        # avoiding nine full IK settle cycles inside the episode budget.
        for distance in np.linspace(-0.03, travel, 3):
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
            finger_positions = self._finger_positions(arm)
            self._trace("visual_press_contact", min_finger_point_distance=float(
                np.min(np.linalg.norm(finger_positions - point, axis=1))))
        # BEHAVIOR toggles only after several consecutive finger-overlap steps.
        for _ in range(12):
            self._step(self._action())
        self.save_current_observation("after_press", camera)
        return True  # Motion completed; NOT a task-success assertion.
