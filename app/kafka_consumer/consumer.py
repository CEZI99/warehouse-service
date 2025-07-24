import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import DATABASE_URL
from app.services.movement_service import MovementService
from app.dependencies.data_validate_message import required_structure

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.engine = create_async_engine(DATABASE_URL)
        self.Session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def _validate_message_structure(self, data: Dict[str, Any]) -> bool:
        """Проверка структуры сообщения"""
        try:
            if not isinstance(data, dict):
                raise ValueError("Message is not a dictionary")

            # Проверка верхнего уровня
            for top_level_key in required_structure:
                if top_level_key not in data:
                    raise ValueError(f"Missing top-level key: {top_level_key}")

            # Проверка вложенной структуры data
            if not isinstance(data["data"], dict):
                raise ValueError("'data' must be an object")

            for nested_key in required_structure["data"]:
                if nested_key not in data["data"]:
                    raise ValueError(f"Missing nested key: data.{nested_key}")

            return True
        except Exception as e:
            logger.error(f"Invalid message keys structure: {e}")
            return False

    async def process_message(self, message) -> bool:
        """Обработка одного сообщения из Kafka"""
        try:
            # Логирование сырого сообщения
            logger.debug(f"Raw message received: {message}")

            # Декодирование сообщения
            try:
                message_str = message.value.decode('utf-8')
                logger.debug(f"Decoded message: {message_str}")
            except UnicodeDecodeError as e:
                logger.error(f"Decoding error: {e}")
                return False

            # Парсинг JSON
            try:
                data = json.loads(message_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return False

            # Валидация структуры
            if not await self._validate_message_structure(data):
                return False

            # Подготовка данных для обработки
            movement = {
                "id": data["id"],
                "source": data["source"],
                "movement_id": data["data"]["movement_id"],
                "movement_type": data["data"]["event"],
                "warehouse_id": data["data"]["warehouse_id"],
                "product_id": data["data"]["product_id"],
                "quantity": data["data"]["quantity"],
                "timestamp": datetime.fromisoformat(data["data"]["timestamp"].rstrip('Z'))
            }

            logger.info(f"Processing movement: {movement['id']}")

            # Обработка движения
            async with self.Session() as session:
                await MovementService._process_movement(session, movement)
                await session.commit()

            return True

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False

    async def consume(self):
        """Основной цикл потребления сообщений"""
        consumer = AIOKafkaConsumer(
            'warehouse-movements',
            bootstrap_servers=self.bootstrap_servers,
            group_id="warehouse-group",
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            session_timeout_ms=60000,
            heartbeat_interval_ms=20000,
            max_poll_interval_ms=300000
        )

        logger.info("Starting Kafka consumer...")
        await consumer.start()

        try:
            while True:
                try:
                    async for msg in consumer:
                        logger.info(
                            f"Received message from topic={msg.topic} "
                            f"partition={msg.partition} "
                            f"offset={msg.offset}"
                        )

                        success = await self.process_message(msg)
                        if success:
                            await consumer.commit()
                        else:
                            logger.warning("Message processing failed, skipping commit")

                except asyncio.CancelledError:
                    logger.info("Consumer stopped by cancellation")
                    break
                except Exception as e:
                    logger.error(f"Consumer error: {e}", exc_info=True)
                    await asyncio.sleep(5)

        finally:
            logger.info("Stopping consumer...")
            await consumer.stop()
            await self.engine.dispose()

async def main():
    """Точка входа для запуска потребителя"""
    try:
        consumer = KafkaConsumer(bootstrap_servers="kafka:9092")
        await consumer.consume()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Consumer service stopped")

if __name__ == "__main__":
    asyncio.run(main())
