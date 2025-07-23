import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.database import DATABASE_URL
from services.movement_service import MovementService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncKafkaConsumer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.engine = create_async_engine(DATABASE_URL)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def parse_message(self, msg_value: bytes) -> Dict[str, Any]:
        try:
            data = json.loads(msg_value.decode('utf-8'))
            return {
                "id": data["data"]["movement_id"],
                "movement_type": data["data"]["event"],
                "warehouse_id": data["data"]["warehouse_id"],
                "product_id": data["data"]["product_id"],
                "quantity": data["data"]["quantity"],
                "timestamp": datetime.fromisoformat(data["data"]["timestamp"].rstrip('Z')),
                "related_movement_id": None
            }
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            raise

    async def process_message(self, msg):
        try:
            movement_data = await self.parse_message(msg.value)
            logger.info(f"Processing movement: {movement_data}")

            async with self.async_session() as session:
                try:
                    await MovementService.process_movement(session, movement_data)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error processing movement: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def consume_messages(self):
        consumer = AIOKafkaConsumer(
            'warehouse-movements',
            bootstrap_servers=self.bootstrap_servers,
            group_id="warehouse-movement-group",
            auto_offset_reset='earliest'
        )
        
        await consumer.start()
        try:
            async for msg in consumer:
                await self.process_message(msg)
        finally:
            await consumer.stop()

    async def run(self):
        while True:
            try:
                await self.consume_messages()
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                await asyncio.sleep(5)