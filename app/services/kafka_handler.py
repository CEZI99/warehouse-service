import logging
from aiokafka import AIOKafkaProducer
from app.models.schemas import KafkaEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaHandler:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap_servers
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_movement_event(self, event: KafkaEvent):
        try:
            await self.producer.send(
                'warehouse-movements',
                value=event.json().encode('utf-8')
            )
            logger.info(f"Sent Kafka event: {event.subject}")
        except Exception as e:
            logger.error(f"Error sending Kafka event: {e}")
            raise
