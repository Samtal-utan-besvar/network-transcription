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
    answers = []
    message_available = None

"""
For every transcriptions process active a thread is started here. The thread sleeps until event is set
which means that the corresponding process is done transcribing and a message can be retrieved in the pipe.
"""
def answer_handler(event, pipe, answer_lock, globals):
    while True:
        event.wait() #Wait until the transcription is done
        event.clear() #Clear event for future transcription
        answer = pipe.recv() #Retrieve the answer from pipe

        answer_lock.acquire()
        current_time = time.perf_counter()
        globals.answers.append([answer, {"owner":False, "receiver":False}, current_time]) #Save answer for the request_handler
        answer_lock.release()


"""
Cleans up old anwers if they are not gathered within "timeout" time.
"""
def answer_cleaner(answer_lock, globals):
    timeout = 20
    while True:
        time.sleep(timeout)
        answer_lock.acquire()
        current_time = time.perf_counter()
        index = 0
        for ans in globals.answers:
            if current_time - ans[2] > timeout:
                index += 1
            else:
                break
        for i in range(index):
            answers.pop(0)
        answer_lock.release()
        if index != 0:
            print("Cleared up ", index, " old messages because of timeouts!")


"""
Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages).
"""
def request_handler(answer_lock, globals):
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
        ans_hand = threading.Thread(target=answer_handler, args=(answer_event, parent_pipe, answer_lock, globals,))
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
async def echo(websocket, answer_lock, globals):
    async for message in websocket:
        json_message = (json.loads(message))[0]

        if json_message["Reason"] == "answer":
            message_sent = False
            index = -1           #index for deletion if both parties have retrieved the message
            delete_answer = False

            answer_lock.acquire()
            for ans in globals.answers:
                index += 1
                data = ans[0]
                checker = ans[1]
                if json_message["Id"] == data[0]:

                    if json_message["Data"] == "owner":
                        checker["owner"] = True

                    elif json_message["Data"] == "receiver":
                        checker["receiver"] = True

                    await websocket.send(str(data[0]) + ":" + data[1])
                    message_sent = True
                    if checker["owner"] and checker["receiver"]:
                        delete_answer = True
            if delete_answer:
                globals.answers.pop(index)
            answer_lock.release()    

            if not message_sent:
                await websocket.send("")

        elif json_message["Reason"] == "transcription":
            globals.messages.append([json_message["Id"], json_message["Data"].encode("latin1")])
            globals.message_available.release()


"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request_handler to run in parallell. 
"""
async def main():
    globals = global_variables()
    globals.message_available = threading.Semaphore(0) #Semaphore used to synchronize the incoming wbesocket jobs and request_handler scheduling
    answer_lock = threading.Lock()

    req_hand = threading.Thread(target=request_handler, args=(answer_lock, globals,))
    req_hand.start() #Starts a separate thread in request handler while current thread is in charge of websockets

    answer_checker = threading.Thread(target=answer_cleaner, args=(answer_lock, globals,))
    answer_checker.start() #Starts a separate thread in request handler while current thread is in charge of websockets

    print("Started")
    async with websockets.serve(functools.partial(echo, answer_lock=answer_lock, globals=globals), None, 6000, ping_interval=20, ping_timeout=20):
        await asyncio.Future()  # run forever


if __name__ == '__main__': 
    asyncio.run(main())


