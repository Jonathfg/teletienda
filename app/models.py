from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import datetime

class Role(str, Enum):
    cliente = "cliente"
    admin = "admin"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    full_name: Optional[str] = None
    hashed_password: str
    role: Role = Field(sa_column_kwargs={"default": Role.cliente})
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    orders: List["Order"] = Relationship(back_populates="owner")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    state: str = Field(default="pendiente")  # posible: pendiente, procesado, enviado

    owner: Optional[User] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "orderitems"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(nullable=False)  # ID externo en DummyJSON
    quantity: int = Field(default=1)

    order: Optional[Order] = Relationship(back_populates="items")