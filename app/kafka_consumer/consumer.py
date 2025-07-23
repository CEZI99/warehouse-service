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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.engine = create_async_engine(DATABASE_URL)
        self.Session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def process_message(self, message):
        try:
            data = json.loads(message.value.decode('utf-8'))
            movement = {
                "id": data["data"]["movement_id"],
                "movement_type": data["data"]["event"],
                "warehouse_id": data["data"]["warehouse_id"],
                "product_id": data["data"]["product_id"],
                "quantity": data["data"]["quantity"],
                "timestamp": datetime.fromisoformat(data["data"]["timestamp"].rstrip('Z'))
            }
            
            async with self.Session() as session:
                await MovementService.process_movement(session, movement)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def consume(self):
        consumer = AIOKafkaConsumer(
            'warehouse-movements',
            bootstrap_servers=self.bootstrap_servers,
            group_id="warehouse-group",
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # Отключаем авто-коммит
            session_timeout_ms=60000,  # Увеличиваем таймаут
            heartbeat_interval_ms=20000  # Увеличиваем интервал heartbeat
        )
        
        try:
            await consumer.start()
            while True:
                try:
                    async for msg in consumer:
                        await self.process_message(msg)
                except Exception as e:
                    logger.error(f"Consumer error: {e}")
                    await asyncio.sleep(5)
        finally:
            await consumer.stop()

async def main():
    consumer = KafkaConsumer("kafka:9092")
    await consumer.consume()

if __name__ == "__main__":
    asyncio.run(main())
