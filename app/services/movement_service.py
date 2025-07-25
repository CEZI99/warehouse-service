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
    async def _is_dublicated(session: AsyncSession, movement_id: str, movement_type: str) -> bool:
        """Проверка, было ли уже обработано такое перемещение"""
        result = await session.execute(
            select(DBMovement)
            .where(DBMovement.movement_id == movement_id)
            .where(DBMovement.movement_type == movement_type)
        )
        return result.scalars().first() is not None

    @staticmethod
    async def process_kafka_event(session: AsyncSession, message: Dict) -> None:
        """Обработка события из Kafka"""
        try:
            data = message["data"]
            movement_type = data["event"]
            movement_id = data["movement_id"]

            # Проверка на дубликат обработки
            if await MovementService._is_dublicated(session, movement_id, movement_type):
                logger.warning(f"Movement already processed: {movement_id}/{movement_type}")
                return

            # Подготовка данных для обработки
            movement = {
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
        """Связывание парных перемещений (отправка и приемка) между складами.
        Args:
            movement_id: Уникальный идентификатор перемещения, 
                    общий для парных событий отправки/приемки
        Logic:
            1. Находит все записи перемещений с заданным movement_id
            2. Если найдены оба события (отправка и приемка):
            - Устанавливает взаимные ссылки между складами
            - Логирует время доставки
        """
        # Шаг 1: Поиск всех перемещений с этим movement_id
        # Сортировка по timestamp критична для определения порядка событий
        result = await session.execute(
            select(DBMovement)
            .where(DBMovement.movement_id == movement_id)
            .order_by(DBMovement.timestamp)
        )
        movements = result.scalars().all()
        # Шаг 2: Проверяем, что есть оба события (отправка и приемка)
        if len(movements) == 2:
            # Извлекаем departure (отправка) - должно быть первым по времени
            departure = next(m for m in movements if m.movement_type == "departure")
            # Извлекаем arrival (приемка) - должно быть вторым по времени
            arrival = next(m for m in movements if m.movement_type == "arrival")

            # Шаг 3: Устанавливаем взаимные ссылки между складами
            # В записи об отправке указываем склад-получатель
            departure.related_warehouse_id = arrival.warehouse_id
            # В записи о приемке указываем склад-отправитель
            arrival.related_warehouse_id = departure.warehouse_id
            # Шаг 4: Расчет и логирование времени доставки
            time_delta = arrival.timestamp - departure.timestamp  # Вычисляем дельту
            # Форматируем логи для аналитики
            logger.info(
                f"Связаны перемещения: ID={movement_id}, "
                f"Отправка: {departure.warehouse_id} -> Приемка: {arrival.warehouse_id}, "
                f"Время доставки: {time_delta.total_seconds()} сек. "
                f"({time_delta.total_seconds()/3600:.2f} часов)"
            )

        # Если событий меньше 2 - значит второе еще не обработано
        elif len(movements) > 2:
            logger.error(
                f"Обнаружены дубликаты для movement_id={movement_id}. "
                f"Найдено записей: {len(movements)}"
            )