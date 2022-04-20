import asyncio
import websockets
import numpy
import time
import json

"""
A small test program for sending a single local mp3 file to the server
for it to transcribe via web_socket. 
"""


async def retrieve_data():
    async with websockets.connect("ws://129.151.209.72:6000") as websocket:  #129.151.209.72

        json_data = json.dumps([{"Reason":"answer", "Id":7893, "Data":"receiver"}])
        answer = ""
        while answer == "":
            await websocket.send(json_data)
            answer = await websocket.recv()
            time.sleep(0.1)
        print("Receiver")
        print(answer)
        await websocket.close()
if __name__ == '__main__': 
    start_time = time.perf_counter()
    asyncio.run(retrieve_data())
    stop_time = time.perf_counter()
    print("Time was " + str(stop_time - start_time))