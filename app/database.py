from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import DBMovement, DBWarehouseStock
from datetime import datetime
from typing import Dict, Any

async def process_movement(db: AsyncSession, movement: Dict[str, Any]):
    stock = await db.get(DBWarehouseStock, 
        (movement["warehouse_id"], movement["product_id"]))

    current_quantity = stock.quantity if stock else 0

    if movement["movement_type"] == "departure":
        if current_quantity < movement["quantity"]:
            raise ValueError(
                f"Not enough stock in warehouse {movement['warehouse_id']}. "
                f"Available: {current_quantity}, requested: {movement['quantity']}"
            )

        db_movement = DBMovement(
            id=movement["id"],
            movement_type="departure",
            warehouse_id=movement["warehouse_id"],
            product_id=movement["product_id"],
            quantity=movement["quantity"],
            timestamp=movement["timestamp"],
            related_movement_id=movement.get("related_movement_id")
        )
        db.add(db_movement)

        new_quantity = current_quantity - movement["quantity"]
        if stock:
            stock.quantity = new_quantity
        else:
            stock = DBWarehouseStock(
                warehouse_id=movement["warehouse_id"],
                product_id=movement["product_id"],
                quantity=new_quantity
            )
            db.add(stock)

    elif movement["movement_type"] == "arrival":
        related_departure = await db.get(DBMovement, movement["id"])

        if related_departure and related_departure.movement_type == "departure":
            related_departure.related_movement_id = movement["id"]

        db_movement = DBMovement(
            id=movement["id"],
            movement_type="arrival",
            warehouse_id=movement["warehouse_id"],
            product_id=movement["product_id"],
            quantity=movement["quantity"],
            timestamp=movement["timestamp"],
            related_movement_id=related_departure.id if related_departure else None
        )
        db.add(db_movement)

        new_quantity = current_quantity + movement["quantity"]
        if stock:
            stock.quantity = new_quantity
        else:
            stock = DBWarehouseStock(
                warehouse_id=movement["warehouse_id"],
                product_id=movement["product_id"],
                quantity=new_quantity
            )
            db.add(stock)
