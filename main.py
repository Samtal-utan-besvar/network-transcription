import asyncio
from email import message
import websockets
import threading
import transcription_process
import numpy as np
from multiprocessing import Process, Pipe, Semaphore, Event, Manager
import json
import time
import functools

class global_variables:
    messages = []
    answers = {}
    message_available = None
    clients = {}


"""
For every transcriptions process active a thread is started here. The thread sleeps until event is set
which means that the corresponding process is done transcribing and a message can be retrieved in the pipe.
"""
def answer_handler(event, pipe, globals):
    while True:
        event.wait() #Wait until the transcription is done
        event.clear() #Clear event for future transcription
        answer = pipe.recv() #Retrieve the answer from pipe

        current_time = time.perf_counter()

        id = answer[0]
        text = answer[1]

        globals.answers[id] = (text, current_time)
        for client in globals.clients[id]:
            sendAnswer(client, str(id) + ":" + text)


def sendAnswer(client, answer):
    asyncio.run(client.send(answer))


"""
Cleans up old anwers if they are not gathered within "timeout" time.
"""
def answer_cleaner(globals):
    timeout = 20
    while True:
        time.sleep(timeout)
        current_time = time.perf_counter()
        count = 0
        for id in list(globals.answers.keys()):
            trans_time = globals.answers[id][1]
            if current_time > trans_time + timeout:
                globals.answers.pop(id)
                globals.clients.pop(id)
                count += 1
        if count != 0:
            print("Cleared up ", count, " old messages because of timeouts!")


"""
Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages).
"""
def request_handler(globals):
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
        ans_hand = threading.Thread(target=answer_handler, args=(answer_event, parent_pipe, globals,))
        ans_hand.start() #Starts the answering thread in answer_handler for each process
        #Process itself
        p = Process(target=transcription_process.main, args=(child_pipe, incoming_work_sema, answer_event, manag, free_processes,)) 
        p.start() #Starts the process in transcription_process.main

        process_bundle = [p, parent_pipe, incoming_work_sema, manag]
        active_processes.append(process_bundle) #Save the process with relevant information for use later

    while True:
        globals.message_available.acquire() #wait until a message has been recieved from websocket
        free_processes.acquire() #wait until a transcription process is free to work again

        bundle = None #reset previous process_bundle
        for pro_bundle in active_processes: #find one process currently free
            if not pro_bundle[3]['working']: #if process not working
                bundle = pro_bundle
                break


        message = globals.messages.pop(0) #Get the oldest message for transcribing
        sound_data = np.frombuffer(message[1], dtype=np.int16)

        if len(sound_data) != 0:

            """
            If the sound is 16-bit, convert it to floating point.
            """
            if max(sound_data) > 1 or min(sound_data) < -1:
                new_sound = []
                for sample in sound_data:
                    new_value = float(sample/32768)
                    if new_value > 1:
                        new_value = 1
                    elif new_value < -1:
                        new_value = -1
                    new_sound.append(new_value)
                sound_data = new_sound

            #Get communnication links to process
            incoming_work_sema = bundle[2]
            parent_pipe = bundle[1]

            #Start the process work
            incoming_work_sema.release() #Signal transcription instance that there is work on the way
            parent_pipe.send((message[0], sound_data)) #Converts sound from bytes to float array and sends it into pipe for transcription


"""
Websocket answering function. Adds all incoming text into a work queue (messages).
Does not analyze messages yet for sorting and handling requests differently.
"""
async def echo(websocket, globals):

    async for message in websocket:
        json_message = (json.loads(message))[0]

        id = json_message["Id"]
        addClient(websocket, id, globals)
        if json_message["Reason"] == "answer":

            if id in globals.answers.keys():
                text = globals.answers[id][0]
                await websocket.send(str(id) + ":" + text)


        elif json_message["Reason"] == "transcription":
            globals.messages.append([json_message["Id"], json_message["Data"].encode("latin1")])
            globals.message_available.release()


def addClient(websocket, id, globals):

    print('add client:', websocket.remote_address)

    if not id in globals.clients.keys():
        globals.clients[id] = set()
    
    globals.clients[id].add(websocket)
    print("clients:", len(globals.clients[id]))



"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request_handler to run in parallell. 
"""
async def main():
    globals = global_variables()
    globals.message_available = threading.Semaphore(0) #Semaphore used to synchronize the incoming wbesocket jobs and request_handler scheduling

    req_hand = threading.Thread(target=request_handler, args=(globals,))
    req_hand.start() #Starts a separate thread in request handler while current thread is in charge of websockets

    answer_checker = threading.Thread(target=answer_cleaner, args=(globals,))
    answer_checker.start() #Starts a separate thread in request handler while current thread is in charge of websockets

    print("Started")
    async with websockets.serve(functools.partial(echo, globals=globals), None, 6000, ping_interval=20, ping_timeout=20):
        await asyncio.Future()  # run forever


if __name__ == '__main__': 
    asyncio.run(main())


