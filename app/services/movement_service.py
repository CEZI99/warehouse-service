from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import DBMovement, DBWarehouseStock
from sqlalchemy import select
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MovementService:
    @staticmethod
    async def get_stock(session: AsyncSession, warehouse_id: str, product_id: str) -> Optional[DBWarehouseStock]:
        """Получение текущих остатков на складе"""
        return await session.get(DBWarehouseStock, (warehouse_id, product_id))

    @staticmethod
    async def process_kafka_event(session: AsyncSession, message: Dict) -> None:
        """Обработка события из Kafka"""
        try:
            data = message["data"]
            movement_type = data["event"]
            movement_id = data["movement_id"]
            
            # Проверка на дубликат обработки
            if await MovementService._is_processed(session, movement_id, movement_type):
                logger.warning(f"Movement already processed: {movement_id}/{movement_type}")
                return

            # Подготовка данных для обработки
            movement = {
                "id": message["id"],
                "movement_id": movement_id,
                "movement_type": movement_type,
                "warehouse_id": data["warehouse_id"],
                "product_id": data["product_id"],
                "quantity": data["quantity"],
                "timestamp": datetime.fromisoformat(data["timestamp"].rstrip('Z')),
                "source": message["source"],
                "destination": message["destination"],
                "processed_at": datetime.now()
            }

            # Обработка перемещения
            await MovementService._process_movement(session, movement)
            
            # Связывание парных перемещений
            if movement_type in ["arrival", "departure"]:
                await MovementService._link_movements(session, movement_id)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def _process_movement(session: AsyncSession, movement: Dict) -> None:
        """Основная логика обработки перемещения"""
        stock = await MovementService.get_stock(
            session,
            movement["warehouse_id"],
            movement["product_id"]
        )

        current_quantity = stock.quantity if stock else 0
        new_quantity = current_quantity
        update_time = datetime.now()

        # Обработка разных типов перемещений
        if movement["movement_type"] == "departure":
            if current_quantity < movement["quantity"]:
                raise ValueError(
                    f"Not enough stock. Available: {current_quantity}, "
                    f"requested: {movement['quantity']}"
                )
            new_quantity = current_quantity - movement["quantity"]
        elif movement["movement_type"] == "arrival":
            new_quantity = current_quantity + movement["quantity"]
        else:
            raise ValueError(f"Unknown movement type: {movement['movement_type']}")

        # Обновление или создание записи об остатках
        if stock:
            stock.quantity = new_quantity
            stock.last_updated = update_time
        else:
            stock = DBWarehouseStock(
                warehouse_id=movement["warehouse_id"],
                product_id=movement["product_id"],
                quantity=new_quantity,
                last_updated=update_time
            )
            session.add(stock)

        # Сохранение информации о перемещении
        db_movement = DBMovement(**movement)
        session.add(db_movement)

    @staticmethod
    async def _link_movements(session: AsyncSession, movement_id: str) -> None:
        """Связывание парных перемещений (отправка и приемка)"""
        result = await session.execute(
            select(DBMovement)
            .where(DBMovement.movement_id == movement_id)
            .order_by(DBMovement.timestamp)
        )
        movements = result.scalars().all()
        
        if len(movements) == 2:
            departure = next(m for m in movements if m.movement_type == "departure")
            arrival = next(m for m in movements if m.movement_type == "arrival")
            
            departure.related_warehouse_id = arrival.warehouse_id
            arrival.related_warehouse_id = departure.warehouse_id
            
            # Расчет времени между отправкой и получением
            time_delta = arrival.timestamp - departure.timestamp
            logger.info(
                f"Linked movements: {movement_id}, "
                f"time delta: {time_delta.total_seconds()} sec"
            )

    @staticmethod
    async def _is_processed(session: AsyncSession, movement_id: str, movement_type: str) -> bool:
        """Проверка, было ли уже обработано такое перемещение"""
        result = await session.execute(
            select(DBMovement)
            .where(DBMovement.movement_id == movement_id)
            .where(DBMovement.movement_type == movement_type)
        )
        return result.scalars().first() is not None
