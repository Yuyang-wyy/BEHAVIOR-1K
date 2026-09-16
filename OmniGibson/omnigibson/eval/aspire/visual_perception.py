"""ASPIRE SAM3 wire protocol and RGB-D geometry; no simulator imports."""

from __future__ import annotations

import base64
import io
from urllib.parse import urlparse

import numpy as np
import requests
from PIL import Image


class PerceptionUnavailable(RuntimeError):
    pass


class Sam3Client:
    def __init__(self, url: str = "http://127.0.0.1:8114", timeout: float = 90.0):
        if urlparse(url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("The perception service must be loopback-only")
        self.url = url.rstrip("/")
        self.timeout = timeout

    def segment(self, rgb, text_prompt: str):
        rgb = np.asarray(rgb)
        if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError("SAM3 expects an HxWx3 uint8 RGB image")
        stream = io.BytesIO()
        Image.fromarray(rgb).save(stream, format="PNG")
        try:
            response = requests.post(
                f"{self.url}/segment",
                json={"image_base64": base64.b64encode(stream.getvalue()).decode("ascii"),
                      "text_prompt": text_prompt},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise PerceptionUnavailable(f"SAM3 unavailable at {self.url}: {error}") from error
        results = []
        for item in payload["results"]:
            if tuple(item["shape"]) != rgb.shape[:2]:
                raise ValueError("SAM3 mask resolution differs from the RGB image")
            mask = np.frombuffer(base64.b64decode(item["mask_base64"], validate=True), dtype=np.uint8)
            mask = mask.reshape(rgb.shape[:2]).astype(bool)
            score = float(item["score"])
            box = np.asarray(item["box"], dtype=float)
            if not np.isfinite(score) or box.shape != (4,) or not np.isfinite(box).all():
                raise ValueError("Malformed SAM3 score or box")
            results.append({"mask": mask, "score": score, "box": box.tolist(), "label": text_prompt})
        return sorted(results, key=lambda item: item["score"], reverse=True)


class ContactGraspNetClient:
    """Call the existing ASPIRE service; do not load weights into the simulator."""

    def __init__(self, url="http://127.0.0.1:8115", timeout=90):
        if urlparse(url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("The grasp service must be loopback-only")
        self.url, self.timeout = url.rstrip("/"), timeout

    def plan(self, depth, intrinsics, mask):
        depth = np.asarray(depth, dtype=np.float32)
        intrinsics = np.asarray(intrinsics, dtype=np.float32)
        mask = np.asarray(mask, dtype=bool)
        if depth.ndim != 2 or mask.shape != depth.shape or intrinsics.shape != (3, 3):
            raise ValueError("GraspNet expects matching HxW depth/mask and 3x3 intrinsics")
        if not np.isfinite(intrinsics).all() or intrinsics[0, 0] <= 0 or intrinsics[1, 1] <= 0:
            raise ValueError("Invalid GraspNet intrinsics")
        valid = np.isfinite(depth) & (depth > .2) & (depth < 3)
        if np.count_nonzero(mask & valid) < 20:
            raise ValueError("Too few valid masked grasp pixels")

        def encode(array):
            stream = io.BytesIO()
            np.save(stream, array, allow_pickle=False)
            return base64.b64encode(stream.getvalue()).decode("ascii")

        request = {
            "depth_base64": encode(np.where(valid, depth, 0)), "cam_K_base64": encode(intrinsics),
            "segmap_base64": encode((mask & valid).astype(np.uint8)), "segmap_id": 1,
            "filter_grasps": False, "z_range": [.2, 3.0], "forward_passes": 1,
            "max_retries": 7,
        }
        for attempt in range(3):
            try:
                response = requests.post(f"{self.url}/plan", timeout=self.timeout, json=request)
                response.raise_for_status()
                payload = response.json()
                break
            except (requests.RequestException, ValueError) as error:
                if attempt == 2:
                    raise PerceptionUnavailable(
                        f"Contact-GraspNet unavailable at {self.url}: {error}") from error
        arrays = [np.load(io.BytesIO(base64.b64decode(payload[key], validate=True)), allow_pickle=False)
                  for key in ("grasps_base64", "scores_base64", "contact_pts_base64")]
        grasps, scores, contacts = arrays
        if grasps.size == scores.size == contacts.size == 0:
            return np.empty((0, 4, 4)), np.empty(0), np.empty((0, 3))
        count = len(grasps)
        if grasps.shape != (count, 4, 4) or scores.shape != (count,) or contacts.shape != (count, 3):
            raise ValueError("Malformed Contact-GraspNet array shapes")
        if not all(np.isfinite(array).all() for array in arrays):
            raise ValueError("Nonfinite Contact-GraspNet result")
        rotation = grasps[:, :3, :3]
        if not np.allclose(rotation.transpose(0, 2, 1) @ rotation, np.eye(3), atol=.001) or not np.allclose(np.linalg.det(rotation), 1, atol=.001):
            raise ValueError("Contact-GraspNet returned invalid rotations")
        if not np.allclose(grasps[:, 3], [0, 0, 0, 1]):
            raise ValueError("Contact-GraspNet returned invalid homogeneous poses")
        return grasps, scores, contacts


def contact_grasps_to_eef(grasps, world_from_camera, fingertip_length):
    """Contact-GraspNet CV/panda frame -> own EEF (+Z approach, +Y jaw axis)."""
    world_from_cv = np.asarray(world_from_camera) @ np.diag([1, -1, -1, 1])
    world_grasps = world_from_cv @ grasps
    # The model's build_6d_grasp uses a .1034m hand-to-jaw baseline along local Z.
    world_grasps[:, :3, 3] += world_grasps[:, :3, 2] * (.1034 - fingertip_length + .015)
    world_grasps[:, :3, :3] = world_grasps[:, :3, :3] @ np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    pregrasps = world_grasps.copy()
    pregrasps[:, :3, 3] -= world_grasps[:, :3, 2] * .12
    return pregrasps, world_grasps


def mask_to_world_points(mask, depth, intrinsics, world_from_camera):
    """Backproject image-plane depth; camera pose uses OpenGL (+Y up, -Z forward)."""
    depth = np.asarray(depth)
    if depth.ndim == 3 and depth.shape[-1] == 1:
        depth = depth[..., 0]
    mask = np.asarray(mask, dtype=bool)
    k = np.asarray(intrinsics, dtype=float)
    transform = np.asarray(world_from_camera, dtype=float)
    if depth.ndim != 2 or mask.shape != depth.shape:
        raise ValueError("Mask and depth must have identical HxW shapes")
    if k.shape != (3, 3) or transform.shape != (4, 4):
        raise ValueError("Expected 3x3 intrinsics and 4x4 camera transform")
    if not np.isfinite(k).all() or not np.isfinite(transform).all() or k[0, 0] <= 0 or k[1, 1] <= 0:
        raise ValueError("Invalid camera calibration")
    y, x = np.where(mask & np.isfinite(depth) & (depth > 0) & (depth < 10))
    z = depth[y, x]
    rays = np.linalg.solve(k, np.stack((x, y, np.ones_like(x))).astype(float))
    camera_points = (rays * z).T * np.array([1.0, -1.0, -1.0])
    return camera_points @ transform[:3, :3].T + transform[:3, 3]


def observed_box(points):
    """Upright PCA box fitted to visible points, not a ground-truth object frame."""
    points = np.asarray(points, dtype=float)
    points = points[np.isfinite(points).all(axis=1)]
    if len(points) < 20:
        raise ValueError("Too few valid object depth pixels")
    center = np.median(points, axis=0)
    distances = np.linalg.norm(points - center, axis=1)
    points = points[distances <= np.percentile(distances, 98)]
    _, vectors = np.linalg.eigh(np.cov(points[:, :2].T))
    axis = vectors[:, -1]
    if axis[0] < 0:
        axis = -axis
    rotation = np.array([[axis[0], -axis[1], 0], [axis[1], axis[0], 0], [0, 0, 1]])
    local = points @ rotation
    low, high = np.percentile(local, [1, 99], axis=0)
    return (low + high) / 2 @ rotation.T, rotation, high - low, points
