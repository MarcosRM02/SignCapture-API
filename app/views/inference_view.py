from app.models.inference import InferenceResponse


def build_inference_response(payload: InferenceResponse) -> dict:
    """Serializa la respuesta de inferencia a un diccionario JSON-friendly."""

    return payload.model_dump(mode="json")
