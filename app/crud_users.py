# app/crud_users.py

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.models import User, Role
from app.schemas import UserCreate, UserUpdate
from app.auth import get_password_hash


def create_user(session: Session, user_in: UserCreate, role: Role = Role.cliente) -> User:
    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=role
    )
    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario o email ya existente"
        )
    return user


def get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user


def get_users(session: Session, skip: int = 0, limit: int = 50) -> list[User]:
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()


def update_user(session: Session, user_id: int, user_update: UserUpdate) -> User:
    user = get_user(session, user_id)
    if user_update.email:
        user.email = user_update.email
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    if user_update.role:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: int):
    user = get_user(session, user_id)
    session.delete(user)
    session.commit()
    return {"message": "Usuario eliminado"}