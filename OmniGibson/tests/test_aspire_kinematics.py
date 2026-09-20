from pathlib import Path

import numpy as np

from omnigibson.utils.aspire_kinematics import FingerGeometry, PlanarOdometry


ASSET = Path(__file__).parents[2] / "datasets/omnigibson-robot-assets/models/r1pro/urdf/r1pro.urdf"


def test_exact_body_twist_and_validation():
    odom = PlanarOdometry()
    np.testing.assert_allclose(odom.update([1, 0, 1], np.pi / 2)[:2, 3], [1, 1], atol=1e-12)
    np.testing.assert_allclose(PlanarOdometry().update([1, 2, 0], 1)[:2, 3], [1, 2])
    odom = PlanarOdometry()
    odom.update([0, 0, 1], np.pi / 2)
    np.testing.assert_allclose(odom.update([1, 0, 0], 1)[:2, 3], [0, 1], atol=1e-12)
    for qvel, dt in [([0, 0], 1), ([np.nan, 0, 0], 1), ([0, 0, 0], -1), ([0, 0, 0], np.nan)]:
        try:
            odom.update(qvel, dt)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid twist accepted")


def test_finger_fk_and_virtual_base_is_ignored():
    geometry = FingerGeometry(ASSET)
    encoders = {name: 0.025 for name in geometry.JOINTS}
    encoders["base_footprint_x_joint"] = np.nan
    poses = geometry.update(encoders)
    expected = np.diag([-1.0, 1.0, -1.0, 1.0])
    expected[2, 3] = -0.02311
    expected[0, 3], expected[1, 3] = 8.8709e-5, 0.038453
    np.testing.assert_allclose(poses["left_gripper_finger_link1"], expected, atol=1e-12)
