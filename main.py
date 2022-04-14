import asyncio
import websockets
import threading
from transcription_process import transcribe

messages = []

def request_handler():
    #number_of_procecess = 1
    while len(messages)==0:
        pass
    message = messages.pop(0)
    transcribe(message)


async def echo(websocket):
    async for message in websocket:
        messages.append(message)
        await websocket.send(message)

async def main():
    print("Started")
    req_hand = threading.Thread(target=request_handler, args=(1,))
    req_hand.start()
    async with websockets.serve(echo, None, 6000):
        await asyncio.Future()  # run forever

asyncio.run(main())
