from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.schemas.user import AccountCreate, AccountLogin
from core.security import create_token
from database.models import Account
from dependencies import get_session, password_hasher, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])


def authenticate_account(email: str, password: str, session: Session) -> Account | None:
    account = session.query(Account).filter(Account.email == email).first()

    if not account:
        return None

    if not password_hasher.verify(password, account.hashed_password):
        return None

    return account


@router.post("/register")
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


@router.post("/login")
def login(
    credentials: AccountLogin,
    session: Session = Depends(get_session),
):
    account = authenticate_account(
        credentials.email,
        credentials.password,
        session,
    )

    if not account:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha incorretos",
        )

    if not account.is_active:
        raise HTTPException(
            status_code=403,
            detail="Conta desativada",
        )

    access_token = create_token(account.id)

    refresh_token = create_token(
        account.id,
        timedelta(days=7),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login-oauth2")
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    account = authenticate_account(
        form_data.username,
        form_data.password,
        session,
    )

    if not account:
        raise HTTPException(
            status_code=401,
            detail="Email ou senha incorretos",
        )

    if not account.is_active:
        raise HTTPException(
            status_code=403,
            detail="Conta desativada",
        )

    access_token = create_token(account.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/refresh")
def refresh_access_token(
    account: Account = Depends(verify_token),
):
    access_token = create_token(account.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_current_account(
    account: Account = Depends(verify_token),
):
    return {
        "id": account.id,
        "name": account.name,
        "email": account.email,
        "is_active": account.is_active,
    }
