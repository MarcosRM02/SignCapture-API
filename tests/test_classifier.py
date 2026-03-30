import numpy as np

from app.core.config import Settings
from app.models.inference import LandmarkPoint
from app.services.classifier import GestureClassifierService
from app.services.media import ExtractedFrameLandmarks


class FakeModel:
    classes_ = np.array([0, 1, 2])

    def predict_proba(self, feature_matrix: np.ndarray) -> np.ndarray:
        assert feature_matrix.shape[1] == 77
        return np.array([[0.1, 0.8, 0.1]], dtype=np.float32)


def test_predict_returns_letter_and_feedback(monkeypatch) -> None:
    service = GestureClassifierService(
        settings=Settings(model_class_labels_csv="A,B,C"),
    )
    monkeypatch.setattr(service, "_load_model", lambda: FakeModel())

    result = service.predict([_build_frame()])

    assert result.prediction.label == "B"
    assert result.prediction.top_candidates[0].label == "B"
    assert result.feedback.level in {"success", "info"}
    assert result.feedback.tips


def test_predict_without_hand_returns_error_feedback() -> None:
    service = GestureClassifierService(
        settings=Settings(model_class_labels_csv="A,B,C"),
    )

    result = service.predict([])

    assert result.prediction.label == "sin_deteccion"
    assert result.prediction.confidence == 0.0
    assert result.feedback.level == "error"


def _build_frame() -> ExtractedFrameLandmarks:
    landmarks = [
        LandmarkPoint(
            x=0.30 + (index % 5) * 0.06,
            y=0.20 + (index // 5) * 0.08,
            z=-0.10 + index * 0.01,
        )
        for index in range(21)
    ]
    return ExtractedFrameLandmarks(frame_index=0, landmarks=landmarks)
