"""Mesh-free FK and planar odometry for policy-side robot geometry."""

import math
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from omnigibson.utils.urdfpy_utils import URDF


def _load_mesh_free_urdf(path):
    root = ET.parse(path).getroot()
    for link in root.findall("link"):
        for tag in ("visual", "collision"):
            for node in link.findall(tag):
                link.remove(node)
    with tempfile.NamedTemporaryFile(suffix=".urdf") as f:
        ET.ElementTree(root).write(f.name, encoding="utf-8", xml_declaration=True)
        return URDF.load(f.name)


class RobotKinematics:
    """URDF FK plus episode-local planar odometry.

    ``base_qvel`` is [vx, vy, wz] in the robot base frame. Joint names absent
    from ``encoders`` are held at zero, including virtual/base joints.
    """

    def __init__(self, urdf_path, camera_links=("zed_link", "left_realsense_link", "right_realsense_link")):
        self.urdf_path = Path(urdf_path)
        self.urdf = _load_mesh_free_urdf(self.urdf_path)
        self.camera_links = tuple(camera_links)
        self._odom = np.eye(4)

    @property
    def odom_from_base(self):
        return self._odom.copy()

    def step(self, encoders, base_qvel=(0.0, 0.0, 0.0), dt=0.0):
        vx, vy, wz = map(float, base_qvel)
        yaw = math.atan2(self._odom[1, 0], self._odom[0, 0])
        c, s = math.cos(yaw), math.sin(yaw)
        self._odom[0, 3] += (c * vx - s * vy) * dt
        self._odom[1, 3] += (s * vx + c * vy) * dt
        yaw += wz * dt
        self._odom[:2, :2] = ((math.cos(yaw), -math.sin(yaw)), (math.sin(yaw), math.cos(yaw)))
        cfg = {name: float(value) for name, value in encoders.items() if name in self.urdf.joint_map}
        fk = self.urdf.link_fk(cfg=cfg, use_names=True)
        return {name: self._odom @ fk[name] for name in self.camera_links if name in fk}, fk

    def odom_from_link(self, link_name, encoders):
        cfg = {name: float(value) for name, value in encoders.items() if name in self.urdf.joint_map}
        return self._odom @ self.urdf.link_fk(cfg=cfg, link=link_name)

    def odom_from_camera(self, camera_link, encoders):
        if camera_link not in self.camera_links:
            raise ValueError(f"unknown calibrated camera link: {camera_link}")
        return self.odom_from_link(camera_link, encoders)

    def curobo_base_target(self, odom_target):
        """Convert an odometry-frame target into the URDF/curobo base frame."""
        return np.linalg.inv(self._odom) @ np.asarray(odom_target, dtype=float)
