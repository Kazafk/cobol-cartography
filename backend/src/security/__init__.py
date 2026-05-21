from fastapi import HTTPException
from ..config import Settings


def check_ai_mode(intended_provider: str, settings: Settings) -> None:
    """Raise HTTP 403 if an external AI call is attempted when it is not allowed."""
    if intended_provider == "external" and not settings.allow_external_ai:
        raise HTTPException(
            status_code=403,
            detail=(
                "External AI calls are disabled. "
                "Set ALLOW_EXTERNAL_AI=true and confirm at session start."
            ),
        )
