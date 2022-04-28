import asyncio
import websockets
import librosa
import numpy
import time
import json

"""
A small test program for sending a single local mp3 file to the server
for it to transcribe via web_socket. Prompts the server as owner for file
to retrieve the transcription.
"""


async def send_data(data):
    async with websockets.connect("ws://129.151.206.9:6000") as websocket:  #129.151.206.9
        json_data = json.dumps([{"Reason":"transcription", "Id":7893, "Data":data.decode(encoding = "latin1")}])
        await websocket.send(json_data)


        json_data = json.dumps([{"Reason":"answer", "Id":7893, "Data":"owner"}])
        answer = ""
        while answer == "":
            await websocket.send(json_data)
            answer = await websocket.recv()
            time.sleep(0.1)
        print("Owner")
        print(answer)
        
        await websocket.close()

if __name__ == '__main__': 
    f = "4_ref.mp3"
    sound, sampling_rate = librosa.load(f)
    sound_16khz = librosa.resample(sound, orig_sr=sampling_rate, target_sr=16_000)

    new_sound = []
    for sample in sound_16khz:
        new_sample = sample * 32768
        if new_sample > 32767:
            new_sample = 32767
        if new_sample < -32767:
            new_sample = -32767
        new_sound.append(new_sample)

    start_time = time.perf_counter()
    asyncio.run(send_data(numpy.asarray(new_sound, dtype=numpy.int16).tobytes()))
    stop_time = time.perf_counter()
    print("Time was " + str(stop_time - start_time))