from datetime import timedelta
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from app.models.database import get_db, DBMovement, DBWarehouseStock

router = APIRouter(prefix="/api/warehouses", tags=["Warehouse API"])

CACHE_EXPIRE_STOCK = int(os.getenv("CACHE_EXPIRE_STOCK", 300))  # 5 минут по умолчанию
CACHE_EXPIRE_MOVEMENTS = int(os.getenv("CACHE_EXPIRE_MOVEMENTS", 3600))  # 1 час по умолчанию


@router.get("/{warehouse_id}/products/{product_id}")
@cache(
    expire=timedelta(seconds=CACHE_EXPIRE_STOCK),
    key_builder=lambda request, *args, **kwargs: f"stock:{request.path_params['warehouse_id']}:{request.path_params['product_id']}"
)
@cache(
    expire=timedelta(seconds=CACHE_EXPIRE_STOCK),
    key_builder=lambda *args, **kwargs:f"stock:{kwargs['request'].path_params['warehouse_id']}:{kwargs['request'].path_params['product_id']}"
)
async def get_warehouse_stock(
    warehouse_id: str,
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение текущих запасов товара на складе с кэшированием"""
    stock = await db.get(DBWarehouseStock, (warehouse_id, product_id))
    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Товар {product_id} не найден на складе {warehouse_id}"
        )
    return {
        "warehouse_id": warehouse_id,
        "product_id": product_id,
        "current_quantity": stock.quantity,
        "last_updated": stock.last_updated
    }

@router.get("/movements/{movement_id}")
@cache(
    expire=timedelta(seconds=CACHE_EXPIRE_MOVEMENTS),
    key_builder=lambda *args, **kwargs: f"movement:{kwargs['request'].path_params['movement_id']}"
)
async def get_movement_details(
    movement_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение информации о перемещении с кэшированием"""
    movement = await db.get(DBMovement, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Перемещение не найдено")

    result = {
        "id": movement.id,
        "type": movement.movement_type,
        "warehouse_id": movement.warehouse_id,
        "product_id": movement.product_id,
        "quantity": movement.quantity,
        "timestamp": movement.timestamp.isoformat()
    }

    if movement.related_movement_id:
        related = await db.get(DBMovement, movement.related_movement_id)
        if related:
            time_diff = movement.timestamp - related.timestamp
            result.update({
                "related_movement_id": movement.related_movement_id,
                "time_in_transit": str(time_diff).split(".")[0],
                "quantity_difference": abs(movement.quantity - related.quantity)
            })

    return result
