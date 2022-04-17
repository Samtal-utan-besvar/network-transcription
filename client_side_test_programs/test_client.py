import asyncio
import websockets
import librosa
import numpy as np

"""
A small test program for sending a single local mp3 file to the server
for it to transcribe via web_socket. 
"""


async def send_data(data):
    async with websockets.connect("ws://129.151.209.72:6000") as websocket:
        await websocket.send(data)
        await websocket.send("svar")
        await print(websocket.recv())


f = "4_ref.mp3"
sound, sampling_rate = librosa.load(f)
sound_16khz = librosa.resample(sound, orig_sr=sampling_rate, target_sr=16_000)
#np_file = np.load(sound_16khz, allow_pickle=True)
asyncio.run(send_data(sound_16khz.tobytes()))