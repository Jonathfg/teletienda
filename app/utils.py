# app/utils.py

import httpx
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
import csv
import pandas as pd
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from app.schemas import Product, OrderRead, OrderItemRead
from datetime import datetime

DUMMYJSON_BASE = "https://dummyjson.com"


# ---------------------------- Consumo de API externa DummyJSON ----------------------------

async def fetch_product(product_id: int) -> Product:
    """
    Obtiene un producto por su ID desde DummyJSON.
    """
    url = f"{DUMMYJSON_BASE}/products/{product_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto {product_id} no encontrado")
    data = resp.json()
    return Product(**data)


async def fetch_products_list(
    limit: int = 10,
    skip: int = 0,
    sort: Optional[str] = None,
    filter_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Obtiene lista de productos con paginación, ordenación y filtros opcionales.
    filter_params puede incluir claves como 'category', 'minPrice', 'maxPrice', etc.
    Retorna el JSON completo que provee DummyJSON:
    { "products": [...], "total": int, "skip": int, "limit": int }
    """
    params: Dict[str, Any] = {"limit": limit, "skip": skip}
    if sort:
        params["sort"] = sort
    if filter_params:
        for key, val in filter_params.items():
            params[key] = val

    url = f"{DUMMYJSON_BASE}/products"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener lista de productos")
    return resp.json()  # contiene: products, total, skip, limit


# ---------------------------- Exportación a CSV / Excel / PDF ----------------------------

def export_orders_to_csv(orders: List[OrderRead]) -> bytes:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "User ID", "Created At", "State",
        "Product ID", "Title", "Quantity", "Price Unitario", "Subtotal"
    ])
    for order in orders:
        for item in order.items:
            precio_unitario = item.product.price
            subtotal = precio_unitario * item.quantity
            writer.writerow([
                order.id,
                order.user_id,
                order.created_at.isoformat(),
                order.state,
                item.product.id,
                item.product.title,
                item.quantity,
                f"{precio_unitario:.2f}",
                f"{subtotal:.2f}"
            ])
    return output.getvalue().encode('utf-8')


def export_orders_to_excel(orders: List[OrderRead]) -> bytes:
    rows = []
    for order in orders:
        for item in order.items:
            precio_unitario = item.product.price
            subtotal = precio_unitario * item.quantity
            rows.append({
                "Order ID": order.id,
                "User ID": order.user_id,
                "Created At": order.created_at,
                "State": order.state,
                "Product ID": item.product.id,
                "Title": item.product.title,
                "Quantity": item.quantity,
                "Price Unitario": precio_unitario,
                "Subtotal": subtotal
            })
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Orders")
    return buffer.getvalue()


def export_orders_to_pdf(orders: List[OrderRead]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    y = height - inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y, "Reporte de Pedidos")
    c.setFont("Helvetica", 10)
    y -= inch

    for order in orders:
        c.drawString(inch, y, f"Pedido ID: {order.id} | Usuario: {order.user_id} | Fecha: {order.created_at.isoformat()} | Estado: {order.state}")
        y -= 0.3 * inch
        c.drawString(inch * 1.5, y, "Productos:")
        y -= 0.3 * inch
        for item in order.items:
            precio_unitario = item.product.price
            subtotal = precio_unitario * item.quantity
            line = f"- {item.product.title} (ID:{item.product.id}) x {item.quantity} @ {precio_unitario:.2f}€ = {subtotal:.2f}€"
            c.drawString(inch * 2, y, line)
            y -= 0.3 * inch
            if y < inch:
                c.showPage()
                y = height - inch
        total = sum(item.product.price * item.quantity for item in order.items)
        c.drawString(inch * 1.5, y, f"Total Pedido: {total:.2f}€")
        y -= inch
        if y < inch:
            c.showPage()
            y = height - inch

    c.showPage()
    c.save()
    return buffer.getvalue()