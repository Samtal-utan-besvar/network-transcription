import asyncio
from email import message
import websockets
import threading
import transcription_process
import numpy as np
from multiprocessing import Process, Pipe, Semaphore, Event, Manager

messages = []
answers = []
message_available = None

"""
For every transcriptions process active a thread is started here. The thread sleeps until event is set
which means that the corresponding process is done transcribing and a message can be retrieved in the pipe.
"""
def answer_handler(event, pipe):
    while True:
        event.wait() #Wait until the transcription is done
        event.clear() #Clear event for future transcription
        answer = pipe.recv() #Retrieve the answer from pipe
        answers.append(answer) #Save answer for the request_handler

"""
Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages).
"""
def request_handler():
    number_of_processes = 1 #Specify the amount of transcribing instances you want (could be good to keep it below the amount of cpu-cores)

    active_processes = []
    free_processes = Semaphore(0) #Counter for the number of processes not currently transcribing
    for i in range(number_of_processes):
        #Setup communication for Process
        parent_pipe, child_pipe = Pipe() #Used to send soundfiles to and text answers back from process
        incoming_work_sema = Semaphore(0) #Alerts process that there is incoming transcription work
        answer_event = Event() #Wakes up the corresponding answer_handler thread when the text is done
        manag = Manager().dict(working=False)
        #Answer thread for specific transcription process
        ans_hand = threading.Thread(target=answer_handler, args=(answer_event, parent_pipe))
        ans_hand.start() #Starts the answering thread in answer_handler for each process
        #Process itself
        p = Process(target=transcription_process.main, args=(child_pipe, incoming_work_sema, answer_event, manag, free_processes,)) 
        p.start() #Starts the process in transcription_process.main

        process_bundle = [p, parent_pipe, incoming_work_sema, manag]
        active_processes.append(process_bundle) #Save the process with relevant information for use later

    while True:
        message_available.acquire() #wait until a message has been recieved from websocket
        free_processes.acquire() #wait until a transcription process is free to work again

        bundle = None #reset previous process_bundle
        for pro_bundle in active_processes: #find one process currently free
            if not pro_bundle[3]['working']: #if process not working
                bundle = pro_bundle
                break


        message = messages.pop(0) #Get the oldest message for transcribing

        #Get communnication links to process
        incoming_work_sema = bundle[2]
        parent_pipe = bundle[1]

        #Start the process work
        incoming_work_sema.release() #Signal transcription instance that there is work on the way
        parent_pipe.send(np.frombuffer(message, dtype=np.float32)) #Converts sound from bytes to float array and sends it into pipe for transcription


"""
Websocket answering function. Adds all incoming text into a work queue (messages).
Does not analyze messages yet for sorting and handling requests differently.
"""
async def echo(websocket):
    async for jsonmessage in websocket:
        
        if jsonmessage['Reason'] == "svar":
            message_sent = False
            for ans in answers:
                if jsonmessage['Id'] == ans[0]:
                    await websocket.send(ans[1])
                    message_sent = True
                    
                if not message_sent:
                    await websocket.send("")

        elif jsonmessage['Reason'] == "transcription":
            messages.append([message['Id'], np.assarray(message['Data'])])
            message_available.release()


"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request_handler to run in parallell. 
"""
async def main():
    global message_available
    message_available = threading.Semaphore(0) #Semaphore used to synchronize the incoming wbesocket jobs and request_handler scheduling

    req_hand = threading.Thread(target=request_handler, args=())
    req_hand.start() #Starts a separate thread in request handler while current thread is in charge of websockets

    print("Started")
    async with websockets.serve(echo, None, 6000):
        await asyncio.Future()  # run forever


if __name__ == '__main__': 
    asyncio.run(main())


