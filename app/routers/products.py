from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from app.schemas import Product
from app.utils import fetch_products_list
import asyncio

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=dict)
async def list_products(
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    sort: Optional[str] = Query(None, description="Campo para ordenar, p.ej. 'price' o '-price'"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0)
):
    """
    Lista de productos con paginación, ordenación y filtros. Retorna:
    {
      "products": [...],
      "total": int,
      "skip": int,
      "limit": int
    }
    """
    filters = {}
    if category:
        filters["category"] = category
    if min_price is not None:
        filters["minPrice"] = min_price
    if max_price is not None:
        filters["maxPrice"] = max_price

    result = await fetch_products_list(limit=limit, skip=skip, sort=sort, filter_params=filters)
    return result