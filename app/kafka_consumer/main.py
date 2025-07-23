import asyncio
import os
from .consumer import AsyncKafkaConsumer

async def main():
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    consumer = AsyncKafkaConsumer(kafka_servers)
    await consumer.run()

if __name__ == "__main__":
    asyncio.run(main())