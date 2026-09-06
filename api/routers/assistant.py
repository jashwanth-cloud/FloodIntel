from fastapi import APIRouter, HTTPException

from api.schemas.assistant import AssistantRequest
from api.services.assistant_service import SUPPORTED_LANGUAGES, ask_assistant


router = APIRouter(
    prefix="/api/assistant",
    tags=["AI Assistant"],
)


@router.post("/")
async def assistant(request: AssistantRequest):
    language = request.language.lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Unsupported language.",
                "supported_languages": SUPPORTED_LANGUAGES,
            },
        )

    try:
        return ask_assistant(
            message=request.message.strip(),
            language=language,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc