# app/routers/users.py

from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from typing import List

from app.schemas import UserCreate, UserRead, UserUpdate
from app.crud_users import create_user, get_user, get_users, update_user, delete_user
from app.database import get_session
from app.auth import get_current_active_user, get_current_active_admin

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    # Sólo un ADMIN podrá crear usuarios distintos a él (o cambiar rol). 
    current_admin=Depends(get_current_active_admin)
):
    """
    Registro de nuevo usuario (rol por defecto: cliente). 
    Sólo ADMIN puede crear nuevos usuarios.
    """
    return create_user(session, user_in)

@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_active_admin)
):
    """
    Obtener datos de un usuario (sólo admin)
    """
    return get_user(session, user_id)

@router.get("/", response_model=List[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_active_admin)
):
    """
    Listar usuarios (sólo admin)
    """
    return get_users(session, skip, limit)

@router.patch("/{user_id}", response_model=UserRead)
def modify_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_active_admin)
):
    """
    Actualizar datos de usuario (sólo admin)
    """
    return update_user(session, user_id, user_update)

@router.delete("/{user_id}")
def remove_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_admin=Depends(get_current_active_admin)
):
    """
    Eliminar usuario (sólo admin)
    """
    return delete_user(session, user_id)