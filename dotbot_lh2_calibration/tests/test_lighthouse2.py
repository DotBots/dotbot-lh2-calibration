"""Test module for the LH2 calibration."""

import pytest

from dotbot_lh2_calibration.lighthouse2 import calculate_camera_point


def test_camera_points():
    assert calculate_camera_point(49341, 85887, 1) == pytest.approx(
        (-0.43435315273542, 0.1512338330873567)
    )
