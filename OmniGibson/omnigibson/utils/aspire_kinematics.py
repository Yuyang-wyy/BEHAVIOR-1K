"""CPU-only policy geometry helpers."""

import math
import tempfile
import xml.etree.ElementTree as ET

import numpy as np

from omnigibson.utils.urdfpy_utils import URDF


def _load_urdf(path):
    root = ET.parse(path).getroot()
    for link in root.findall("link"):
        for tag in ("visual", "collision"):
            for node in link.findall(tag):
                link.remove(node)
    with tempfile.NamedTemporaryFile(suffix=".urdf") as f:
        ET.ElementTree(root).write(f.name, encoding="utf-8", xml_declaration=True)
        return URDF.load(f.name)


class PlanarOdometry:
    """Episode-local planar pose from constant body-frame twists."""

    def __init__(self):
        self._odom_from_base = np.eye(4)

    @property
    def odom_from_base(self):
        return self._odom_from_base.copy()

    def update(self, base_qvel, dt):
        qvel = np.asarray(base_qvel, dtype=float)
        dt = np.asarray(dt, dtype=float)
        if qvel.shape != (3,) or dt.shape != () or not np.isfinite(qvel).all() or not np.isfinite(dt) or dt < 0:
            raise ValueError("base_qvel must be finite shape (3,), and dt must be finite and >= 0")
        vx, vy, wz = qvel
        theta = wz * dt
        if not np.isfinite(theta):
            raise ValueError("twist integration overflow")
        if abs(wz) < 1e-12:
            dx, dy = vx * dt, vy * dt
        else:
            dx = (math.sin(theta) * vx + (math.cos(theta) - 1) * vy) / wz
            dy = ((1 - math.cos(theta)) * vx + math.sin(theta) * vy) / wz
        delta = np.eye(4)
        delta[:2, :2] = ((math.cos(theta), -math.sin(theta)), (math.sin(theta), math.cos(theta)))
        delta[:2, 3] = (dx, dy)
        candidate = self._odom_from_base.copy()
        candidate[:2, :3] = (self._odom_from_base @ delta)[:2, :3]
        candidate[:2, 3] = (self._odom_from_base @ delta)[:2, 3]
        if not np.isfinite(candidate).all():
            raise ValueError("odometry integration overflow")
        self._odom_from_base = candidate
        return self.odom_from_base


class FingerGeometry:
    """Canonical R1Pro finger links relative to the physical EEF frame."""

    JOINTS = tuple(f"{arm}_gripper_finger_joint{i}" for arm in ("left", "right") for i in (1, 2))

    def __init__(self, urdf_path):
        self.urdf = _load_urdf(urdf_path)
        # USD fixed gripper_link -> eef_link calibration: (0,0,-.06), 180 deg Y.
        self._eef_from_gripper = np.diag([-1.0, 1.0, -1.0, 1.0])
        self._eef_from_gripper[2, 3] = -0.06

    def update(self, encoders):
        if not hasattr(encoders, "__getitem__"):
            raise TypeError("encoders must be a mapping")
        cfg = {name: float(encoders[name]) for name in self.JOINTS}
        if not np.isfinite(list(cfg.values())).all():
            raise ValueError("finger encoders must be finite")
        fk = self.urdf.link_fk(cfg=cfg, use_names=True)
        result = {}
        for arm in ("left", "right"):
            eef_from_base = self._eef_from_gripper @ np.linalg.inv(fk[f"{arm}_gripper_link"])
            for index in (1, 2):
                link = f"{arm}_gripper_finger_link{index}"
                result[link] = eef_from_base @ fk[link]
        return result
