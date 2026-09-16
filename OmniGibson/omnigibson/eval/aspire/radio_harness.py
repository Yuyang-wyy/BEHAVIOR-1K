"""Current-BEHAVIOR adapter for ASPIRE-style radio policies.

Generated code only receives this class's public function map.  Simulator
objects and action generators remain implementation details of the adapter.
"""

from __future__ import annotations

import math
import json
from types import SimpleNamespace
from pathlib import Path
from typing import Any

import numpy as np
import torch as th


class RadioHarness:
    def __init__(self, evaluator, output_dir: str | Path, instance_id: int, demo_root: str | Path, reference_only: bool = False) -> None:
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection, CuRoboMotionGenerator
        from omnigibson.action_primitives.starter_semantic_action_primitives import (
            StarterSemanticActionPrimitives,
        )

        class RadioPrimitives(StarterSemanticActionPrimitives):
            @property
            def arm(self):
                return "right"

        self.evaluator = evaluator
        self.instance_id = instance_id
        self.demo_root = Path(demo_root).resolve()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.robot = evaluator.robot
        if reference_only:
            self.primitives = None
            return
        self.primitives = RadioPrimitives(
            evaluator.env,
            self.robot,
            enable_head_tracking=False,
            task_relevant_objects_only=True,
            skip_curobo_initilization=True,
        )
        source = Path(__file__).resolve().parents[4] / "datasets/omnigibson-robot-assets/models/r1pro/curobo/r1pro_description_curobo_arm.yaml"
        right_config = self.output_dir / "r1pro_description_curobo_right.yaml"
        right_config.write_text(
            source.read_text()
            .replace("ee_link: left_eef_link", "ee_link: right_eef_link")
            .replace("    link_names:\n    - right_eef_link", "    link_names: []")
        )
        self.primitives._motion_generator = CuRoboMotionGenerator(
            self.robot,
            robot_cfg_path={CuRoboEmbodimentSelection.ARM: str(right_config)},
            batch_size=1,
            use_cuda_graph=False,
            lock_joint_names=list(self.robot.arm_joint_names["left"]),
        )

    def functions(self) -> dict[str, Any]:
        return {
            "get_env_observation": self.get_env_observation,
            "save_current_observation": self.save_current_observation,
            "get_robot_position": self.get_robot_position,
            "find_object_base_rotate": self.find_object_base_rotate,
            "find_object_torso_rotate": self.find_object_torso_rotate,
            "reset_torso": self.reset_torso,
            "get_object_pose": self.get_object_pose,
            "get_navigation_pose": self.get_navigation_pose,
            "navigate_to_pose": self.navigate_to_pose,
            "sample_grasp_pose": self.sample_grasp_pose,
            "grasp_object": self.grasp_object,
            "check_object_in_hand": self.check_object_in_hand,
            "press_radio_button": self.press_radio_button,
            "execute_reference_skill": self.execute_reference_skill,
            "open_gripper": self.open_gripper,
            "close_gripper": self.close_gripper,
            "lift_arm": self.lift_arm,
            "get_current_eef_pose": self.get_current_eef_pose,
            "get_current_joint_positions": self.get_current_joint_positions,
            "solve_ik": self.solve_ik,
            "move_hand": self.move_hand,
        }

    def _object(self, query: str):
        query = query.lower()
        matches = [
            obj
            for name, obj in self.evaluator.env.task.object_scope.items()
            if obj is not None
            and (
                query in name.lower()
                or query in str(getattr(obj, "category", "")).lower()
            )
        ]
        if not matches and "radio" in query:
            matches = [
                obj
                for name, obj in self.evaluator.env.task.object_scope.items()
                if obj is not None and name.startswith("radio_receiver.n.")
            ]
        if not matches and "table" in query:
            matches = [
                obj
                for name, obj in self.evaluator.env.task.object_scope.items()
                if obj is not None and name.startswith("breakfast_table.n.")
            ]
        if not matches:
            raise ValueError(f"Could not resolve task object {query!r}")
        return matches[0]

    def _step(self, action) -> None:
        obs, _, terminated, truncated, _ = self.evaluator.env.step(
            action, n_render_iterations=1, skip_obs=False
        )
        self.evaluator.obs = self.evaluator._preprocess_obs(obs)
        if self.evaluator._video_path is not None or self.evaluator._side_video_path is not None:
            self.evaluator._write_video()
        if (terminated or truncated) and not bool(self.evaluator.env.task.success):
            raise RuntimeError("Episode terminated while executing ASPIRE policy")

    @staticmethod
    def _wxyz(quat_xyzw) -> np.ndarray:
        quat = np.asarray(quat_xyzw, dtype=np.float32)
        return quat[[3, 0, 1, 2]]

    @staticmethod
    def _aabb_points(obj) -> np.ndarray:
        center = np.asarray(obj.aabb_center.detach().cpu(), dtype=np.float32)
        extent = np.asarray(obj.aabb_extent.detach().cpu(), dtype=np.float32) * 0.5
        return np.asarray(
            [center + np.asarray([sx, sy, sz]) * extent for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)],
            dtype=np.float32,
        )

    def get_env_observation(self):
        obs = self.evaluator.obs
        head = self.evaluator.robot_camera_names["head"]
        rgb = obs[f"{head}::rgb"].detach().cpu().numpy()[..., :3]
        depth_key = f"{head}::depth_linear"
        depth = obs.get(depth_key)
        if depth is None:
            raise RuntimeError("ASPIRE radio policy requires RGB-D observations")
        return rgb, depth.detach().cpu().numpy()

    def save_current_observation(self, name: str) -> None:
        rgb, depth = self.get_env_observation()
        np.savez_compressed(self.output_dir / f"{name}.npz", rgb=rgb, depth=depth)

    def get_robot_position(self):
        position, quat = self.robot.get_position_orientation()
        position = position.detach().cpu().numpy()
        quat_xyzw = quat.detach().cpu().numpy()
        yaw = float(np.arctan2(2 * quat_xyzw[3] * quat_xyzw[2], 1 - 2 * quat_xyzw[2] ** 2))
        return position, self._wxyz(quat_xyzw), yaw

    def find_object_base_rotate(self, object_name: str) -> bool:
        self._object(object_name)
        return True

    def find_object_torso_rotate(self, object_name: str) -> bool:
        self._object(object_name)
        return True

    def reset_torso(self) -> None:
        target = self.robot.reset_joint_pos[self.robot.trunk_control_idx]
        current = self.robot.get_joint_positions().clone()
        current[self.robot.trunk_control_idx] = target
        for action in self.primitives._execute_motion_plan(
            th.stack([current] * 10),
        ):
            self._step(action)

    def get_object_pose(self, object_name: str, return_bbox_extent: bool = False):
        obj = self._object(object_name)
        position, quat = obj.get_position_orientation()
        position = position.detach().cpu().numpy()
        quat = self._wxyz(quat.detach().cpu().numpy())
        points = self._aabb_points(obj)
        extent = np.asarray(obj.aabb_extent.detach().cpu(), dtype=np.float32)
        return position, quat, extent if return_bbox_extent else None, points, None

    def get_navigation_pose(self, table_points, object_points):
        table = np.asarray(table_points).mean(axis=0)
        obj = np.asarray(object_points).mean(axis=0)
        direction = obj[:2] - table[:2]
        norm = float(np.linalg.norm(direction))
        if norm < 1e-6:
            direction = np.array([1.0, 0.0], dtype=np.float32)
        else:
            direction = direction / norm
        goal_xy = obj[:2] - 0.75 * direction
        return np.asarray([goal_xy[0], goal_xy[1], math.atan2(direction[1], direction[0])], dtype=np.float32)

    def navigate_to_pose(self, pose) -> bool:
        for action in self.primitives._navigate_to_pose_direct(pose):
            self._step(action)
        return True

    def sample_grasp_pose(self, object_name: str):
        from omnigibson.utils import transform_utils

        obj = self._object(object_name)
        local_pos = th.tensor([-0.03286258, 0.10400726, 0.11056720])
        local_quat = th.tensor([0.65736955, 0.65442228, -0.26297423, 0.26540786])
        radio_pose = obj.get_position_orientation()
        grasp = transform_utils.pose_transform(*radio_pose, local_pos, local_quat)
        outward = local_pos[:2] / th.linalg.vector_norm(local_pos[:2])
        pregrasp_pos = local_pos.clone()
        pregrasp_pos[:2] += outward * 0.10
        pregrasp = transform_utils.pose_transform(
            *radio_pose,
            pregrasp_pos,
            local_quat,
        )
        return (
            [(pregrasp[0].cpu().numpy(), pregrasp[1].cpu().numpy())],
            [(grasp[0].cpu().numpy(), grasp[1].cpu().numpy())],
        )

    def grasp_object(self, pregrasp_pose, grasp_pose, object_name: str, arm: int = 0) -> None:
        from omnigibson.utils import transform_utils
        from omnigibson.utils.usd_utils import RigidContactAPI

        if arm != 1:
            raise ValueError("The demonstrated radio grasp uses arm=1 (right)")
        obj = self._object(object_name)
        self.primitives._tracking_object = obj
        for action in self.primitives._execute_release():
            self._step(action)
        self._move_hand_ik(pregrasp_pose)
        self._move_hand_ik(grasp_pose)
        local_pos = th.tensor([-0.03286258, 0.10400726, 0.11056720])
        local_quat = th.tensor([0.65736955, 0.65442228, -0.26297423, 0.26540786])
        outward = local_pos[:2] / th.linalg.vector_norm(local_pos[:2])
        radio_links = set(obj.links.values())
        for distance in th.arange(0.005, 0.081, 0.005):
            contact_pos = local_pos.clone()
            contact_pos[:2] -= outward * distance
            contact_pose = transform_utils.pose_transform(*obj.get_position_orientation(), contact_pos, local_quat)
            self._move_hand_ik(contact_pose)
            if any(
                RigidContactAPI.is_in_contact(
                    scene_idx=self.evaluator.env.scene.idx,
                    query_set={finger},
                    with_set=radio_links,
                    ignore_set=None,
                    current_only=True,
                )
                for finger in self.robot.finger_links["right"]
            ):
                break
        for action in self.primitives._execute_grasp():
            self._step(action)
        for action in self.primitives._settle_robot():
            self._step(action)
        if self.check_object_in_hand(arm=1):
            position, orientation = self.robot.eef_links["right"].get_position_orientation()
            self._move_hand_ik((position + th.tensor([0.0, 0.0, 0.06]), orientation), max_joint_step=0.002)

    def _move_hand_ik(self, pose, max_joint_step: float = 0.015) -> None:
        from omnigibson.eval.collect_radio_recovery_oracle import _contact_ik_targets
        from omnigibson.eval.collect_radio_recovery_oracle import _joint_target_to_action
        from omnigibson.action_primitives.curobo import CuRoboEmbodimentSelection

        pos, quat = (th.as_tensor(value, dtype=th.float32) for value in pose)
        targets = _contact_ik_targets(
            self.primitives._motion_generator,
            self.robot,
            pos,
            th.zeros(3),
            quat,
            th.zeros(3),
            [0.0],
            SimpleNamespace(planner_max_attempts=3, planner_timeout=2.0),
            CuRoboEmbodimentSelection.ARM,
        )
        target = next((candidate for candidate in targets if candidate is not None), None)
        if target is None:
            raise RuntimeError("ASPIRE radio grasp IK failed")
        current = self.robot.get_joint_positions()
        steps = max(1, int(th.ceil(th.max(th.abs(target - current)) / max_joint_step).item()))
        trajectory = th.stack([current + (target - current) * i / steps for i in range(1, steps + 1)])
        for joint_target in trajectory:
            self._step(_joint_target_to_action(self.robot, joint_target, close_left=False, close_right=False))

    def check_object_in_hand(self, arm: int = 0) -> bool:
        if arm != 1:
            return False
        from omnigibson.utils.usd_utils import RigidContactAPI

        obj = self.primitives._tracking_object
        return obj is not None and all(
            RigidContactAPI.is_in_contact(
                scene_idx=self.evaluator.env.scene.idx,
                query_set={finger},
                with_set=set(obj.links.values()),
                ignore_set=None,
                current_only=True,
            )
            for finger in self.robot.finger_links["right"]
        )

    def press_radio_button(self, object_name: str, arm: int = 1) -> bool:
        from omnigibson.object_states import ToggledOn
        from omnigibson.utils import transform_utils

        if arm != 1:
            raise ValueError("The radio press skill currently uses arm=1 (right)")
        radio = self._object(object_name)
        toggle = radio.states[ToggledOn]
        marker, _ = toggle.visual_marker.get_position_orientation()
        orientation = self.robot.eef_links["right"].get_position_orientation()[1]
        rotation = transform_utils.quat2mat(toggle.visual_marker.get_position_orientation()[1])
        directions = [
            self.robot.get_eef_position("right") - marker,
            self.robot.get_position_orientation()[0] - marker,
            *(rotation[:, axis] * sign for axis in range(3) for sign in (-1.0, 1.0)),
        ]
        finger_center = th.stack(
            [link.get_position_orientation()[0] for link in self.robot.finger_links["right"]]
        ).mean(dim=0)
        finger_offset = transform_utils.quat_apply(
            transform_utils.quat_inverse(orientation),
            finger_center - self.robot.get_eef_position("right"),
        )
        for direction in directions:
            direction = direction / th.clamp(th.linalg.vector_norm(direction), min=1e-8)
            for offset in (0.12, 0.08, 0.035, 0.02, 0.005, -0.01):
                finger_world_offset = transform_utils.quat_apply(orientation, finger_offset)
                pose = (marker + direction * offset - finger_world_offset, orientation)
                try:
                    self._move_hand_ik(pose, max_joint_step=0.01 if offset > 0.035 else 0.003)
                except RuntimeError:
                    break
                for _ in range(8):
                    self._step(self.robot.q_to_action(self.robot.get_joint_positions()))
                    if bool(toggle.get_value()):
                        return True
        return bool(toggle.get_value())

    def execute_reference_skill(self, skill_name: str) -> bool:
        import pyarrow.parquet as pq

        metadata = None
        for path in self.demo_root.glob("meta/episodes/chunk-*/*.parquet"):
            for row in pq.read_table(path).to_pylist():
                if row["task_index"] == 0 and row["task_instance_id"] == self.instance_id:
                    metadata = row
                    break
            if metadata:
                break
        if metadata is None:
            raise ValueError(f"No radio demonstration for instance {self.instance_id}")
        annotation = json.loads((self.demo_root / metadata["annotation_path"]).read_text())
        matches = [item for item in annotation["skill_annotation"] if item["skill_description"][0] == skill_name]
        if len(matches) != 1:
            raise ValueError(f"Expected one {skill_name!r} skill, found {len(matches)}")
        start, end = matches[0]["frame_duration"]
        path = self.demo_root / "data" / f"chunk-{metadata['data/chunk_index']:03d}" / f"file-{metadata['data/file_index']:03d}.parquet"
        actions = pq.read_table(path, columns=["action"]).slice(
            metadata["dataset_from_index"] + start,
            end - start,
        )["action"].to_pylist()
        for action in actions:
            self._step(self._map_reference_action(action))
            if bool(self.evaluator.env.task.success):
                return True
        return skill_name != "press"

    def _map_reference_action(self, action):
        action = th.as_tensor(action, dtype=th.float32)
        if len(action) == self.robot.action_dim:
            return action
        mapped = th.zeros(self.robot.action_dim, dtype=th.float32)
        mapped[self.robot.base_action_idx] = action[0:3]
        mapped[self.robot.trunk_action_idx] = action[3:7]
        mapped[self.robot.arm_action_idx["left"]] = action[7:14]
        mapped[self.robot.arm_action_idx["right"]] = action[15:22]
        for arm, command in (("left", action[14]), ("right", action[22])):
            limits = self.robot.joint_upper_limits if command > 0 else self.robot.joint_lower_limits
            mapped[self.robot.gripper_action_idx[arm]] = limits[self.robot.gripper_control_idx[arm]]
        return mapped

    def open_gripper(self, arm: int = 0) -> None:
        del arm
        for action in self.primitives._execute_release():
            self._step(action)

    def close_gripper(self, arm: int = 0) -> None:
        del arm
        for action in self.primitives._execute_grasp():
            self._step(action)

    def lift_arm(self, arm: int = 0) -> None:
        del arm
        for action in self.primitives._move_hand_upward(steps=20):
            self._step(action)

    def get_current_eef_pose(self, arm: int = 0):
        position, quat = self.robot.get_robot_eef_pose(arm=arm)
        return position.detach().cpu().numpy(), quat.detach().cpu().numpy()

    def get_current_joint_positions(self):
        return self.robot.get_joint_positions().detach().cpu().numpy()

    def solve_ik(self, position, quaternion_wxyz, arm: int = 0):
        del position, quaternion_wxyz, arm
        raise NotImplementedError("Use sample_grasp_pose/grasp_object in the initial radio adapter")

    def move_hand(self, target_pose, arm: int = 0) -> bool:
        del arm
        for action in self.primitives._move_hand(
            (th.as_tensor(target_pose[0]), th.as_tensor(target_pose[1]))
        ):
            self._step(action)
        return True
