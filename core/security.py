from datetime import datetime, timedelta, timezone

import jwt

from config import settings


def create_token(
    account_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    exp = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(account_id),
        "exp": exp,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
