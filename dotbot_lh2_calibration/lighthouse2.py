# SPDX-FileCopyrightText: 2022-present Inria
# SPDX-FileCopyrightText: 2022-present Filip Maksimovic <filip.maksimovic@inria.fr>
# SPDX-FileCopyrightText: 2022-present Alexandre Abadie <alexandre.abadie@inria.fr>
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module containing the API to convert LH2 raw data to relative positions."""

# pylint: disable=invalid-name,unspecified-encoding,no-member

import dataclasses
import math
import os
import pickle
import typing
from abc import ABC
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from dotbot_utils.protocol import PayloadFieldMetadata, Payload


REFERENCE_POINTS_DEFAULT = [
    [-0.1, 0.1],
    [0.1, 0.1],
    [-0.1, -0.1],
    [0.1, -0.1],
]
CALIBRATION_DIR = Path.home() / ".dotbot"


@dataclass
class PayloadLh2CalibrationHomography(Payload):
    """Dataclass that holds computed LH2 homography for a basestation indicated by index."""

    metadata: list[PayloadFieldMetadata] = dataclasses.field(
        default_factory=lambda: [
            PayloadFieldMetadata(name="index", disp="idx"),
            PayloadFieldMetadata(
                name="homography_matrix", disp="mat.", type_=bytes, length=36
            ),
        ]
    )
    index: int = 0
    homography_matrix: bytes = dataclasses.field(default_factory=lambda: bytearray)


def calculate_camera_point(count1, count2, poly_in):
    """Calculate camera points from counts."""
    if poly_in < 2:
        period = 959000
    if poly_in > 1:
        period = 957000

    a1 = (count1 * 8 / period) * 2 * math.pi
    a2 = (count2 * 8 / period) * 2 * math.pi

    cam_x = -math.tan(0.5 * (a1 + a2))
    if count1 < count2:
        cam_y = -math.sin(a2 / 2 - a1 / 2 - 60 * math.pi / 180) / math.tan(
            math.pi / 6
        )
    else:
        cam_y = -math.sin(a1 / 2 - a2 / 2 - 60 * math.pi / 180) / math.tan(
            math.pi / 6
        )

    return cam_x, cam_y


def _unitize(x_in, y_in):
    magnitude = np.sqrt(x_in**2 + y_in**2)
    return x_in / magnitude, y_in / magnitude


@dataclass
class LH2Location:
    """Class that stores LH2 counts."""

    count1: int
    polynomial_index1: int
    count2: int
    polynomial_index2: int


@dataclass
class CalibrationData:
    """Class that stores calibration data."""

    zeta: float
    random_rodriguez: np.array
    normal: np.array
    m: np.array


class LighthouseManager:
    """Class to manage the LightHouse positionning state and workflow."""

    def __init__(self):
        Path.mkdir(CALIBRATION_DIR, exist_ok=True)
        self.calibration_output_path = CALIBRATION_DIR / "calibration.out"
        self.calibration_points = np.zeros(
            (2, len(REFERENCE_POINTS_DEFAULT), 2), dtype=np.float64
        )
        self.calibration_points_available = [False] * len(
            REFERENCE_POINTS_DEFAULT
        )
        self.last_location = None

    def add_calibration_point(self, index) -> bool:
        """Register a new camera points for calibration."""
        if self.last_location is None:
            return False

        self.calibration_points_available[index] = True
        self.calibration_points[0][index] = np.asarray(
            calculate_camera_point(
                self.last_location.count1,
                self.last_location.count2,
                self.last_location.polynomial_index1,
            ),
            dtype=np.float64,
        )
        self.calibration_points[1][index] = np.asarray(
            calculate_camera_point(
                self.last_location.count1,
                self.last_location.count2,
                self.last_location.polynomial_index2,
            ),
            dtype=np.float64,
        )
        self.last_location: LH2Location = None
        return True

    def load_calibration(self) -> PayloadLh2CalibrationHomography:
        if not os.path.exists(self.calibration_output_path):
            self.logger.info("No calibration file found")
            return None
        with open(self.calibration_output_path, "rb") as calibration_file:
            calibration = pickle.load(calibration_file)
        return calibration

    def compute_calibration(self) -> bool:  # pylint: disable=too-many-locals
        """Compute the calibration values and matrices."""
        camera_points = [[], []]
        for data in self.calibration_points[0]:
            camera_points[0].append(data)
        for data in self.calibration_points[1]:
            camera_points[1].append(data)
        camera_points_arr = np.asarray(camera_points, dtype=np.float64)
        homography_mat = cv2.findHomography(
            camera_points_arr[0][0 : len(camera_points[0])][:],
            camera_points_arr[1][0 : len(camera_points[1])][:],
            method=cv2.RANSAC,
            ransacReprojThreshold=0.001,
        )[0]
        
        if homography_mat is None:
            raise ValueError("Homography matrix could not be computed.")

        _, S, V = np.linalg.svd(homography_mat)
        V = V.T

        s1 = S[0] / S[1]
        s3 = S[2] / S[1]
        zeta = s1 - s3
        a1 = np.sqrt(1 - s3**2)
        b1 = np.sqrt(s1**2 - 1)
        a, b = _unitize(a1, b1)
        v1 = np.array(V[:, 0])
        v3 = np.array(V[:, 2])
        n = b * v1 + a * v3

        if n[2] < 0:
            n = -n

        random_rodriguez = np.array(
            [
                [
                    -n[1] / np.sqrt(n[0] * n[0] + n[1] * n[1]),
                    n[0] / np.sqrt(n[0] * n[0] + n[1] * n[1]),
                    0,
                ],
                [
                    n[0] * n[2] / np.sqrt(n[0] * n[0] + n[1] * n[1]),
                    n[1] * n[2] / np.sqrt(n[0] * n[0] + n[1] * n[1]),
                    -np.sqrt(n[0] * n[0] + n[1] * n[1]),
                ],
                [-n[0], -n[1], -n[2]],
            ]
        )

        pts_cam_new = np.hstack(
            (camera_points_arr[1], np.ones((len(camera_points_arr[1]), 1)))
        )
        scales = (1 / zeta) / np.matmul(n, pts_cam_new.T)
        scales_matrix = np.vstack((scales, scales, scales))
        final_points = scales_matrix * pts_cam_new.T
        final_points = final_points.T

        temporary_numpy_trash_heap = (
            np.array([REFERENCE_POINTS_DEFAULT], dtype=np.float64) + 0.5
        )
        temporary_numpy_trash_heap_pt2 = temporary_numpy_trash_heap.squeeze()

        M, _ = cv2.findHomography(
            camera_points_arr[0],
            temporary_numpy_trash_heap_pt2,
            method=cv2.RANSAC,
            ransacReprojThreshold=0.001,
        )

        calibration_data = CalibrationData(zeta, random_rodriguez, n, M)
        matrix_bytes = bytearray()
        for bytes_block in [
            int(n * 1e6).to_bytes(4, "little", signed=True)
            for n in calibration_data.m.ravel()
        ]:
            matrix_bytes += bytes_block

        # Prepare homography matrix and send it to the robot
        calibration = PayloadLh2CalibrationHomography(
            index=0,
            homography_matrix=matrix_bytes,
        )

        # Store calibration data as pickle for later reload
        with open(self.calibration_output_path, "wb") as output_file:
            pickle.dump(calibration, output_file)
