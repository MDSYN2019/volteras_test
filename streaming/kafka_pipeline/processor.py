"""Consume raw GPS events and publish the validated live-location product."""

import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from kafka_pipeline.messages import validate_and_enrich


async def main() -> None:
    brokers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    raw_topic = os.getenv("KAFKA_RAW_TOPIC", "vehicle.location.raw.v1")
    product_topic = os.getenv("KAFKA_PRODUCT_TOPIC", "vehicle.location.current.v1")
    consumer = AIOKafkaConsumer(
        raw_topic,
        bootstrap_servers=brokers,
        group_id="location-product-builder-v1",
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=brokers)
    await consumer.start()
    await producer.start()
    try:
        async for message in consumer:
            try:
                product = validate_and_enrich(json.loads(message.value))
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                print(f"rejected offset={message.offset}: {error}", flush=True)
                continue
            await producer.send_and_wait(
                product_topic,
                json.dumps(product).encode(),
                key=product["vehicle_id"].encode(),
            )
            print(f"published {product_topic} sequence={product['sequence']}", flush=True)
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())

