# Network - transcription

This repo is used for tracking and developing files for the transcription server. It is meant be run on an linux based multicore server. The software developed in this repository is capable of:
<ol>
  <li>Recieving matrices of sound data with a corresponding id and who the owner of this file is.</li>
  <li>Transcribe transfered soundfiles into text and store.</li>
  <li>Keep track of the text until the owner and the reciever has requested and been given the text.</li>
  <li>Distribute the transcribing task among all available cores.</li>
</ol>
The software utilizes the community Hugging Face's open source transcribing model KBLab/wav2vec2-large-voxrex-swedish which has a good precision. 
