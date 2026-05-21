from fastapi import HTTPException, status


def check_ai_mode(intended_provider: str = "external") -> None:
    """Raise HTTP 403 if an external AI call is attempted when it is not allowed.

    Call this at the start of any endpoint or service method that would send
    data to an external LLM provider.
    """
    from backend.src.config import get_settings  # lazy import to avoid circular

    settings = get_settings()
    if intended_provider == "external" and not settings.allow_external_ai:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "external_ai_blocked",
                "message": (
                    "External AI calls are disabled. "
                    "Set ALLOW_EXTERNAL_AI=true to enable (requires explicit opt-in)."
                ),
                "ai_mode": settings.ai_mode,
            },
        )
