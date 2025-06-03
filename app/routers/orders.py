from fastapi import APIRouter, Depends, status
from typing import List
from sqlmodel import Session
from app.schemas import OrderCreate, OrderRead, OrderUpdateState
from app.crud_orders import create_order, get_order, get_orders_by_user, get_all_orders, update_order_state, enrich_order, enrich_orders_list
from app.database import get_session
from app.auth import get_current_active_user, get_current_active_admin
import asyncio

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_new_order(
    order_in: OrderCreate,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_active_user)
):
    """
    Crea un pedido para el usuario autenticado.
    """
    order = create_order(session, current_user, order_in)
    enriched = await enrich_order(order)
    return enriched

@router.get("/", response_model=List[OrderRead])
async def list_user_orders(
    session: Session = Depends(get_session),
    current_user=Depends(get_current_active_user)
):
    """
    Lista todos los pedidos del usuario autenticado.
    """
    orders = get_orders_by_user(session, current_user)
    enriched = await enrich_orders_list(orders)
    return enriched

@router.get("/all", response_model=List[OrderRead], dependencies=[Depends(get_current_active_admin)])
async def list_all_orders(session: Session = Depends(get_session)):
    """
    (Admin) Lista todos los pedidos de todos los usuarios.
    """
    orders = get_all_orders(session)
    enriched = await enrich_orders_list(orders)
    return enriched

@router.get("/{order_id}", response_model=OrderRead)
async def get_single_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_active_user)
):
    """
    Obtiene un pedido por ID (si admin puede cualquiera, si cliente sólo el suyo).
    """
    order = get_order(session, order_id, current_user)
    enriched = await enrich_order(order)
    return enriched

@router.patch("/{order_id}/state", response_model=OrderRead, dependencies=[Depends(get_current_active_admin)])
async def change_order_state(
    order_id: int,
    state_in: OrderUpdateState,
    session: Session = Depends(get_session)
):
    """
    (Admin) Cambia el estado de un pedido.
    """
    order = update_order_state(session, order_id, state_in)
    enriched = await enrich_order(order)
    return enriched