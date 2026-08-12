"""Generate a repeatable synthetic drive and publish GPS readings to Kafka."""

import asyncio
import json
import math
import os

from aiokafka import AIOKafkaProducer

from kafka_pipeline.messages import location_event


async def main() -> None:
    brokers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_RAW_TOPIC", "vehicle.location.raw.v1")
    vehicle_id = os.getenv("VEHICLE_ID", "demo-car-1")
    interval = float(os.getenv("LOCATION_INTERVAL_SECONDS", "1"))
    center_lat = float(os.getenv("ROUTE_CENTER_LATITUDE", "51.5074"))
    center_lon = float(os.getenv("ROUTE_CENTER_LONGITUDE", "-0.1278"))
    producer = AIOKafkaProducer(bootstrap_servers=brokers)
    await producer.start()
    try:
        sequence = 0
        while True:
            angle = sequence * math.pi / 45
            event = location_event(
                vehicle_id,
                center_lat + math.sin(angle) * 0.012,
                center_lon + math.cos(angle) * 0.019,
                sequence,
            )
            await producer.send_and_wait(
                topic, json.dumps(event).encode(), key=vehicle_id.encode()
            )
            print(f"produced {topic} sequence={sequence}", flush=True)
            sequence += 1
            await asyncio.sleep(interval)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())

