from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from sqlmodel import Session, select
from app.schemas import ExportRequest, ExportFormat, OrderRead
from app.database import get_session
from app.models import Order
from app.crud_orders import get_all_orders, get_orders_by_user, enrich_orders_list
from app.auth import get_current_active_user, get_current_active_admin
from app.utils import export_orders_to_csv, export_orders_to_excel, export_orders_to_pdf
import asyncio
from datetime import datetime

router = APIRouter(prefix="/exports", tags=["exports"])

@router.post("/", summary="Exportar pedidos", responses={
    200: {"content": {"application/octet-stream": {}}},
})
async def export_orders(
    export_req: ExportRequest,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_active_user)
):
    """
    Exporta los pedidos a CSV, Excel o PDF.
    - Si el usuario es cliente, sólo se exportan sus pedidos.
    - Si es admin y no se pasa user_id, se exportan todos.
    - Si es admin y pasa user_id, se exportan sólo de ese usuario.
    """
    # Obtener pedidos
    if current_user.role == "admin":
        if export_req.user_id:
            # Pedidos de usuario específico
            stmt = select(Order).where(Order.user_id == export_req.user_id).order_by(Order.created_at.desc())
            orders = session.exec(stmt).all()
        else:
            orders = get_all_orders(session)
    else:
        # Role cliente solo sus pedidos
        orders = get_orders_by_user(session, current_user)

    # Enriquecer orders
    enriched = await enrich_orders_list(orders)

    # Generar export según formato
    if export_req.format == ExportFormat.csv:
        data = export_orders_to_csv(enriched)
        media_type = "text/csv"
        filename = f"orders_{datetime.utcnow().isoformat()}.csv"
    elif export_req.format == ExportFormat.excel:
        data = export_orders_to_excel(enriched)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"orders_{datetime.utcnow().isoformat()}.xlsx"
    elif export_req.format == ExportFormat.pdf:
        data = export_orders_to_pdf(enriched)
        media_type = "application/pdf"
        filename = f"orders_{datetime.utcnow().isoformat()}.pdf"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de exportación no válido")

    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\""
    }
    return Response(content=data, media_type=media_type, headers=headers)