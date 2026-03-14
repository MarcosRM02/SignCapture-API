from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Comprueba que la API esta viva y puede responder."""

    return {"status": "ok"}
