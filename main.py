import asyncio
import websockets

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    print("Started")
    async with websockets.serve(echo, 6000):
        await asyncio.Future()  # run forever

asyncio.run(main())