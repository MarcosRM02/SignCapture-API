from __future__ import annotations

import numpy as np

_EPSILON = 1e-12


def normalize_landmarks_array(landmarks: np.ndarray) -> np.ndarray:
    """Normaliza 21 landmarks 3D al rango [-1, 1]."""

    if landmarks.shape != (21, 3):
        raise ValueError(f"Forma de landmarks no soportada: {landmarks.shape}")

    normalized = np.zeros((21, 3), dtype=np.float32)

    for axis in range(3):
        coordinates = landmarks[:, axis]
        min_value = coordinates.min()
        max_value = coordinates.max()
        if max_value > min_value:
            normalized[:, axis] = (coordinates - min_value) / (max_value - min_value) * 2 - 1

    return normalized


def build_feature_vector(landmarks: np.ndarray) -> np.ndarray:
    """Replica el vector de 77 features usado durante el entrenamiento."""

    normalized_landmarks = normalize_landmarks_array(landmarks)
    flat_landmarks = normalized_landmarks.reshape(-1)
    angles = _compute_ordered_angles(normalized_landmarks)
    return np.concatenate([flat_landmarks, angles]).astype(np.float32)


def _compute_ordered_angles(landmarks: np.ndarray) -> np.ndarray:
    midpoint_59 = (landmarks[5] + landmarks[9]) / 2.0
    midpoint_913 = (landmarks[9] + landmarks[13]) / 2.0
    midpoint_1317 = (landmarks[13] + landmarks[17]) / 2.0

    return np.array(
        [
            _compute_angle_degrees(landmarks[1], landmarks[2], landmarks[3]),
            _compute_angle_degrees(landmarks[2], landmarks[3], landmarks[4]),
            _compute_angle_degrees(landmarks[5], landmarks[6], landmarks[7]),
            _compute_angle_degrees(landmarks[6], landmarks[7], landmarks[8]),
            _compute_angle_degrees(landmarks[9], landmarks[10], landmarks[11]),
            _compute_angle_degrees(landmarks[10], landmarks[11], landmarks[12]),
            _compute_angle_degrees(landmarks[13], landmarks[14], landmarks[15]),
            _compute_angle_degrees(landmarks[14], landmarks[15], landmarks[16]),
            _compute_angle_degrees(landmarks[17], landmarks[18], landmarks[19]),
            _compute_angle_degrees(landmarks[18], landmarks[19], landmarks[20]),
            _compute_angle_degrees(landmarks[1], landmarks[0], landmarks[5]),
            _compute_angle_degrees(landmarks[6], midpoint_59, landmarks[10]),
            _compute_angle_degrees(landmarks[10], midpoint_913, landmarks[14]),
            _compute_angle_degrees(landmarks[14], midpoint_1317, landmarks[18]),
        ],
        dtype=np.float32,
    )


def _compute_angle_degrees(
    point_a: np.ndarray,
    point_b: np.ndarray,
    point_c: np.ndarray,
) -> float:
    ba = point_a - point_b
    bc = point_c - point_b

    denominator = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denominator <= _EPSILON:
        return 0.0

    cosine = np.clip(np.dot(ba, bc) / denominator, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))
