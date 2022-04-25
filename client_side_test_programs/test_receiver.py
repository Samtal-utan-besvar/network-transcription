import asyncio
import websockets
import numpy
import time
import json

"""
A receiver client for prompting server for an answer sent in by another client. So in order for this
test file to be succesful you have to run test_sender. If you run recever first it will wait for the 
server to receive a job from sender. If you run sender first you have to run receiver within 20 seconds,
otherwise the server will remove the answer, which is also a test in itself if you wait to run this file
for 20 seconds. 

Also test the server by running sender first and then receiver twice. The second request should fail since
the server has already served the owner and receiver and therefore removed the answer. 
"""
async def retrieve_data():
    async with websockets.connect("ws://129.151.206.9:6000") as websocket:  #129.151.209.72

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