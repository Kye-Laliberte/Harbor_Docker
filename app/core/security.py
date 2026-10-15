from secrets import compare_digest
import logging
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    configured_key = settings.API_KEY
    if not configured_key:
        logging.exception("API key is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key is not configured",
        )

    if api_key is None or not compare_digest(
        api_key.encode("utf-8"),
        configured_key.encode("utf-8"),
    ):

        logging.exception("Invalid or missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )