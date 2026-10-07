from collections.abc import Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from config import settings
from database.connection import SessionLocal
from database.models import Account

password_hasher = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-oauth2")


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_token(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),  # noqa: B008
) -> Account:
    payload = decode_token(token)

    account_id = payload.get("sub")

    if not account_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        account_id = int(account_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")

    account = session.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=401, detail="Conta inválida")

    if not account.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    return account
