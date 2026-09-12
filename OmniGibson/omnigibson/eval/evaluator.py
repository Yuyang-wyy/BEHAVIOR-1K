import cv2
import json
import logging
import os
import sys
import time
import traceback
from signal import SIGINT, signal
from typing import Any, List, Tuple

import numpy as np
import torch as th
from av.container import Container
from av.stream import Stream
from hydra.utils import instantiate
from omegaconf import DictConfig, OmegaConf

TORCH_NUM_THREADS = None
TORCH_NUM_INTEROP_THREADS = None

if TORCH_NUM_THREADS is not None:
    th.set_num_threads(TORCH_NUM_THREADS)
if TORCH_NUM_INTEROP_THREADS is not None:
    th.set_num_interop_threads(TORCH_NUM_INTEROP_THREADS)

import omnigibson as og
import omnigibson.utils.transform_utils as T
from gello.utils.og_teleop_cfg import DISABLED_TRANSITION_RULES
from gello.utils.og_teleop_utils import (
    augment_rooms,
    get_task_relevant_room_types,
    load_available_tasks,
)
from omnigibson.envs.env_wrapper import EnvironmentWrapper
from omnigibson.eval.utils.eval_utils import (
    EVAL_TIMEOUT_MULTIPLIER,
    NUM_HIDDEN_TEST_INSTANCES,
    NUM_PUBLIC_TEST_INSTANCES,
    TASK_NAMES_TO_INDICES,
    TEST_INSTANCE_IDS,
    flatten_obs_dict,
    generate_basic_environment_config,
    get_robot_camera_names,
    seed_everything,
)
from omnigibson.eval.utils.obs_utils import create_video_writer, write_video
from omnigibson.eval.utils.score_utils import load_human_stats
from omnigibson.macros import gm
from omnigibson.metrics import AgentMetric, MetricBase, TaskMetric
from omnigibson.object_states import OnTop, ToggledOn
from omnigibson.controllers.controller_base import IsGraspingState
from omnigibson.robots import Robot
from omnigibson.utils.asset_utils import get_task_instance_path
from omnigibson.utils.bddl_utils import is_system_bddl_inst
from omnigibson.eval.utils.light_utils import LightToggleSynchronizer, set_light_control_toggles
from omnigibson.utils.python_utils import recursively_convert_to_torch
from omnigibson.utils.ui_utils import create_module_logger

LIGHT_EVAL_TASKS = {"turning_out_all_lights_before_sleep"}
EVAL_BASE_LINK_MASS = 250.0
EVAL_HEAD_HORIZONTAL_APERTURE = 40.0
DEFAULT_ROBOT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "r1pro.yaml")
EVAL_MODES = ("train", "public_test", "hidden_test")
RADIO_TRACE_EVENT_NAMES = ("docked", "grasped", "toggled", "contacted", "lifted", "placed")
RADIO_TRACE_STATE_NAMES = (
    "base_radio_xy_distance",
    "nearest_eef_radio_distance",
    "radio_height_delta",
    "table_xy_displacement",
)

gm.USE_GPU_DYNAMICS = False
gm.ENABLE_TRANSITION_RULES = True

logger = create_module_logger(module_name=__name__)
logger.setLevel(logging.INFO)


def _to_plain_dict(cfg: Any) -> dict | None:
    if cfg is None:
        return None
    if isinstance(cfg, DictConfig):
        cfg = OmegaConf.to_container(cfg, resolve=True)
    return dict(cfg)


def resolve_instance_ids(task_name: str, instance_indices: list[int], mode: str = "public_test") -> list[int]:
    assert mode in EVAL_MODES, f"Mode must be one of {EVAL_MODES}, got {mode}"
    if mode == "train":
        return [int(instance_id) for instance_id in instance_indices]

    test_instances = (
        TEST_INSTANCE_IDS[:NUM_PUBLIC_TEST_INSTANCES]
        if mode == "public_test"
        else TEST_INSTANCE_IDS[NUM_PUBLIC_TEST_INSTANCES:]
    )
    num_split_instances = NUM_PUBLIC_TEST_INSTANCES if mode == "public_test" else NUM_HIDDEN_TEST_INSTANCES
    assert set(instance_indices).issubset(
        set(range(num_split_instances))
    ), f"Instance indices must be in range({num_split_instances}) for mode {mode}"
    return [int(test_instances[i]) for i in instance_indices]


class Evaluator:
    def __init__(self, cfg: DictConfig) -> None:
        self.cfg = cfg

        self.n_trials = 0
        self.n_success_trials = 0
        self.total_time = 0
        self.robot_action = dict()
        self.robot_name = None
        self.robot_eval_config = {}
        self.robot_camera_names = {}
        self._timing_step_count = 0
        self._timing_log_every = int(os.environ.get("B1K_TIMING_LOG_EVERY", "0"))
        self._chunk_boundary_observations = bool(self.cfg.get("chunk_boundary_observations", False))
        self._training_fail_fast = bool(self.cfg.get("training_fail_fast", False))
        self._fail_fast_table_displacement = float(self.cfg.get("fail_fast_table_displacement", 0.03))
        self._fail_fast_table_patience = int(self.cfg.get("fail_fast_table_patience", 2))
        self.early_termination_reason = None
        self._fail_fast_table = None
        self._fail_fast_initial_table_xy = None
        self._fail_fast_table_streak = 0
        self._fresh_observation_steps = 0
        self._skipped_observation_steps = 0
        # Privileged traces are an explicitly train-only, offline supervision
        # artifact. None of these values are added to observations or sent to
        # the policy server.
        self._privileged_trace = None
        self._privileged_trace_step = 0
        self._training_recovery_snapshots = None

        self.env = self.load_env(env_wrapper=self.cfg.env_wrapper)
        self.robot = self.load_robot()
        self.robot_camera_names = get_robot_camera_names(self.robot.name, self.robot_eval_config)
        self._validate_robot_eval_config()
        self._apply_robot_eval_settings()
        self.policy = self.load_policy()
        self.metrics = self.load_metrics()
        self.obs = None
        self.light_synchronizer = None

        # Initialize the physics views so the first reset() (which eval.py issues before the first
        # load_task_instance) can read/restore robot joint state.
        og.sim.update_handles()

        self.env._current_episode = 0
        self._video_writer = None
        self._video_path = None
        self._side_video_writer = None
        self._side_video_path = None
        self._side_camera_pose = None
        self._video_rate = 30

    @property
    def should_sync_lights(self) -> bool:
        return self.env.task.activity_name in LIGHT_EVAL_TASKS

    def _reset_light_synchronizer(self) -> None:
        if self.should_sync_lights:
            self.light_synchronizer = LightToggleSynchronizer(self.env.scene)
            self.light_synchronizer.reset_from_current_state()
        else:
            self.light_synchronizer = None

    def _sync_lights_and_get_obs(self, obs: dict | None = None) -> dict:
        if not self.should_sync_lights:
            return obs

        if self.light_synchronizer is None:
            self._reset_light_synchronizer()
        else:
            self.light_synchronizer.sync_from_current_state()
        for _ in range(3):
            og.sim.render()
        obs, _ = self.env.get_obs()
        return obs

    def load_env(self, env_wrapper: DictConfig) -> EnvironmentWrapper:
        for rule in DISABLED_TRANSITION_RULES:
            rule.ENABLED = False

        available_tasks = load_available_tasks()
        task_name = self.cfg.task.name
        assert task_name in available_tasks, f"Got invalid task name: {task_name}"

        self.human_stats = load_human_stats(task_name)

        task_cfg = available_tasks[task_name][0]
        cfg = generate_basic_environment_config(task_name=task_name, task_cfg=task_cfg)
        if self.cfg.partial_scene_load:
            relevant_rooms = get_task_relevant_room_types(activity_name=task_name)
            relevant_rooms = augment_rooms(relevant_rooms, task_cfg["scene_model"], task_name)
            cfg["scene"]["load_room_types"] = relevant_rooms

        robot_cfg = self._build_robot_config(task_name=task_name, task_cfg=task_cfg)
        self.robot_name = robot_cfg["name"]
        cfg["robots"] = [robot_cfg]

        if self.cfg.max_steps is None:
            max_steps = int(self.human_stats["length"] * EVAL_TIMEOUT_MULTIPLIER)
            logger.info(
                f"Setting timeout to be {EVAL_TIMEOUT_MULTIPLIER}x the average length of human demos: {max_steps}"
            )
            cfg["task"]["termination_config"]["max_steps"] = max_steps
        else:
            logger.info(f"Setting timeout to be {self.cfg.max_steps} steps through config.")
            cfg["task"]["termination_config"]["max_steps"] = self.cfg.max_steps
        cfg["task"]["include_obs"] = False

        env = og.Environment(configs=cfg)
        env._eval_robot_config = self.robot_eval_config
        return instantiate(env_wrapper, env=env)

    def load_robot(self) -> Robot:
        if self.robot_name is not None:
            return self.env.scene.object_registry("name", self.robot_name)
        return self.env.robots[0]

    def _validate_robot_eval_config(self) -> None:
        missing_camera_sensors = []
        for camera_id, camera_name in self.robot_camera_names.items():
            sensor_name = camera_name.split("::", 1)[1]
            if sensor_name not in self.robot.sensors:
                missing_camera_sensors.append(f"{camera_id}: {sensor_name}")
        if missing_camera_sensors:
            raise ValueError(
                "Configured eval.camera_sensor_names entries were not found in robot.sensors: "
                f"{missing_camera_sensors}"
            )

        if self.cfg.get("write_video", False):
            required_camera_ids = {"left_wrist", "right_wrist", "head"}
            missing_camera_ids = sorted(required_camera_ids - set(self.robot_camera_names))
            if missing_camera_ids:
                raise ValueError(
                    "--write-video requires eval.camera_sensor_names roles "
                    f"{sorted(required_camera_ids)}; missing {missing_camera_ids}"
                )

    def _build_robot_config(self, task_name: str, task_cfg: dict) -> dict:
        robot_cfg = _to_plain_dict(OmegaConf.select(self.cfg, "robot"))
        if robot_cfg is None:
            robot_cfg = _to_plain_dict(OmegaConf.load(DEFAULT_ROBOT_CONFIG_PATH))
        else:
            robot_cfg = dict(robot_cfg)
        assert "model" in robot_cfg, "Robot config must include canonical 'model'"
        assert "type" not in robot_cfg, "Robot config must use canonical 'model', not 'type'"
        robot_cfg["model"] = robot_cfg["model"].lower()
        assert "name" in robot_cfg, "Robot config must include 'name'"
        self.robot_eval_config = _to_plain_dict(robot_cfg.pop("eval", None)) or {}
        robot_cfg["position"] = task_cfg["robot_start_position"]
        robot_cfg["orientation"] = task_cfg["robot_start_orientation"]

        return robot_cfg

    def _apply_robot_eval_settings(self) -> None:
        if self.robot.model in ("r1", "r1pro"):
            og.sim.stop()
            self.robot.base_footprint_link.mass = EVAL_BASE_LINK_MASS
            og.sim.play()

        head_camera_name = self.robot_camera_names.get("head")
        if head_camera_name is not None:
            head_sensor_name = head_camera_name.split("::")[1]
            if head_sensor_name in self.robot.sensors:
                self.robot.sensors[head_sensor_name].horizontal_aperture = EVAL_HEAD_HORIZONTAL_APERTURE

    def load_policy(self) -> Any:
        policy = instantiate(self.cfg.model)
        if hasattr(policy, "set_action_dim"):
            policy.set_action_dim(self.robot.action_dim)
        logger.info("")
        logger.info("=" * 50)
        logger.info(f"Loaded policy: {self.cfg.policy_name}")
        logger.info("=" * 50)
        logger.info("")
        return policy

    def load_metrics(self) -> List[MetricBase]:
        return [AgentMetric(self.human_stats), TaskMetric(self.human_stats)]

    def step(self) -> Tuple[bool, bool]:
        step_start = time.monotonic()
        policy_start = time.monotonic()
        needs_fresh_observation = bool(self.policy.needs_fresh_observation)
        if self._privileged_trace is not None:
            if needs_fresh_observation:
                self._record_radio_privileged_state()
            self._privileged_trace_step += 1
        self.robot_action = self.policy.forward(obs=self.obs)
        if needs_fresh_observation and self._training_recovery_snapshots is not None:
            self._maybe_record_radio_training_recovery_snapshot()
        policy_ms = (time.monotonic() - policy_start) * 1000

        rollout_status = getattr(self.policy, "rollout_status", None)
        if self._training_fail_fast and rollout_status and rollout_status.get("failure", False):
            reason = rollout_status.get("failure_reason") or "policy retry budget exhausted"
            return self._mark_fail_fast(f"policy_controller: {reason}")

        capture_observation = True
        if self._chunk_boundary_observations:
            capture_observation = bool(getattr(self.policy, "needs_fresh_observation", True))
        # Video output is deliberately incompatible with stale camera frames.
        if self._video_path is not None or self._side_video_path is not None:
            capture_observation = True

        env_start = time.monotonic()
        with og.sim.render_on_step(capture_observation):
            obs, _, terminated, truncated, info = self.env.step(
                self.robot_action,
                n_render_iterations=1,
                skip_obs=not capture_observation,
            )
        env_ms = (time.monotonic() - env_start) * 1000
        observation_start = time.monotonic()
        if capture_observation:
            obs = self._sync_lights_and_get_obs(obs)
            self.obs = self._preprocess_obs(obs)
            self._fresh_observation_steps += 1
        else:
            self._skipped_observation_steps += 1
        observation_ms = (time.monotonic() - observation_start) * 1000

        if (
            self._training_fail_fast
            and capture_observation
            and not (terminated or truncated)
            and self._table_displacement_exceeded()
        ):
            truncated = True

        if self._video_path is not None or self._side_video_path is not None:
            self._write_video()

        if terminated or truncated:
            self.n_trials += 1
            if info["done"]["success"]:
                self.n_success_trials += 1

        for metric in self.metrics:
            metric.step(self.env, self.robot_action, obs, 0.0, terminated, truncated, info)
        self._timing_step_count += 1
        if self._timing_log_every and self._timing_step_count % self._timing_log_every == 0:
            logger.info(
                "B1K_SIM_TIMING step=%d fresh_obs=%d policy_ms=%.1f env_ms=%.1f observation_ms=%.1f total_ms=%.1f",
                self._timing_step_count,
                int(capture_observation),
                policy_ms,
                env_ms,
                observation_ms,
                (time.monotonic() - step_start) * 1000,
            )
        return terminated, truncated

    def start_radio_privileged_trace(self) -> None:
        """Start a train-only radio trace aligned to policy decision boundaries.

        The evaluator calls this explicitly only for data collection. Simulator
        predicates are written after the episode and never enter the policy's
        online observation path.
        """
        if self.cfg.mode != "train":
            raise ValueError("Privileged critic traces are restricted to train mode.")
        if self.env.task.activity_name != "turning_on_radio":
            raise ValueError("Radio privileged tracing only supports turning_on_radio.")
        radios = [
            entity
            for name, entity in self.env.task.object_scope.items()
            if name.startswith("radio_receiver.n.") and entity is not None
        ]
        tables = [
            entity
            for name, entity in self.env.task.object_scope.items()
            if name.startswith("table.n.") and entity is not None
        ]
        if len(radios) != 1 or len(tables) != 1:
            raise RuntimeError(f"Expected one radio and table, found radios={len(radios)} tables={len(tables)}.")
        radio, table = radios[0], tables[0]
        radio_position = radio.get_position_orientation()[0]
        table_position = table.get_position_orientation()[0]
        self._privileged_trace = {
            "radio": radio,
            "table": table,
            "initial_radio_z": float(radio_position[2].item()),
            "initial_table_xy": table_position[:2].detach().cpu().numpy().copy(),
            "step_indices": [],
            "events": [],
            "physical_states": [],
        }
        self._privileged_trace_step = 0

    def _record_radio_privileged_state(self) -> None:
        trace = self._privileged_trace
        if trace is None:
            return
        radio = trace["radio"]
        table = trace["table"]
        radio_position = radio.get_position_orientation()[0]
        base_position = self.robot.get_position_orientation()[0]
        eef_distances = [
            th.linalg.vector_norm(self.robot.get_eef_position(arm) - radio_position)
            for arm in self.robot.arm_names
        ]
        base_distance = float(th.linalg.vector_norm(base_position[:2] - radio_position[:2]).item())
        eef_distance = min(float(distance.item()) for distance in eef_distances)
        radio_height_delta = float(radio_position[2].item() - trace["initial_radio_z"])
        table_xy = table.get_position_orientation()[0][:2].detach().cpu().numpy()
        table_displacement = float(np.linalg.norm(table_xy - trace["initial_table_xy"]))

        radio_link_paths = set(radio.link_prim_paths)
        contacted = any(
            bool(self.robot._find_gripper_contacts(arm)[0] & radio_link_paths)
            for arm in self.robot.arm_names
        )
        on_table = bool(radio.states[OnTop].get_value(table))
        toggled = bool(radio.states[ToggledOn].get_value())
        lifted = radio_height_delta >= 0.04 and not on_table
        grasped = any(
            self.robot.is_grasping(arm, candidate_obj=radio) == IsGraspingState.TRUE
            for arm in self.robot.arm_names
        ) or (not on_table and radio_height_delta >= 0.002)
        docked = base_distance <= 1.20 and eef_distance <= 0.80
        placed = toggled and on_table and not grasped

        trace["step_indices"].append(self._privileged_trace_step)
        trace["events"].append([docked, grasped, toggled, contacted, lifted, placed])
        trace["physical_states"].append(
            [base_distance, eef_distance, radio_height_delta, table_displacement]
        )

    def finish_radio_privileged_trace(
        self,
        path: str,
        *,
        success: bool,
        metadata: dict | None = None,
    ) -> str:
        """Persist and clear the current offline critic-supervision trace."""
        trace = self._privileged_trace
        if trace is None:
            raise RuntimeError("No radio privileged trace is active.")
        output_path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if os.path.exists(output_path):
            raise FileExistsError(f"Refusing to overwrite privileged trace: {output_path}")
        temporary_path = output_path + ".tmp"
        with open(temporary_path, "wb") as file:
            np.savez_compressed(
                file,
                format_version=np.asarray(1, dtype=np.int32),
                label_source=np.asarray("live_train_simulator_state_offline_only"),
                event_names=np.asarray(RADIO_TRACE_EVENT_NAMES),
                state_names=np.asarray(RADIO_TRACE_STATE_NAMES),
                step_indices=np.asarray(trace["step_indices"], dtype=np.int64),
                events=np.asarray(trace["events"], dtype=np.float32),
                physical_states=np.asarray(trace["physical_states"], dtype=np.float32),
                success=np.asarray(bool(success)),
                metadata_json=np.asarray(json.dumps(metadata or {}, sort_keys=True)),
            )
        os.replace(temporary_path, output_path)
        self._privileged_trace = None
        self._privileged_trace_step = 0
        return output_path

    def start_radio_training_recovery_snapshots(self, directory: str, *, metadata: dict | None = None) -> None:
        """Arm bounded, train-only simulator snapshots at radio recovery entry states."""
        if self.cfg.mode != "train":
            raise ValueError("Privileged recovery snapshots are restricted to train mode.")
        if self._privileged_trace is None:
            raise RuntimeError("Recovery snapshots require an active privileged radio trace.")
        if self._training_recovery_snapshots is not None:
            raise RuntimeError("Radio recovery snapshot collection is already active.")
        output_dir = os.path.abspath(os.path.expanduser(directory))
        os.makedirs(output_dir, exist_ok=True)
        self._training_recovery_snapshots = {
            "directory": output_dir,
            "metadata": dict(metadata or {}),
            "seen_keys": set(),
            "paths": [],
            "grounded_grasp_loss_count": 0,
        }

    def _maybe_record_radio_training_recovery_snapshot(self) -> None:
        snapshots = self._training_recovery_snapshots
        trace = self._privileged_trace
        if snapshots is None or trace is None or not trace["events"]:
            return

        status = getattr(self.policy, "rollout_status", None) or {}
        control_state = str(status.get("control_state", ""))
        trigger_keys = []
        if control_state == "grasp_retry":
            trigger_keys.append(f"grasp_retry_{int(status.get('grasp_retries', 0))}")
        elif control_state == "press_retry":
            trigger_keys.append(f"press_retry_{int(status.get('press_retries', 0))}")
        elif control_state == "failure":
            trigger_keys.append("controller_failure")

        grasp_index = RADIO_TRACE_EVENT_NAMES.index("grasped")
        if len(trace["events"]) >= 2 and trace["events"][-2][grasp_index] and not trace["events"][-1][grasp_index]:
            snapshots["grounded_grasp_loss_count"] += 1
            trigger_keys.append(f"grounded_grasp_loss_{snapshots['grounded_grasp_loss_count']}")

        new_keys = [key for key in trigger_keys if key not in snapshots["seen_keys"]]
        if not new_keys:
            return
        snapshots["seen_keys"].update(new_keys)
        state = og.sim.dump_state(serialized=True).detach().cpu().numpy()
        decision_index = len(trace["events"]) - 1
        metadata = {
            **snapshots["metadata"],
            "decision_index": decision_index,
            "simulator_step_index": int(trace["step_indices"][-1]),
            "triggers": new_keys,
        }
        safe_trigger = "__".join(new_keys).replace("/", "-")
        output_path = os.path.join(
            snapshots["directory"],
            f"snapshot-{len(snapshots['paths']):03d}_{safe_trigger}.npz",
        )
        if os.path.exists(output_path):
            raise FileExistsError(f"Refusing to overwrite training recovery snapshot: {output_path}")
        temporary_path = output_path + ".tmp"
        with open(temporary_path, "wb") as file:
            np.savez_compressed(
                file,
                format_version=np.asarray(1, dtype=np.int32),
                label_source=np.asarray("live_train_simulator_state_offline_only"),
                simulator_state=state,
                state_size=np.asarray(len(state), dtype=np.int64),
                event_names=np.asarray(RADIO_TRACE_EVENT_NAMES),
                events=np.asarray(trace["events"][-1], dtype=np.float32),
                state_names=np.asarray(RADIO_TRACE_STATE_NAMES),
                physical_state=np.asarray(trace["physical_states"][-1], dtype=np.float32),
                rollout_status_json=np.asarray(json.dumps(status, sort_keys=True)),
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
            )
        os.replace(temporary_path, output_path)
        snapshots["paths"].append(output_path)
        logger.info("Saved train-only radio recovery snapshot: %s", output_path)

    def finish_radio_training_recovery_snapshots(self) -> list[str]:
        """Return snapshot paths and disarm collection for the current rollout."""
        snapshots = self._training_recovery_snapshots
        if snapshots is None:
            raise RuntimeError("No radio recovery snapshot collection is active.")
        paths = list(snapshots["paths"])
        self._training_recovery_snapshots = None
        return paths

    def load_radio_training_recovery_snapshot(self, path: str, *, expected_metadata: dict) -> dict:
        """Restore one validated train-only radio state for controlled recovery experiments."""
        if self.cfg.mode != "train":
            raise ValueError("Privileged recovery snapshots may be loaded only in train mode.")
        if self.env.task.activity_name != "turning_on_radio":
            raise ValueError("Radio recovery snapshots only support turning_on_radio.")
        snapshot_path = os.path.abspath(os.path.expanduser(path))
        with np.load(snapshot_path, allow_pickle=False) as snapshot:
            required = {"format_version", "simulator_state", "state_size", "metadata_json"}
            missing = sorted(required - set(snapshot.files))
            if missing:
                raise ValueError(f"Recovery snapshot is missing fields: {missing}")
            if int(snapshot["format_version"].item()) != 1:
                raise ValueError(f"Unsupported recovery snapshot format in {snapshot_path}")
            metadata = json.loads(str(snapshot["metadata_json"].item()))
            mismatches = {
                key: (metadata.get(key), value)
                for key, value in expected_metadata.items()
                if metadata.get(key) != value
            }
            if mismatches:
                raise ValueError(f"Recovery snapshot identity mismatch: {mismatches}")
            state = np.asarray(snapshot["simulator_state"])
            if state.ndim != 1 or len(state) != int(snapshot["state_size"].item()):
                raise ValueError("Recovery snapshot state vector has an invalid shape or size.")

        og.sim.load_state(th.as_tensor(state), serialized=True)
        # A physics step updates object-state caches after serialized restoration.
        og.sim.step_physics()
        og.sim.render()
        obs, _ = self.env.get_obs()
        obs = self._sync_lights_and_get_obs(obs)
        self.obs = self._preprocess_obs(obs)
        for metric in self.metrics:
            metric.reset(self.env)
        self._reset_fail_fast_monitor()
        logger.info("Loaded train-only radio recovery snapshot: %s", snapshot_path)
        return metadata

    def _mark_fail_fast(self, reason: str) -> Tuple[bool, bool]:
        if self.early_termination_reason is None:
            self.early_termination_reason = reason
            self.n_trials += 1
            logger.warning("Training rollout fail-fast termination: %s", reason)
        return False, True

    def _reset_fail_fast_monitor(self) -> None:
        self.early_termination_reason = None
        self._fail_fast_table = None
        self._fail_fast_initial_table_xy = None
        self._fail_fast_table_streak = 0
        self._fresh_observation_steps = 0
        self._skipped_observation_steps = 0
        if not self._training_fail_fast:
            return
        tables = [
            entity
            for name, entity in self.env.task.object_scope.items()
            if name.startswith("table.n.") and entity is not None
        ]
        if len(tables) != 1:
            logger.warning("Fail-fast table monitor expected one task table, found %d; disabling it.", len(tables))
            return
        self._fail_fast_table = tables[0]
        self._fail_fast_initial_table_xy = (
            self._fail_fast_table.get_position_orientation()[0][:2].detach().cpu().numpy().copy()
        )

    def _table_displacement_exceeded(self) -> bool:
        if self._fail_fast_table is None or self._fail_fast_initial_table_xy is None:
            return False
        table_xy = self._fail_fast_table.get_position_orientation()[0][:2].detach().cpu().numpy()
        displacement = float(np.linalg.norm(table_xy - self._fail_fast_initial_table_xy))
        if displacement >= self._fail_fast_table_displacement:
            self._fail_fast_table_streak += 1
        else:
            self._fail_fast_table_streak = 0
        if self._fail_fast_table_streak < self._fail_fast_table_patience:
            return False
        self.early_termination_reason = (
            f"table_displacement={displacement:.4f}m exceeded "
            f"{self._fail_fast_table_displacement:.4f}m for "
            f"{self._fail_fast_table_streak} fresh observations"
        )
        logger.warning("Training rollout fail-fast termination: %s", self.early_termination_reason)
        return True

    @property
    def video_writer(self) -> Tuple[Container, Stream]:
        return self._video_writer

    @video_writer.setter
    def video_writer(self, video_writer: Tuple[Container, Stream]) -> None:
        if self._video_writer is not None:
            container, stream = self._video_writer
            for packet in stream.encode():
                container.mux(packet)
            container.close()
        self._video_writer = video_writer

    def load_task_instance(self, instance_id: int) -> None:
        scene_model = self.env.task.scene_name
        tro_filename = self.env.task.get_cached_activity_scene_filename(
            scene_model=scene_model,
            activity_name=self.env.task.activity_name,
            activity_definition_id=self.env.task.activity_definition_id,
            activity_instance_id=instance_id,
        )
        mode = self.cfg.get("mode", "public_test")
        tro_file_path = get_task_instance_path(
            scene_model,
            f"{scene_model}_task_{self.env.task.activity_name}_instances/{tro_filename}-tro_state",
            mode=mode,
        )
        if tro_file_path is None:
            raise FileNotFoundError(
                f"Could not find 2026 {mode} task instance {instance_id} for "
                f"{self.env.task.activity_name} in scene {scene_model}."
            )

        with open(tro_file_path, "r") as f:
            tro_state = recursively_convert_to_torch(json.load(f))
        for tro_key, tro_state in tro_state.items():
            if tro_key == "robot_poses":
                presampled_robot_poses = {key.lower(): value for key, value in tro_state.items()}
                if "robot" in presampled_robot_poses:
                    available_poses = presampled_robot_poses["robot"]
                elif self.robot.model in presampled_robot_poses:
                    logger.info("No generic presampled robot pose found, using robot-specific pose.")
                    available_poses = presampled_robot_poses[self.robot.model]
                else:
                    raise KeyError(f"No generic or model-specific presampled robot pose found for {self.robot.model}!")
                self.robot.set_position_orientation(available_poses[0]["position"], available_poses[0]["orientation"])
                self.env.scene.write_task_metadata(key=tro_key, data=tro_state)
            else:
                self.env.task.object_scope[tro_key].load_state(tro_state, serialized=False)

        if self.should_sync_lights:
            set_light_control_toggles(self.env.task.object_scope.values(), True)

        # Keep all task-relevant entities (including the robot/agent) still while the scene settles,
        # so the snapshotted per-instance initial state is stable. The robot must already be in a clean
        # configuration when this is called -- eval.py resets before load_task_instance for this reason.
        og.sim.update_handles()
        for _ in range(25):
            og.sim.step_physics()
            for inst, entity in self.env.task.object_scope.items():
                if not is_system_bddl_inst(inst) and entity is not None:
                    entity.keep_still()

        self.env.scene.update_initial_file()
        self.env.scene.reset()
        self._reset_light_synchronizer()

    def _preprocess_obs(self, obs: dict) -> dict:
        obs = flatten_obs_dict(obs)
        base_pose = self.robot.get_position_orientation()
        cam_rel_poses = []
        for camera_name in self.robot_camera_names.values():
            sensor_name = camera_name.split("::")[1]
            if sensor_name not in self.robot.sensors:
                continue
            camera = self.robot.sensors[sensor_name]
            direct_cam_pose = camera.camera_parameters["cameraViewTransform"]
            if np.allclose(direct_cam_pose, np.zeros(16)):
                cam_rel_poses.append(
                    th.cat(T.relative_pose_transform(*(camera.get_position_orientation()), *base_pose))
                )
            else:
                cam_pose = T.mat2pose(th.tensor(np.linalg.inv(np.reshape(direct_cam_pose, [4, 4]).T), dtype=th.float32))
                cam_rel_poses.append(th.cat(T.relative_pose_transform(*cam_pose, *base_pose)))
        if cam_rel_poses:
            obs[f"{self.robot.name}::cam_rel_poses"] = th.cat(cam_rel_poses, axis=-1)
        obs["task_id"] = th.tensor([TASK_NAMES_TO_INDICES[self.cfg.task.name]], dtype=th.int64)
        return obs

    def _write_video(self) -> None:
        if self._side_video_path is not None:
            self._write_side_video()

        if self._video_path is None:
            return
        required_camera_ids = ("left_wrist", "right_wrist", "head")
        if not all(camera_id in self.robot_camera_names for camera_id in required_camera_ids):
            return
        if self.robot_camera_names["head"] + "::rgb" not in self.obs:
            return
        left_wrist_rgb = cv2.resize(
            self.obs[self.robot_camera_names["left_wrist"] + "::rgb"].numpy(),
            (224, 224),
        )
        right_wrist_rgb = cv2.resize(
            self.obs[self.robot_camera_names["right_wrist"] + "::rgb"].numpy(),
            (224, 224),
        )
        head_rgb = cv2.resize(
            self.obs[self.robot_camera_names["head"] + "::rgb"].numpy(),
            (448, 448),
        )
        frame = np.expand_dims(np.hstack([np.vstack([left_wrist_rgb, right_wrist_rgb]), head_rgb]), 0)
        if self._video_writer is None:
            # Writer is created lazily so its resolution matches the composite (H, W) frame above.
            self.video_writer = create_video_writer(
                self._video_path, resolution=frame.shape[1:3], rate=self._video_rate
            )
        write_video(frame, video_writer=self.video_writer, batch_size=1, mode="rgb")

    def _write_side_video(self) -> None:
        camera = og.sim.viewer_camera
        camera.focal_length = 8.0
        camera.set_position_orientation(*self._side_camera_pose)
        og.sim.render()

        rgb = camera.get_obs()[0]["rgb"]
        if isinstance(rgb, th.Tensor):
            rgb = rgb.cpu().numpy()
        rgb = np.asarray(rgb)[..., :3]
        frame = np.expand_dims(rgb, 0)
        if self._side_video_writer is None:
            self._side_video_writer = create_video_writer(
                self._side_video_path, resolution=frame.shape[1:3], rate=self._video_rate
            )
        write_video(frame, video_writer=self._side_video_writer, batch_size=1, mode="rgb")

    @staticmethod
    def _close_writer(video_writer: Tuple[Container, Stream] | None) -> None:
        if video_writer is None:
            return
        container, stream = video_writer
        for packet in stream.encode():
            container.mux(packet)
        container.close()

    def start_recording(self, fpath: str | None, rate: int = 30, side_fpath: str | None = None) -> None:
        # Finalize any in-progress recording, then arm a new one (writer is created on the first frame).
        self.stop_recording()
        self._video_path = fpath
        self._side_video_path = side_fpath
        self._side_camera_pose = self._get_fixed_side_camera_pose() if side_fpath is not None else None
        self._video_rate = rate

    def _get_fixed_side_camera_pose(self) -> tuple[th.Tensor, th.Tensor]:
        robot_pos = self.robot.get_position_orientation()[0]
        radio = next(
            entity
            for name, entity in self.env.task.object_scope.items()
            if name.startswith("radio_receiver.n.") and entity is not None
        )
        radio_pos = radio.get_position_orientation()[0]
        world_up = th.tensor([0.0, 0.0, 1.0], dtype=robot_pos.dtype, device=robot_pos.device)

        # Stay beside the task object and look across the robot's approach path. The pose is
        # computed once at recording start and remains fixed for the entire rollout.
        approach = radio_pos - robot_pos
        approach[2] = 0.0
        approach = th.nn.functional.normalize(approach, dim=0)
        side = th.linalg.cross(world_up, approach)
        camera_pos = radio_pos - side * 2.2 + world_up * 1.35
        target = (robot_pos + radio_pos) * 0.5 + world_up * 0.85
        forward = th.nn.functional.normalize(target - camera_pos, dim=0)
        right = th.nn.functional.normalize(th.linalg.cross(forward, world_up), dim=0)
        up = th.linalg.cross(right, forward)
        camera_rot = th.stack((right, up, -forward), dim=1)
        return camera_pos, T.mat2quat(camera_rot)

    def stop_recording(self) -> None:
        self.video_writer = None
        self._close_writer(self._side_video_writer)
        self._side_video_writer = None
        self._video_path = None
        self._side_video_path = None
        self._side_camera_pose = None

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            seed_everything(seed)
        obs = self.env.reset()[0]
        self._reset_light_synchronizer()
        obs = self._sync_lights_and_get_obs(obs)
        self.obs = self._preprocess_obs(obs)
        for metric in self.metrics:
            metric.reset(self.env)
        self.policy.reset(seed=seed)
        self.n_success_trials, self.n_trials = 0, 0
        self._reset_fail_fast_monitor()

    @property
    def collection_stats(self) -> dict:
        return {
            "fresh_observation_steps": self._fresh_observation_steps,
            "skipped_observation_steps": self._skipped_observation_steps,
            "early_termination_reason": self.early_termination_reason,
        }

    def finish_rollout(self, success: bool, metadata: dict | None = None) -> str | None:
        """Notify a recording policy of the terminal label and return its replay path, if any."""
        finish = getattr(self.policy, "finish_rollout", None)
        if finish is None:
            return None
        return finish(success=success, metadata=metadata)

    def __enter__(self):
        signal(SIGINT, self._sigint_handler)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        logger.info("")
        logger.info("=" * 50)
        logger.info(f"Total success trials: {self.n_success_trials}")
        logger.info(f"Total trials: {self.n_trials}")
        if self.n_trials > 0:
            logger.info(f"Success rate: {self.n_success_trials / self.n_trials}")
        logger.info("=" * 50)
        logger.info("")
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, exc_tb)
        self.stop_recording()
        self.env.close()
        og.shutdown()

    def _sigint_handler(self, signal_received, frame):
        logger.warning("SIGINT or CTRL-C detected.\n")
        self.__exit__(None, None, None)
        sys.exit(0)


__all__ = ["Evaluator", "resolve_instance_ids"]
