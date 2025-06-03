# app/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
import redis
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.models import User, Role
from app.database import get_session
from app.schemas import TokenPayload

# ------------------------------------------------------
# Configuración de JWT y Redis
# ------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretjwtkey")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "supersecretrefreshkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# ------------------------------------------------------
# Funciones de hashing de contraseña
# ------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ------------------------------------------------------
# CRUD Básico: obtener usuario por username o email, autenticar
# ------------------------------------------------------
def get_user_by_username_or_email(session: Session, username_or_email: str) -> Optional[User]:
    statement = select(User).where((User.username == username_or_email) | (User.email == username_or_email))
    return session.exec(statement).first()

def authenticate_user(session: Session, username_or_email: str, password: str) -> Optional[User]:
    user = get_user_by_username_or_email(session, username_or_email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ------------------------------------------------------
# Creación y verificación de tokens JWT
# ------------------------------------------------------
def create_access_token(*, subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": subject, "role": role})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(*, subject: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def revoke_token_jwt(token: str):
    """
    Revoca un access token guardándolo en Redis con TTL igual al tiempo restante.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        now_ts = datetime.utcnow().timestamp()
        ttl = int(exp_timestamp - now_ts)
        if ttl > 0:
            redis_client.setex(token, ttl, "revoked")
    except jwt.PyJWTError:
        pass

def is_token_revoked(token: str) -> bool:
    """
    Comprueba si un access token ya fue revocado (está en Redis).
    """
    return redis_client.exists(token) == 1

def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(sub=payload.get("sub"), exp=payload.get("exp"), role=payload.get("role"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")


# ------------------------------------------------------
# Dependencias para FastAPI
# ------------------------------------------------------
def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    if is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    token_data = decode_access_token(token)
    user = session.get(User, int(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

def get_current_active_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requieren privilegios de administrador")
    return current_user