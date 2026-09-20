"""Mesh-free FK and planar odometry for policy-side robot geometry."""

import math
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from omnigibson.utils.urdfpy_utils import URDF

_VIRTUAL_BASE_JOINTS = frozenset(
    {
        "base_footprint_x_joint",
        "base_footprint_y_joint",
        "base_footprint_z_joint",
        "base_footprint_rx_joint",
        "base_footprint_ry_joint",
        "base_footprint_rz_joint",
    }
)


def _load_mesh_free_urdf(path):
    root = ET.parse(path).getroot()
    for link in root.findall("link"):
        for tag in ("visual", "collision"):
            for node in link.findall(tag):
                link.remove(node)
    with tempfile.NamedTemporaryFile(suffix=".urdf") as f:
        ET.ElementTree(root).write(f.name, encoding="utf-8", xml_declaration=True)
        return URDF.load(f.name)


def _quat_matrix(wxyz):
    w, x, y, z = np.asarray(wxyz, dtype=float)
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def _load_usd_camera_extrinsics(path, links):
    text = Path(path).read_text()
    extrinsics = {}
    for link in links:
        match = re.search(
            rf'def Xform "{re.escape(link)}".*?(?=\n\s*def Xform |\Z)', text, re.DOTALL
        )
        if match is None:
            raise ValueError(f"USD link not found: {link}")
        camera = re.search(
            r'def Camera "Camera".*?xformOp:orient = \(([^)]+)\).*?'
            r'xformOp:translate = \(([^)]+)\)',
            match.group(),
            re.DOTALL,
        )
        if camera is None:
            raise ValueError(f"USD camera child not found: {link}/Camera")
        orient = [float(v.strip()) for v in camera.group(1).split(",")]
        translate = [float(v.strip()) for v in camera.group(2).split(",")]
        transform = np.eye(4)
        transform[:3, :3] = _quat_matrix(orient)
        transform[:3, 3] = translate
        extrinsics[link] = transform
    return extrinsics


class RobotKinematics:
    """URDF FK plus episode-local planar odometry.

    ``base_qvel`` is [vx, vy, wz] in the robot base frame. Joint names absent
    from ``encoders`` are held at zero, including virtual/base joints.
    """

    def __init__(self, urdf_path, usd_path=None, camera_links=("zed_link", "left_realsense_link", "right_realsense_link")):
        self.urdf_path = Path(urdf_path)
        self.urdf = _load_mesh_free_urdf(self.urdf_path)
        self.camera_links = tuple(camera_links)
        if usd_path is None:
            usd_path = self.urdf_path.parent.parent / "usd" / "r1pro.usda"
        self.camera_extrinsics = _load_usd_camera_extrinsics(usd_path, self.camera_links)
        self._odom = np.eye(4)

    @property
    def odom_from_base(self):
        return self._odom.copy()

    def step(self, encoders, base_qvel=(0.0, 0.0, 0.0), dt=0.0):
        vx, vy, wz = map(float, base_qvel)
        if not np.isfinite((vx, vy, wz)).all() or not np.isfinite(dt) or dt < 0:
            raise ValueError("base_qvel and dt must be finite, with dt >= 0")
        yaw = math.atan2(self._odom[1, 0], self._odom[0, 0])
        theta = wz * dt
        if abs(wz) < 1e-12:
            dx, dy = vx * dt, vy * dt
        else:
            dx = (math.sin(theta) * vx + (math.cos(theta) - 1) * vy) / wz
            dy = ((1 - math.cos(theta)) * vx + math.sin(theta) * vy) / wz
        c, s = math.cos(yaw), math.sin(yaw)
        self._odom[0, 3] += c * dx - s * dy
        self._odom[1, 3] += s * dx + c * dy
        yaw += theta
        self._odom[:2, :2] = ((math.cos(yaw), -math.sin(yaw)), (math.sin(yaw), math.cos(yaw)))
        cfg = self._cfg(encoders)
        fk = self.urdf.link_fk(cfg=cfg, use_names=True)
        return {name: self._odom @ fk[name] @ self.camera_extrinsics[name] for name in self.camera_links if name in fk}, fk

    def _cfg(self, encoders):
        if not hasattr(encoders, "items"):
            raise TypeError("encoders must be a joint-name mapping")
        cfg = {}
        for name, value in encoders.items():
            if name in _VIRTUAL_BASE_JOINTS or name not in self.urdf.joint_map:
                continue
            value = float(value)
            if not np.isfinite(value):
                raise ValueError(f"non-finite encoder value: {name}")
            cfg[name] = value
        return cfg

    def odom_from_link(self, link_name, encoders):
        cfg = self._cfg(encoders)
        return self._odom @ self.urdf.link_fk(cfg=cfg, link=link_name)

    def odom_from_camera(self, camera_link, encoders):
        if camera_link not in self.camera_links:
            raise ValueError(f"unknown calibrated camera link: {camera_link}")
        return self.odom_from_link(camera_link, encoders) @ self.camera_extrinsics[camera_link]

    def curobo_base_target(self, odom_target):
        """Convert an odometry-frame target into the URDF/curobo base frame."""
        return np.linalg.inv(self._odom) @ np.asarray(odom_target, dtype=float)
