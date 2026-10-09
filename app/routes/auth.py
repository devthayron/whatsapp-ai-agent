from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.responses import (
    ErrorResponse,
    MeResponse,
    MessageResponse,
    TokenResponse,
)
from app.schemas.user import AccountCreate, AccountLogin
from config import settings
from core.security import create_token
from database.models import Account
from dependencies import (
    REFRESH_COOKIE,
    get_session,
    password_hasher,
    verify_refresh_token,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# O cookie só é enviado pelo navegador para rotas /auth/*
REFRESH_COOKIE_PATH = "/auth"

UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Não autenticado"}}
INACTIVE = {403: {"model": ErrorResponse, "description": "Conta desativada"}}


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN or None,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


def authenticate_account(email: str, password: str, session: Session) -> Account | None:
    account = session.query(Account).filter(Account.email == email).first()

    if not account:
        return None

    if not password_hasher.verify(password, account.hashed_password):
        return None

    return account


@router.post(
    "/register",
    response_model=MessageResponse,
    summary="Cria uma conta",
    responses={400: {"model": ErrorResponse, "description": "Email já cadastrado"}},
)
def register(account: AccountCreate, session: Session = Depends(get_session)):  # noqa: B008
    existing_account = (
        session.query(Account).filter(Account.email == account.email).first()
    )

    if existing_account:
        raise HTTPException(
            status_code=400, detail="Já existe uma conta com esse email"
        )

    hashed_password = password_hasher.hash(account.password)

    new_account = Account(
        name=account.name, email=account.email, hashed_password=hashed_password
    )

    session.add(new_account)
    session.commit()
    session.refresh(new_account)

    return {
        "message": "Conta criada com sucesso",
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login (access token no corpo, refresh token em cookie HttpOnly)",
    responses={**UNAUTHORIZED, **INACTIVE},
)
def login(
    credentials: AccountLogin,
    response: Response,
    session: Session = Depends(get_session),  # noqa: B008
):
    """Retorna o access token no corpo e grava o refresh token em cookie HttpOnly."""
    account = authenticate_account(credentials.email, credentials.password, session)

    if not account:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not account.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    access_token = create_token(account.id, token_type="access")

    refresh_token = create_token(
        account.id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )

    set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/login-oauth2",
    response_model=TokenResponse,
    summary="Login do botão Authorize do Swagger (não grava cookie)",
    responses={**UNAUTHORIZED, **INACTIVE},
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
):
    """Login do botão Authorize do Swagger. Não grava cookie."""
    account = authenticate_account(form_data.username, form_data.password, session)

    if not account:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not account.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    access_token = create_token(account.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Novo access token a partir do cookie do refresh token",
    responses={**UNAUTHORIZED, **INACTIVE},
)
def refresh_access_token(
    account: Account = Depends(verify_refresh_token),  # noqa: B008
):
    """Lê o refresh token do cookie e devolve um novo access token."""
    access_token = create_token(account.id, token_type="access")

    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Apaga o cookie do refresh token",
)
def logout(response: Response):
    """Remove o cookie do refresh token. Não revoga o token no servidor."""
    clear_refresh_cookie(response)

    return {"message": "Sessão encerrada"}


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Dados da conta autenticada",
    responses={**UNAUTHORIZED, **INACTIVE},
)
def get_current_account(
    account: Account = Depends(verify_token),  # noqa: B008
):
    return {
        "id": account.id,
        "name": account.name,
        "email": account.email,
        "is_active": account.is_active,
    }
