import asyncio
import websockets
import threading
from transcription_process import transcribe
import numpy as np

messages = []


"""
Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages). 
"""
def request_handler():
    #number_of_procecess = 1
    while len(messages)==0:
        pass
    message = messages.pop(0)
    transcribe(np.frombytes(message))


"""
Websocket answering function. Adds all incoming text into a work queue (messages)
"""
async def echo(websocket):
    async for message in websocket:
        messages.append(message)
        await websocket.send(message)


"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request handler to run in parallell. 
"""
async def main():
    print("Started")
    req_hand = threading.Thread(target=request_handler, args=())
    req_hand.start()
    async with websockets.serve(echo, None, 6000):
        await asyncio.Future()  # run forever

asyncio.run(main())
