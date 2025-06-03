# app/schemas.py

from typing import List, Optional
from pydantic import BaseModel, EmailStr, constr
from enum import Enum
from datetime import datetime

# ----- Esquemas de Usuario -----

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    password: constr(min_length=6)

class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[constr(min_length=6)] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ----- Esquemas de Autenticación -----

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # normalmente será el user_id en cadena
    exp: int
    role: str

class TokenRefresh(BaseModel):
    refresh_token: str


# ----- Esquemas de Producto (consumidos desde DummyJSON) -----

class Product(BaseModel):
    id: int
    title: str
    description: str
    price: float
    discountPercentage: float
    rating: float
    stock: int
    brand: str
    category: str
    thumbnail: Optional[str]
    images: Optional[List[str]]

    class Config:
        orm_mode = True


# ----- Esquemas de Pedidos -----

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemRead(BaseModel):
    id: int
    product: Product
    quantity: int

    class Config:
        orm_mode = True

class OrderRead(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    state: str
    items: List[OrderItemRead]
    total_amount: float

    class Config:
        orm_mode = True

class OrderUpdateState(BaseModel):
    state: str  # valores permitidos: "pendiente", "procesado", "enviado"


# ----- Esquemas de Exportación -----

class ExportFormat(str, Enum):
    csv = "csv"
    excel = "excel"
    pdf = "pdf"

class ExportRequest(BaseModel):
    format: ExportFormat
    user_id: Optional[int] = None  # si admin: user_id opcional; si cliente, se ignora o valida internamente