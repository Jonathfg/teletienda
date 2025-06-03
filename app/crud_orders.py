# app/crud_orders.py

from sqlmodel import Session, select
from fastapi import HTTPException, status
from typing import List
from app.models import Order, OrderItem, User
from app.schemas import OrderCreate, OrderItemCreate, OrderRead, OrderItemRead, OrderUpdateState
from app.utils import fetch_product
import asyncio

def create_order(session: Session, user: User, order_in: OrderCreate) -> Order:
    order = Order(user_id=user.id)
    session.add(order)
    session.flush()  # para obtener order.id antes de commit
    for item_in in order_in.items:
        item = OrderItem(
            order_id=order.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        session.add(item)
    session.commit()
    session.refresh(order)
    return order

def get_order(session: Session, order_id: int, user: User) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    # Si no es admin y el pedido no pertenece al user, prohibir
    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    return order

def get_orders_by_user(session: Session, user: User) -> List[Order]:
    statement = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    return session.exec(statement).all()

def get_all_orders(session: Session) -> List[Order]:
    statement = select(Order).order_by(Order.created_at.desc())
    return session.exec(statement).all()

def update_order_state(session: Session, order_id: int, state_in: OrderUpdateState) -> Order:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    order.state = state_in.state
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

async def enrich_order(order: Order) -> OrderRead:
    """
    Convierte un objeto Order (modelo) en OrderRead, consultando DummyJSON para cada item.
    """
    items_read = []
    total = 0.0
    # Para cada item guardado, pedimos datos de producto a DummyJSON
    for item in order.items:
        product = await fetch_product(item.product_id)
        subtotal = product.price * item.quantity
        total += subtotal
        items_read.append(OrderItemRead(
            id=item.id,
            product=product,
            quantity=item.quantity
        ))
    order_read = OrderRead(
        id=order.id,
        user_id=order.user_id,
        created_at=order.created_at,
        state=order.state,
        items=items_read,
        total_amount=total
    )
    return order_read

async def enrich_orders_list(orders: List[Order]) -> List[OrderRead]:
    """
    Dado un listado de Orders, lanza concurrentemente las enriquecidas.
    """
    tasks = [enrich_order(order) for order in orders]
    return await asyncio.gather(*tasks)