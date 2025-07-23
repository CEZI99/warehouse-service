from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import DBMovement, DBWarehouseStock
class MovementService:
    @staticmethod
    async def get_stock(session: AsyncSession, warehouse_id: str, product_id: str):
        return await session.get(DBWarehouseStock, (warehouse_id, product_id))

    @staticmethod
    async def process_movement(session: AsyncSession, movement: dict):
        stock = await MovementService.get_stock(
            session, 
            movement["warehouse_id"], 
            movement["product_id"]
        )
        
        current_quantity = stock.quantity if stock else 0
        
        if movement["movement_type"] == "departure":
            if current_quantity < movement["quantity"]:
                raise ValueError(
                    f"Not enough stock. Available: {current_quantity}, "
                    f"requested: {movement['quantity']}"
                )
            
            new_quantity = current_quantity - movement["quantity"]
            if stock:
                stock.quantity = new_quantity
            else:
                stock = DBWarehouseStock(
                    warehouse_id=movement["warehouse_id"],
                    product_id=movement["product_id"],
                    quantity=new_quantity
                )
                session.add(stock)
            
            db_movement = DBMovement(**movement)
            session.add(db_movement)
        
        elif movement["movement_type"] == "arrival":
            if stock:
                stock.quantity += movement["quantity"]
            else:
                stock = DBWarehouseStock(
                    warehouse_id=movement["warehouse_id"],
                    product_id=movement["product_id"],
                    quantity=movement["quantity"]
                )
                session.add(stock)
            
            db_movement = DBMovement(**movement)
            session.add(db_movement)
