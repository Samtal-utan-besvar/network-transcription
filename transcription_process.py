import torch
import torchaudio
from datasets import load_dataset
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import time
import numpy as np
import os


"""
The transcription process, highgly based on the example code from hugging face.
Send in a numpy array of a sound file in swedish and sample rate 16kHz and it will transcribe. 
"""
def transcribe(soundfile, processor, model):
    print("Started transcribing")
    #np_file = np.load(soundfile, allow_pickle=True)
    total_time = 0
    inputs = processor(soundfile, sampling_rate=16_000, return_tensors="pt", padding=True)
    start = time.perf_counter()
    with torch.no_grad():
        logits = model(inputs.input_values, attention_mask=inputs.attention_mask).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    texts = processor.batch_decode(predicted_ids)
    inference_time = time.perf_counter()-start
    total_time += inference_time

    sample_length = len(soundfile) / 16000

    print("Sample time:\t", sample_length)
    print("Inference time:\t", inference_time, "\nPrediction:\t", texts[0])
    return texts[0]


def main(pipe, sema, answer_event):
    processor = Wav2Vec2Processor.from_pretrained("KBLab/wav2vec2-large-voxrex-swedish")
    model = Wav2Vec2ForCTC.from_pretrained("KBLab/wav2vec2-large-voxrex-swedish")
    while True:
        sema.acquire()
        sound = pipe.recv()
        answer = transcribe(sound, processor, model)
        answer_event.set()
        pipe.send(answer)
