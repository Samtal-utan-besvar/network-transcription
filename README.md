# Network - transcription

This repo is used for tracking and developing files for the transcription server. It is meant be run on an linux based multicore server. The software developed in this repository is capable of:
<ol>
  <li>Recieving matrices of sound data (of 16-bit integer format) with a corresponding id.</li>
  <li>Transcribe transfered soundfiles into text and store for a limited time.</li>
  <li>Keep track of the text until the owner and the reciever of the transcription has requested and been given the text.</li>
  <li>Distribute the transcribing task among all available CPU cores.</li>
</ol>
The software utilizes the community Hugging Face's open source transcribing model KBLab/wav2vec2-large-voxrex-swedish which has a good precision compared to other paid models. The multiprocessing logic is dynamically written which means the number of transcription processes easily can be modified via an integer in main.py labeled "number_of_processes". If your system is 4-core, keep it to 1 since pytorch allocates resources good on its own and 2 processes actually reduces performance. If your system is 12-core (6 cores with dual threads) 3 parallell processes has been tested with a good result. Don't hesitate to experiment with this number on your own though. 

### Requirements:
<ol>
  <li>Python 3.7 or higher due to certain functionality in asyncio. Think of this when installing on a linux system since they can come with older versions of Python that does not work and need to be worked around.</li>
  <li>
  Port 6000 needs to be opened on the network and the system in the current configuration in order to communicate with the server outside the local network. After setting up the server, please also make sure to provide all connecting clients with the corrept IP-adress. 
  </li>
</ol>

### Packages to pip install:
<ol>
  <li>torch</li>
  <li>torchaudio</li>
  <li>transformers</li>
  <li>datasets</li>
  <li>numpy</li>
  <li>websockets</li>
</ol>
Please make sure that theese packages are installed to your Python 3.7+ version and not any older default version. You could also need additional packages dependent on what is pre-installed in your configuration. 

### Test Programs:
The test programs are meant to be run on a separate system from the server. If you are running them on windows you need to install ffmpeg manually. This includes downloading a library and adding it to path. If you are running linux, a simple apt install should do the trick. Try to run the scripts and see what is missing from the error codes. Don't forget to update your IP-adress.
