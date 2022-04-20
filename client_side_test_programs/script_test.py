import numpy as np
import librosa
"""
f = "4_ref.mp3"
sound, sampling_rate = librosa.load(f)
sound_16khz = librosa.resample(sound, orig_sr=sampling_rate, target_sr=16_000)
print(str(sound_16khz.tobytes()))
"""

import struct

numbers = np.ones((2,3), dtype=np.float32)
bts = numbers.tobytes()
strii = str(bts)
print("Numbers is")
print(numbers)
print("bts is")
print(bts)
print("strii is")
print(strii)

new_bytes = strii.encode('iso-8859-15')

print("new_bts is")
print(new_bytes)

new_numbers = np.frombuffer(new_bytes, dtype=np.float32)

print("new Numbers is")
print(new_numbers)