import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://129.151.209.72:4000") as websocket:
        await websocket.send("Hello world!")
        await websocket.recv()

asyncio.run(hello())