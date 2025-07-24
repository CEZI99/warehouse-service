from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import DBWarehouseStock
from app.models.schemas import WarehouseStock
from datetime import datetime

class StockService:
    @staticmethod
    async def get_stock(
        session: AsyncSession, 
        warehouse_id: str, 
        product_id: str
    ) -> WarehouseStock:
        stock = await session.get(DBWarehouseStock, (warehouse_id, product_id))
        if not stock:
            return WarehouseStock(
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=0,
                last_updated=datetime.utcnow()
            )
        return stock

    @staticmethod
    async def update_stock(
        session: AsyncSession,
        warehouse_id: str,
        product_id: str,
        quantity: int
    ) -> None:
        stock = await session.get(DBWarehouseStock, (warehouse_id, product_id))
        if stock:
            stock.quantity = quantity
            stock.last_updated = datetime.utcnow()
        else:
            stock = DBWarehouseStock(
                warehouse_id=warehouse_id,
                product_id=product_id,
                quantity=quantity,
                last_updated=datetime.utcnow()
            )
            session.add(stock)
        await session.commit()
