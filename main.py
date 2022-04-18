import asyncio
from email import message
import websockets
import threading
import transcription_process
import numpy as np
from multiprocessing import Process, Pipe, Semaphore, Event, Manager

messages = []
answers = []
message_available = ""


def answer_handler(event, pipe):
    while True:
        event.wait()
        event.clear()
        answer = pipe.recv()
        answers.append(answer)

"""
Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages).
"""
def request_handler():

    active_processes = []
    for i in range(3):
        #Setup communication for Process
        parent_pipe, child_pipe = Pipe()
        sema = Semaphore(0)
        answer_event = Event()
        manag = Manager().dict(working=False)
        #Answer thread for specific transcription process
        ans_hand = threading.Thread(target=answer_handler, args=(answer_event, parent_pipe))
        ans_hand.start()
        #Process itself
        p = Process(target=transcription_process.main, args=(child_pipe, sema, answer_event, manag,)) 
        p.start()

        process_bundle = [p, parent_pipe, sema, manag]
        active_processes.append(process_bundle)

    while True:
        message_available.wait() #wait until a message has been recieved from websocket

        bundle = None #reset previous process_bundle
        searching_process = True
        while searching_process:
            #choose process bundle by finding an idle one
            for pro_bundle in active_processes:
                if not pro_bundle[3]['working']: #if process not working
                    bundle = pro_bundle
                    break
            if bundle!=None:
                searching_process = False

        message_available.clear() #clear flag so that a new message can be received
        message = messages.pop(0) #Get the oldest message for transcribing

        #Get communnication links to process
        sema = bundle[2]
        parent_pipe = bundle[1]
        #Process work
        sema.release()
        parent_pipe.send(np.frombuffer(message, dtype=np.float32))




"""
Websocket answering function. Adds all incoming text into a work queue (messages).
Does not analyze messages yet for sorting and handling different requests differently.
"""
async def echo(websocket):
    async for message in websocket:
        if message == "svar":
            if answers:
                await websocket.send(answers.pop(0))
            else:
                await websocket.send("")
        else:
            messages.append(message)
            message_available.set()


"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request_handler to run in parallell. 
"""
async def main():
    global message_available
    message_available = threading.Event()

    req_hand = threading.Thread(target=request_handler, args=())
    req_hand.start()
    print("Started")
    async with websockets.serve(echo, None, 6000):
        await asyncio.Future()  # run forever

asyncio.run(main())


