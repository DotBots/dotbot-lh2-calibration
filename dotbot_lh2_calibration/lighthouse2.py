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
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

REFERENCE_POINTS_DEFAULT = [
    [0.4, 0.6],
    [0.6, 0.6],
    [0.4, 0.4],
    [0.6, 0.4],
]
CALIBRATION_DIR = Path.home() / ".dotbot"


LH_PERIODS = [
    959000,  # mode 1
    957000,  # mode 2
    953000,  # mode 3
    949000,  # mode 4
    947000,  # mode 5
    943000,  # mode 6
    941000,  # mode 7
    939000,  # mode 8
    937000,  # mode 9
    929000,  # mode 10
    919000,  # mode 11
    911000,  # mode 12
    907000,  # mode 13
    901900,  # mode 14
    893000,  # mode 15
    887000,  # mode 16
]


@dataclass
class LH2Homography:
    """Dataclass that holds computed LH2 homography for a basestation indicated by index."""

    matrix: np.ndarray = dataclasses.field(
        default_factory=lambda: np.zeros((3, 3), dtype=np.float64)
    )


@dataclass
class LH2Counts:
    """Class that stores LH2 counts."""

    polynomial_index: int
    count1: int
    count2: int


@dataclasses.dataclass
class LH2CountsPair:
    """Pair of LH2 counts."""

    ref_counts: LH2Counts
    new_counts: LH2Counts


def calculate_camera_point(count1, count2, poly_in):
    """Calculate camera points from counts."""
    period = LH_PERIODS[poly_in]

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


def camera_points_from_counts(counts: list[LH2Counts]) -> np.ndarray:
    """Convert counts to camera points."""
    camera_points = np.zeros((len(counts), 2), dtype=np.float64)
    for index, count in enumerate(counts):
        camera_points[index] = np.asarray(
            calculate_camera_point(
                count.count1,
                count.count2,
                count.polynomial_index,
            ),
            dtype=np.float64,
        )
    return camera_points


def compute_homography_matrix(
    camera_points: np.ndarray,
    reference_points: np.ndarray,
) -> np.ndarray:
    """Compute homography matrix from camera points to reference points."""
    M, _ = cv2.findHomography(
        camera_points,
        reference_points,
        method=cv2.RANSAC,
        ransacReprojThreshold=0.001,
    )

    if M is None:
        raise ValueError("Homography computation failed.")

    return M


def homography_as_bytes(matrix: np.ndarray) -> bytes:
    """Convert homography matrix to bytes."""
    matrix_bytes = bytearray()
    try:
        for bytes_block in [
            int(n * 1e6).to_bytes(4, "little", signed=True)
            for n in matrix.ravel()
        ]:
            matrix_bytes += bytes_block
    except:
        matrix_bytes = bytearray(36)
    return matrix_bytes


class LighthouseManager:
    """Class to manage the LightHouse positionning state and workflow."""

    def __init__(self, extra_lh_num: int = 0):
        Path.mkdir(CALIBRATION_DIR, exist_ok=True)
        self.calibration_output_path = CALIBRATION_DIR / "calibration.out"
        self.extra_lh_num = extra_lh_num
        self.homographies: list[LH2Homography] = [LH2Homography()] * (
            1 + self.extra_lh_num
        )

    def _compute_reference_homography(
        self, calibration_counts: list[LH2Counts]
    ) -> LH2Homography:
        """Compute the reference calibration values and matrices."""
        # Convert reference counts to camera view points
        camera_points = camera_points_from_counts(calibration_counts)

        # Compute homography from camera points to ground plane coordinates
        homography = compute_homography_matrix(
            camera_points,
            np.array([REFERENCE_POINTS_DEFAULT], dtype=np.float64),
        )

        return LH2Homography(matrix=homography)

    def _compute_extra_calibration(
        self, counts_pairs: list[LH2CountsPair]
    ) -> LH2Homography:
        """Compute the extra lighthouse calibration values and matrices."""

        # Convert reference counts to camera points
        ref_camera_points = camera_points_from_counts(
            [pair.ref_counts for pair in counts_pairs]
        )

        # Convert to homogeneous coordinates
        zeros = np.zeros((ref_camera_points.shape[0], 1), dtype=np.float64)
        ref_camera_points = np.hstack((ref_camera_points, zeros))

        # Convert reference camera points to ground plane coordinates using reference homography
        ref_coordinates = np.matmul(
            self.homographies[0].matrix,
            ref_camera_points.T,
        )
        ref_coordinates.T[:, 2] = 0

        # Convert new camera points from new LH counts
        new_camera_points = camera_points_from_counts(
            [pair.new_counts for pair in counts_pairs]
        )

        # Convert to homogeneous coordinates
        new_camera_points = np.hstack((new_camera_points, zeros))

        # Compute homography from new camera points to ground plane coordinates
        homography = compute_homography_matrix(
            new_camera_points,
            ref_coordinates.T,
        )

        return LH2Homography(matrix=homography)

    def compute_calibration(
        self,
        calibration_counts: list[LH2Counts],
        extra_lh_counts_pairs: list[list[LH2CountsPair]],
    ) -> list[LH2Homography]:
        """Compute the calibration values and matrices."""
        self.homographies[0] = self._compute_reference_homography(
            calibration_counts
        )
        for lh_index, counts_pairs in enumerate(
            extra_lh_counts_pairs, start=1
        ):
            self.homographies[lh_index] = self._compute_extra_calibration(
                counts_pairs
            )

    def load_calibration(self) -> bytes:
        if not os.path.exists(self.calibration_output_path):
            return None
        with open(self.calibration_output_path, "rb") as calibration_file:
            homography_matrix = calibration_file.read(36)
        return homography_matrix

    def save_calibration(self) -> None:
        """Save the calibration to a file."""
        with open(self.calibration_output_path, "wb") as calibration_file:
            for index, homography in enumerate(self.homographies):
                calibration_file.write(
                    int(index).to_bytes(4, "little", signed=False)
                )
                calibration_file.write(homography_as_bytes(homography.matrix))
