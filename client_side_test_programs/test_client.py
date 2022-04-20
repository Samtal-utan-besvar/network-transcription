import asyncio
import websockets
import librosa
import numpy
import time
import json

"""
A small test program for sending a single local mp3 file to the server
for it to transcribe via web_socket. 
"""


async def send_data(data):
    async with websockets.connect("ws://localhost:6000") as websocket:  #129.151.209.72
        json_data = json.dumps([{"Reason":"transcription", "Id":7893, "Data":data.decode(encoding = "latin1")}])
        await websocket.send(json_data)

        json_data = json.dumps([{"Reason":"answer", "Id":7893, "Data":"owner"}])
        answer = ""
        while answer == "":
            await websocket.send(json_data)
            answer = await websocket.recv()
            time.sleep(0.1)
        print(answer)
        await websocket.close()

f = "4_ref.mp3"
sound, sampling_rate = librosa.load(f)
sound_16khz = librosa.resample(sound, orig_sr=sampling_rate, target_sr=16_000)
#np_file = np.load(sound_16khz, allow_pickle=True)

start_time = time.perf_counter()
asyncio.run(send_data(sound_16khz.tobytes()))
stop_time = time.perf_counter()
print("Time was " + str(stop_time - start_time))