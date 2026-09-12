"""Extract simulator-grounded radio events from exact recorded demonstration states.

The LeRobot export maps each episode to its source ``raw_episode_id``.  The corresponding raw
HDF5 contains the original scene JSON and a serialized OmniGibson state before every action.  This
utility restores those states directly instead of action-replaying a packaged task instance, which
avoids both task-instance ID mismatches and accumulated replay drift.

Each episode is downloaded through the Hugging Face cache and written independently, so an
interrupted multi-hour extraction can be resumed safely.
"""

import argparse
import json
import logging
from pathlib import Path
import tempfile

import h5py
from huggingface_hub import hf_hub_download
import numpy as np
import pandas as pd
import torch as th

import omnigibson as og
from omnigibson.controllers.controller_base import IsGraspingState
from omnigibson.envs import HDF5PlaybackWrapper
from omnigibson.envs.data_wrapper import _align_scene_object_states_with_recorded_schema
from omnigibson.eval.utils.eval_utils import DEFAULT_EVAL_SEED, seed_everything
from omnigibson.macros import gm
from omnigibson.object_states import OnTop, ToggledOn
from omnigibson.utils import transform_utils as T
from omnigibson.utils.ui_utils import create_module_logger


logger = create_module_logger(module_name=__name__)
logger.setLevel(logging.INFO)

# Keep the original three transition events first for compatibility with the pilot observer checkpoint.
EVENT_NAMES = ("docked", "grasped", "toggled", "contacted", "lifted", "placed")
STATE_NAMES = (
    "base_radio_xy_distance",
    "nearest_eef_radio_distance",
    "radio_height_delta",
    "table_xy_displacement",
)
LABEL_SOURCE = "raw_hdf5_simulator_states"
TOGGLE_TARGET_CAMERA_TOKENS = (
    "zed_link",
    "left_realsense_link",
    "right_realsense_link",
)
TOGGLE_TARGET_CAMERA_NAMES = ("head", "left_wrist", "right_wrist")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("/home/ywang/Behavior/data/2026-challenge-demos"),
    )
    parser.add_argument(
        "--raw-repo-id",
        default="behavior-1k/2026-challenge-rawdata",
        help="Hugging Face dataset containing the source HDF5 demonstrations.",
    )
    parser.add_argument("--raw-revision", default="main")
    parser.add_argument(
        "--raw-cache-dir",
        type=Path,
        default=None,
        help="Optional Hugging Face cache directory; the normal hub cache is used by default.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/ywang/Behavior/openpi/phase_data/turning_on_radio/grounded_events_raw"),
    )
    parser.add_argument("--task-index", type=int, default=0)
    parser.add_argument("--sample-stride", type=int, default=16)
    parser.add_argument("--max-episodes", type=int, default=200)
    parser.add_argument(
        "--episode-start-index",
        type=int,
        default=0,
        help="When --episode-indices is omitted, select episodes at or above this LeRobot index.",
    )
    parser.add_argument("--episode-stride", type=int, default=1)
    parser.add_argument("--episode-indices", type=int, nargs="*", default=None)
    parser.add_argument("--docked-base-distance", type=float, default=1.20)
    parser.add_argument("--docked-eef-distance", type=float, default=0.80)
    parser.add_argument("--lift-height", type=float, default=0.04)
    parser.add_argument(
        "--legacy-grasp-lift-height",
        type=float,
        default=0.002,
        help="Minimum radio lift used to recover grasps from recordings that predate assisted-grasp serialization.",
    )
    parser.add_argument("--overwrite", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument(
        "--write-toggle-targets",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Project the privileged radio toggle marker into the three robot cameras. "
            "The resulting files are training labels only; the online policy never receives the marker pose."
        ),
    )
    parser.add_argument(
        "--manifest-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Validate existing episode files and rebuild manifest.json without launching the simulator.",
    )
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def _load_episode_metadata(dataset_root: Path) -> pd.DataFrame:
    paths = sorted((dataset_root / "meta" / "episodes").glob("**/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No episode metadata found under {dataset_root}.")
    columns = ["episode_index", "length", "task_instance_id", "raw_episode_id", "annotation_path"]
    metadata = pd.concat([pd.read_parquet(path, columns=columns) for path in paths], ignore_index=True)
    if metadata["raw_episode_id"].isna().any():
        raise RuntimeError("Every selected episode must have a raw_episode_id mapping.")
    return metadata


def _finger_contact(robot, radio) -> bool:
    radio_link_paths = set(radio.link_prim_paths)
    for arm in robot.arm_names:
        contact_paths, _ = robot._find_gripper_contacts(arm)  # No public finger-only contact query exists.
        if contact_paths & radio_link_paths:
            return True
    return False


def _is_grasped(robot, radio) -> bool:
    return any(robot.is_grasping(arm, candidate_obj=radio) == IsGraspingState.TRUE for arm in robot.arm_names)


def _sample_grounded_state(
    robot,
    radio,
    table,
    initial_radio_z: float,
    initial_table_xy: np.ndarray,
    args: argparse.Namespace,
) -> tuple[np.ndarray, np.ndarray]:
    radio_position = radio.get_position_orientation()[0]
    base_position = robot.get_position_orientation()[0]
    eef_distances = [th.linalg.vector_norm(robot.get_eef_position(arm) - radio_position) for arm in robot.arm_names]
    base_distance = th.linalg.vector_norm(base_position[:2] - radio_position[:2]).item()
    eef_distance = min(float(distance.item()) for distance in eef_distances)
    radio_height_delta = float(radio_position[2].item() - initial_radio_z)
    table_xy = table.get_position_orientation()[0][:2].detach().cpu().numpy()
    table_displacement = float(np.linalg.norm(table_xy - initial_table_xy))

    contacted = _finger_contact(robot, radio)
    on_table = bool(radio.states[OnTop].get_value(table))
    toggled = bool(radio.states[ToggledOn].get_value())
    lifted = radio_height_delta >= args.lift_height and not on_table
    # The 2026 raw demonstrations were recorded before assisted-grasp constraints were added to
    # serialized robot state. Prefer the live simulator predicate when it is available; otherwise
    # recover the physically unambiguous interval where the radio has left its support surface.
    grasped = _is_grasped(robot, radio) or (
        not on_table and radio_height_delta >= args.legacy_grasp_lift_height
    )
    docked = base_distance <= args.docked_base_distance and eef_distance <= args.docked_eef_distance
    placed = toggled and on_table and not grasped

    events = np.asarray([docked, grasped, toggled, contacted, lifted, placed], dtype=np.float32)
    physical_state = np.asarray(
        [base_distance, eef_distance, radio_height_delta, table_displacement], dtype=np.float32
    )
    return events, physical_state


def _episode_output_path(output_dir: Path, episode_index: int) -> Path:
    return output_dir / f"episode_{episode_index:06d}.npz"


def _episode_file_is_valid(
    path: Path,
    episode_index: int,
    raw_episode_id: int | None = None,
    *,
    require_toggle_targets: bool = False,
) -> bool:
    try:
        with np.load(path) as episode:
            valid = (
                int(episode["episode_index"]) == episode_index
                and str(episode["label_source"]) == LABEL_SOURCE
                and episode["events"].ndim == 2
                and episode["events"].shape[1] == len(EVENT_NAMES)
                and len(episode["frame_indices"]) == len(episode["events"])
                and len(episode["physical_states"]) == len(episode["events"])
            )
            if require_toggle_targets:
                num_samples = len(episode["events"])
                num_cameras = len(TOGGLE_TARGET_CAMERA_NAMES)
                valid = valid and (
                    tuple(map(str, episode["toggle_target_camera_names"].tolist()))
                    == TOGGLE_TARGET_CAMERA_NAMES
                    and episode["toggle_target_normalized_pixels"].shape == (num_samples, num_cameras, 2)
                    and episode["toggle_target_camera_coordinates"].shape == (num_samples, num_cameras, 3)
                    and episode["toggle_target_clip_w"].shape == (num_samples, num_cameras)
                    and episode["toggle_target_in_frame"].shape == (num_samples, num_cameras)
                    and episode["toggle_target_camera_resolutions"].shape == (num_samples, num_cameras, 2)
                )
            return valid and (raw_episode_id is None or int(episode["raw_episode_id"]) == raw_episode_id)
    except (OSError, ValueError, KeyError):
        return False


def _write_manifest(args: argparse.Namespace, metadata: pd.DataFrame) -> None:
    total_event_counts = np.zeros(len(EVENT_NAMES), dtype=np.int64)
    episodes_with_event = np.zeros(len(EVENT_NAMES), dtype=np.int64)
    num_samples = 0
    raw_episode_ids = []
    episode_indices = []
    for row in metadata.itertuples(index=False):
        episode_index = int(row.episode_index)
        raw_episode_id = int(row.raw_episode_id)
        path = _episode_output_path(args.output_dir, episode_index)
        if not _episode_file_is_valid(
            path,
            episode_index,
            raw_episode_id,
            require_toggle_targets=args.write_toggle_targets,
        ):
            raise RuntimeError(f"Missing or malformed grounded-label file: {path}")
        with np.load(path) as episode:
            events = episode["events"]
        event_counts = events.astype(bool).sum(axis=0)
        total_event_counts += event_counts
        episodes_with_event += event_counts > 0
        num_samples += len(events)
        episode_indices.append(episode_index)
        raw_episode_ids.append(raw_episode_id)

    manifest = {
        "label_source": LABEL_SOURCE,
        "dataset_root": str(args.dataset_root),
        "raw_repo_id": args.raw_repo_id,
        "raw_revision": args.raw_revision,
        "task_index": args.task_index,
        "sample_stride": args.sample_stride,
        "event_names": EVENT_NAMES,
        "state_names": STATE_NAMES,
        "thresholds": {
            "docked_base_distance": args.docked_base_distance,
            "docked_eef_distance": args.docked_eef_distance,
            "lift_height": args.lift_height,
            "legacy_grasp_lift_height": args.legacy_grasp_lift_height,
        },
        "grasp_label_method": (
            "live simulator grasp predicate, with off-support lift fallback because the legacy raw "
            "recordings predate assisted-grasp constraint serialization"
        ),
        "episodes": episode_indices,
        "raw_episode_ids": raw_episode_ids,
        "num_samples": num_samples,
        "event_sample_counts": dict(zip(EVENT_NAMES, total_event_counts.astype(int).tolist(), strict=True)),
        "episodes_with_event": dict(zip(EVENT_NAMES, episodes_with_event.astype(int).tolist(), strict=True)),
        "toggle_target_schema": (
            {
                "camera_names": TOGGLE_TARGET_CAMERA_NAMES,
                "normalized_pixel_convention": "u rightward and v downward, each divided by image width/height",
                "label_policy": "privileged marker projection for offline training only",
            }
            if args.write_toggle_targets
            else None
        ),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))


def _download_raw_episode(args: argparse.Namespace, raw_episode_id: int) -> Path:
    filename = f"task-{args.task_index:04d}/episode_{raw_episode_id:08d}.hdf5"
    return Path(
        hf_hub_download(
            repo_id=args.raw_repo_id,
            filename=filename,
            repo_type="dataset",
            revision=args.raw_revision,
            cache_dir=str(args.raw_cache_dir) if args.raw_cache_dir is not None else None,
        )
    )


def _task_object_names(scene_file: dict) -> tuple[str, str]:
    mapping = scene_file.get("metadata", {}).get("task", {}).get("inst_to_name", {})
    radio_names = [name for synset, name in mapping.items() if synset.startswith("radio_receiver.n.")]
    table_names = [name for synset, name in mapping.items() if synset.startswith("table.n.")]
    if len(radio_names) != 1 or len(table_names) != 1:
        raise RuntimeError(f"Expected exactly one radio and table in scene task metadata, got {mapping}.")
    return radio_names[0], table_names[0]


def _prepare_recorded_scene(playback: HDF5PlaybackWrapper, trajectory, scene_file: dict) -> None:
    """Validate the shared scene registry and synchronize its recorded state schema.

    Challenge task 0 uses one fixed object registry across all source episodes.  We intentionally do
    not call ``Scene.restore(scene_file)`` here: raw demonstrations predate the current robot
    ``controller_groups`` JSON field, while their serialized state vectors remain playback-compatible.
    State 0 below restores every dynamic per-episode value, including robot and object poses.
    """
    playback.recorded_scene_file = scene_file
    playback.scene_file = scene_file

    state = scene_file.get("state", {})
    recorded_registry = state.get("registry", {}).get(
        "object_registry", state.get("object_registry", {})
    )
    recorded_names = set(recorded_registry)
    loaded_names = {obj.name for obj in playback.scene.objects}
    if recorded_names != loaded_names:
        missing = sorted(recorded_names - loaded_names)
        extra = sorted(loaded_names - recorded_names)
        raise RuntimeError(f"Raw scene registry differs from loaded scene; missing={missing}, extra={extra}.")

    # Match official HDF5 playback: restore per-object initialization metadata before reset.
    init_metadata = trajectory.get("init_metadata")
    if init_metadata is not None and len(init_metadata):
        og.sim.stop()
        for attr, dataset in init_metadata.items():
            values = dataset[:]
            if len(values) != playback.scene.n_objects:
                raise RuntimeError(
                    f"init_metadata[{attr!r}] has {len(values)} objects; scene has {playback.scene.n_objects}."
                )
            for obj, value in zip(playback.scene.objects, values, strict=True):
                tensor = th.as_tensor(value)
                setattr(obj, attr, tensor.item() if tensor.ndim == 0 else tensor)
        og.sim.play()

    _align_scene_object_states_with_recorded_schema(
        scene=playback.scene,
        recorded_scene_file=scene_file,
    )


def project_world_point_to_camera(world_point: np.ndarray, camera_parameters: dict) -> dict[str, np.ndarray | float | bool]:
    """Project one world point using Isaac Sim's row-vector view/projection convention."""
    world_point = np.asarray(world_point, dtype=np.float64)
    if world_point.shape != (3,) or not np.all(np.isfinite(world_point)):
        raise ValueError(f"Expected one finite world point, got {world_point}.")
    view_matrix = np.asarray(camera_parameters["cameraViewTransform"], dtype=np.float64).reshape(4, 4)
    projection_matrix = np.asarray(camera_parameters["cameraProjection"], dtype=np.float64).reshape(4, 4)
    resolution = np.asarray(camera_parameters["renderProductResolution"], dtype=np.int64)
    if resolution.shape != (2,) or np.any(resolution <= 0):
        raise ValueError(f"Invalid camera resolution: {resolution}.")

    homogeneous = np.concatenate((world_point, np.ones(1, dtype=np.float64)))
    camera_coordinates = homogeneous @ view_matrix
    clip_coordinates = camera_coordinates @ projection_matrix
    clip_w = float(clip_coordinates[-1])
    if not np.isfinite(clip_w) or abs(clip_w) <= 1e-9:
        normalized_pixel = np.full(2, np.nan, dtype=np.float32)
        in_frame = False
    else:
        normalized_device = clip_coordinates[:2] / clip_w
        # Isaac's normalized device y increases upward; image rows increase downward.
        normalized_pixel = np.asarray(
            [0.5 * (normalized_device[0] + 1.0), 1.0 - 0.5 * (normalized_device[1] + 1.0)],
            dtype=np.float32,
        )
        in_frame = bool(np.all(np.isfinite(normalized_pixel)) and np.all((0.0 <= normalized_pixel) & (normalized_pixel < 1.0)))
    return {
        "normalized_pixel": normalized_pixel,
        "camera_coordinates": np.asarray(camera_coordinates[:3], dtype=np.float32),
        "clip_w": clip_w,
        "in_frame": in_frame,
        "resolution": resolution.astype(np.int32),
    }


def _resolve_toggle_target_sensors(robot) -> tuple:
    sensors = []
    for token in TOGGLE_TARGET_CAMERA_TOKENS:
        matches = [sensor for name, sensor in robot.sensors.items() if token in name]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one robot camera sensor containing {token!r}, found "
                f"{[name for name in robot.sensors if token in name]}."
            )
        sensor = matches[0]
        parameters = sensor.camera_parameters
        sensors.append(
            {
                "sensor": sensor,
                "projection": np.asarray(parameters["cameraProjection"], dtype=np.float32).copy(),
                "resolution": np.asarray(parameters["renderProductResolution"], dtype=np.int32).copy(),
            }
        )
    return tuple(sensors)


def _toggle_marker_in_link_transform(radio) -> th.Tensor:
    toggle_state = radio.states[ToggledOn]
    link_pose = T.pose2mat(toggle_state.link.get_position_orientation())
    marker_pose = T.pose2mat(toggle_state.visual_marker.get_position_orientation())
    return T.pose_inv(link_pose) @ marker_pose


def _sample_toggle_targets(sensors: tuple, radio, marker_in_link: th.Tensor) -> dict[str, np.ndarray]:
    toggle_state = radio.states[ToggledOn]
    link_pose = T.pose2mat(toggle_state.link.get_position_orientation())
    marker_position = (link_pose @ marker_in_link)[:3, 3].detach().cpu().numpy()
    projections = []
    for camera in sensors:
        # Camera-parameter annotators are updated only during rendering. Exact-state
        # playback intentionally renders zero times per sample, so reconstruct the
        # live view matrix from the restored sensor pose while reusing static intrinsics.
        camera_pose = T.pose2mat(camera["sensor"].get_position_orientation()).detach().cpu().numpy()
        live_view_matrix = np.linalg.inv(camera_pose).T
        projections.append(
            project_world_point_to_camera(
                marker_position,
                {
                    "cameraViewTransform": live_view_matrix,
                    "cameraProjection": camera["projection"],
                    "renderProductResolution": camera["resolution"],
                },
            )
        )
    return {
        "normalized_pixels": np.stack([item["normalized_pixel"] for item in projections]),
        "camera_coordinates": np.stack([item["camera_coordinates"] for item in projections]),
        "clip_w": np.asarray([item["clip_w"] for item in projections], dtype=np.float32),
        "in_frame": np.asarray([item["in_frame"] for item in projections], dtype=bool),
        "camera_resolutions": np.stack([item["resolution"] for item in projections]),
    }


def _extract_episode(
    playback: HDF5PlaybackWrapper,
    raw_path: Path,
    row,
    output_path: Path,
    args: argparse.Namespace,
) -> np.ndarray:
    episode_index = int(row.episode_index)
    raw_episode_id = int(row.raw_episode_id)
    with h5py.File(raw_path, "r") as raw_file:
        scene_file = json.loads(raw_file["data"].attrs["scene_file"])
        trajectory = raw_file["data/demo_0"]
        actions = trajectory["action"]
        states = trajectory["state"]
        state_sizes = trajectory["state_size"]
        if len(actions) != int(row.length):
            raise RuntimeError(
                f"Episode {episode_index}: metadata has {row.length} actions but raw episode "
                f"{raw_episode_id} has {len(actions)}."
            )
        if len(states) != len(actions) + 1:
            raise RuntimeError(
                f"Episode {episode_index}: expected one more state than action, got "
                f"{len(states)} states and {len(actions)} actions."
            )

        _prepare_recorded_scene(playback, trajectory, scene_file)
        radio_name, table_name = _task_object_names(scene_file)
        radio = playback.scene.object_registry("name", radio_name, None)
        table = playback.scene.object_registry("name", table_name, None)
        if radio is None or table is None:
            raise RuntimeError(f"Could not resolve radio={radio_name!r} or table={table_name!r} in restored scene.")
        robot = playback.robots[0]
        toggle_target_sensors = _resolve_toggle_target_sensors(robot) if args.write_toggle_targets else ()

        # Raw state i is the observation immediately before action i.  A 1 ms step mirrors the
        # official playback implementation and is required for PhysX to propagate contact buffers.
        og.sim.load_state(th.as_tensor(states[0, : int(state_sizes[0])]), serialized=True)
        og.sim.step()
        initial_radio_z = float(radio.get_position_orientation()[0][2].item())
        initial_table_xy = table.get_position_orientation()[0][:2].detach().cpu().numpy().copy()
        marker_in_link = _toggle_marker_in_link_transform(radio) if args.write_toggle_targets else None

        sampled_frames = []
        grounded_events = []
        physical_states = []
        toggle_targets = []
        for frame_index in range(0, len(actions), args.sample_stride):
            state_size = int(state_sizes[frame_index])
            serialized_state = th.as_tensor(states[frame_index, :state_size])
            og.sim.load_state(serialized_state, serialized=True)
            # LeRobot RGB-D frame i is the observation from serialized state i,
            # immediately before action i. Project the marker before stepping so
            # moving wrist cameras remain exactly aligned to those stored images.
            # Isaac Sim does require one physics-only propagation before link pose
            # getters reflect a loaded state. Reload the exact state afterwards so
            # this label-only synchronization cannot alter event extraction.
            if args.write_toggle_targets:
                og.sim.step()
            toggle_target = (
                _sample_toggle_targets(toggle_target_sensors, radio, marker_in_link)
                if args.write_toggle_targets
                else None
            )
            if args.write_toggle_targets:
                og.sim.load_state(serialized_state, serialized=True)
            playback.env.step(th.as_tensor(actions[frame_index]), n_render_iterations=0)
            events, physical_state = _sample_grounded_state(
                robot,
                radio,
                table,
                initial_radio_z,
                initial_table_xy,
                args,
            )
            sampled_frames.append(frame_index)
            grounded_events.append(events)
            physical_states.append(physical_state)
            if args.write_toggle_targets:
                toggle_targets.append(toggle_target)

    event_array = np.stack(grounded_events)
    output_arrays = {
        "label_source": np.asarray(LABEL_SOURCE),
        "episode_index": np.asarray(episode_index, dtype=np.int64),
        "raw_episode_id": np.asarray(raw_episode_id, dtype=np.int64),
        "task_instance_id": np.asarray(row.task_instance_id, dtype=np.int64),
        "frame_indices": np.asarray(sampled_frames, dtype=np.int64),
        "events": event_array,
        "physical_states": np.stack(physical_states),
    }
    if args.write_toggle_targets:
        output_arrays.update(
            {
                "toggle_target_camera_names": np.asarray(TOGGLE_TARGET_CAMERA_NAMES),
                "toggle_target_normalized_pixels": np.stack(
                    [item["normalized_pixels"] for item in toggle_targets]
                ),
                "toggle_target_camera_coordinates": np.stack(
                    [item["camera_coordinates"] for item in toggle_targets]
                ),
                "toggle_target_clip_w": np.stack([item["clip_w"] for item in toggle_targets]),
                "toggle_target_in_frame": np.stack([item["in_frame"] for item in toggle_targets]),
                "toggle_target_camera_resolutions": np.stack(
                    [item["camera_resolutions"] for item in toggle_targets]
                ),
            }
        )
    temporary_path = output_path.with_suffix(".npz.tmp")
    with temporary_path.open("wb") as file:
        np.savez_compressed(file, **output_arrays)
    temporary_path.replace(output_path)
    return event_array


def main() -> None:
    args = parse_args()
    if args.sample_stride <= 0:
        raise ValueError("--sample-stride must be positive.")
    if args.episode_stride <= 0:
        raise ValueError("--episode-stride must be positive.")
    if args.episode_start_index < 0:
        raise ValueError("--episode-start-index must be non-negative.")
    gm.HEADLESS = args.headless
    # Raw playback restores all recorded object states directly. Transition rules would mutate
    # those restored states a second time and are explicitly disallowed by the playback wrapper.
    gm.ENABLE_TRANSITION_RULES = False
    seed_everything(DEFAULT_EVAL_SEED)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    metadata = _load_episode_metadata(args.dataset_root).sort_values("episode_index")
    if args.episode_indices:
        wanted = set(args.episode_indices)
        metadata = metadata[metadata["episode_index"].isin(wanted)]
        missing = sorted(wanted - set(metadata["episode_index"].astype(int)))
        if missing:
            raise ValueError(f"Unknown episode indices: {missing}")
    else:
        metadata = metadata[metadata["episode_index"] >= args.episode_start_index]
        metadata = metadata.iloc[:: args.episode_stride].iloc[: args.max_episodes]
    if metadata.empty:
        raise ValueError("No episodes selected.")

    if args.manifest_only:
        _write_manifest(args, metadata)
        logger.info("Validated exact-state grounded labels for %d episodes", len(metadata))
        og.shutdown()
        return

    pending_rows = []
    for row in metadata.itertuples(index=False):
        output_path = _episode_output_path(args.output_dir, int(row.episode_index))
        valid = _episode_file_is_valid(
            output_path,
            int(row.episode_index),
            int(row.raw_episode_id),
            require_toggle_targets=args.write_toggle_targets,
        )
        if args.overwrite or not valid:
            pending_rows.append(row)
        else:
            logger.info("Skipping completed episode %d", int(row.episode_index))

    if not pending_rows:
        _write_manifest(args, metadata)
        logger.info("All %d exact-state grounded-label files are already complete", len(metadata))
        og.shutdown()
        return

    first_raw_path = _download_raw_episode(args, int(pending_rows[0].raw_episode_id))
    with tempfile.TemporaryDirectory(prefix="radio-label-playback-") as temporary_dir:
        playback_output = str(Path(temporary_dir) / "unused_playback.hdf5")
        playback = HDF5PlaybackWrapper.create_from_hdf5(
            input_path=str(first_raw_path),
            output_path=playback_output,
            robot_obs_modalities=("proprio", "rgb") if args.write_toggle_targets else ("proprio",),
            n_render_iterations=0,
            overwrite=True,
            only_successes=False,
            include_task=False,
            include_task_obs=False,
            include_robot_control=True,
            include_contacts=True,
        )
        try:
            for position, row in enumerate(pending_rows, start=1):
                episode_index = int(row.episode_index)
                raw_episode_id = int(row.raw_episode_id)
                raw_path = first_raw_path if position == 1 else _download_raw_episode(args, raw_episode_id)
                logger.info(
                    "Extracting episode %d/%d: LeRobot %d <- raw HDF5 %d",
                    position,
                    len(pending_rows),
                    episode_index,
                    raw_episode_id,
                )
                output_path = _episode_output_path(args.output_dir, episode_index)
                event_array = _extract_episode(playback, raw_path, row, output_path, args)
                event_counts = event_array.sum(axis=0).astype(int).tolist()
                logger.info("Saved %s with event counts %s", output_path, dict(zip(EVENT_NAMES, event_counts)))
        finally:
            if playback.input_hdf5.id.valid:
                playback.input_hdf5.close()
            if playback.hdf5_file.id.valid:
                playback.hdf5_file.close()

    _write_manifest(args, metadata)
    logger.info("Completed exact-state grounded labels for %d episodes", len(metadata))
    og.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    main()
