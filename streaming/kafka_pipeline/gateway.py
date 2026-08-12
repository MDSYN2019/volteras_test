"""Fan Kafka location products out to browser WebSocket consumers."""

import asyncio
import os
from contextlib import suppress

from aiohttp import WSMsgType, web
from aiokafka import AIOKafkaConsumer


async def consume(app: web.Application) -> None:
    consumer = AIOKafkaConsumer(
        os.getenv("KAFKA_PRODUCT_TOPIC", "vehicle.location.current.v1"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        group_id="location-websocket-gateway-v1",
        auto_offset_reset="latest",
    )
    await consumer.start()
    app["consumer"] = consumer
    try:
        async for message in consumer:
            stale = []
            for socket in app["sockets"]:
                try:
                    await socket.send_str(message.value.decode())
                except ConnectionError:
                    stale.append(socket)
            for socket in stale:
                app["sockets"].discard(socket)
    finally:
        await consumer.stop()


async def websocket(request: web.Request) -> web.WebSocketResponse:
    socket = web.WebSocketResponse(heartbeat=20)
    await socket.prepare(request)
    request.app["sockets"].add(socket)
    try:
        async for message in socket:
            if message.type == WSMsgType.ERROR:
                break
    finally:
        request.app["sockets"].discard(socket)
    return socket


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def start(app: web.Application) -> None:
    app["consumer_task"] = asyncio.create_task(consume(app))


async def stop(app: web.Application) -> None:
    app["consumer_task"].cancel()
    with suppress(asyncio.CancelledError):
        await app["consumer_task"]


app = web.Application()
app["sockets"] = set()
app.router.add_get("/locations", websocket)
app.router.add_get("/health", health)
app.on_startup.append(start)
app.on_cleanup.append(stop)

if __name__ == "__main__":
    web.run_app(app, port=8080)

