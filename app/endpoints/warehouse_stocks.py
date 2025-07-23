from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import WarehouseStock
from app.models.database import get_db
from app.services.stock_service import StockService

router = APIRouter(prefix="/warehouses", tags=["warehouse stocks"])

@router.get("/{warehouse_id}/products/{product_id}", response_model=WarehouseStock)
async def get_warehouse_stock(
    warehouse_id: str, 
    product_id: str, 
    db: AsyncSession = Depends(get_db)
):
    stock = await StockService.get_stock(db, warehouse_id, product_id)
    if stock.quantity == 0 and stock.last_updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stock found for product {product_id} in warehouse {warehouse_id}"
        )
    return stock