# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta

from app.database import get_session
from app.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    revoke_token_jwt,
    decode_refresh_token,
    oauth2_scheme,  # <- lo importamos aquí
)
from app.schemas import Token, TokenRefresh

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    Endpoint de login: genera access token y refresh token
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/token/refresh", response_model=Token)
def refresh_access_token(token_in: TokenRefresh):
    """
    Renueva el access token usando un refresh token
    """
    user_id = decode_refresh_token(token_in.refresh_token)
    new_access = create_access_token(subject=user_id, role="cliente")
    new_refresh = create_refresh_token(subject=user_id)
    return {"access_token": new_access, "refresh_token": new_refresh}


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),  # <- aquí usamos oauth2_scheme
):
    """
    Revoca el access token actual (se pasa como Bearer)
    """
    revoke_token_jwt(token)
    return {"msg": "Sesión cerrada correctamente"}