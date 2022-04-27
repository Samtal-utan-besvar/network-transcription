import asyncio
import websockets
import librosa
import numpy
import time
import json

"""
A small test program for sending a single local mp3 file to the server
for it to transcribe via web_socket. Both prompts the server as owner 
and receiver to receive transcripts.
"""


async def send_data(data):
    async with websockets.connect("ws://129.151.206.9:6000") as websocket:  #129.151.206.9
        json_data = json.dumps([{"Reason":"transcription", "Id":80050, "Data":data.decode(encoding = "latin1")}])
        await websocket.send(json_data)

        json_data = json.dumps([{"Reason":"answer", "Id":80050, "Data":"owner"}])
        answer = ""
        while answer == "":
            await websocket.send(json_data)
            answer = await websocket.recv()
            time.sleep(0.1)
        print("Owner")
        print(answer)

        json_data = json.dumps([{"Reason":"answer", "Id":80050, "Data":"receiver"}])
        answer = ""
        while answer == "":
            await websocket.send(json_data)
            answer = await websocket.recv()
            time.sleep(0.1)
        print("Receiver")
        print(answer)
        await websocket.close()


if __name__ == '__main__': 
    f = "4_ref.mp3"
    sound, sampling_rate = librosa.load(f)
    sound_16khz = librosa.resample(sound, orig_sr=sampling_rate, target_sr=16_000)
    #np_file = np.load(sound_16khz, allow_pickle=True)

    print(sound_16khz.tobytes())
    """
    start_time = time.perf_counter()
    asyncio.run(send_data(sound_16khz.tobytes()))
    stop_time = time.perf_counter()
    print("Time was " + str(stop_time - start_time))
    """