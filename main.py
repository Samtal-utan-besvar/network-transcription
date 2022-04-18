import asyncio
import websockets
import threading
import transcription_process
import numpy as np
from multiprocessing import Process, Pipe, Semaphore

messages = []
answers = []


"""

def f(conn):
    conn.send([42, None, 'hello'])
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()
    print(parent_conn.recv())   # prints "[42, None, 'hello']"
    p.join()

"""

"""
(Will soon) Starts several processes of parallell transcription instances and delegates incoming transcription work 
amongst theese from the work queue (messages). 
"""
def request_handler():

    parent_pipe, child_pipe = Pipe()
    sema = Semaphore(0)
    p = Process(target=transcription_process.main, args=(child_pipe, sema,))
    p.start()
    while True:
        #number_of_procecess = 1
        while len(messages)==0:
            pass
        message = messages.pop(0)
        parent_pipe.send(np.frombuffer(message, dtype=np.float32))
        sema.release()

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


"""
Main function, sets up the listening websocket and handles all incoming ws work requests.
Starts thread in request_handler to run in parallell. 
"""
async def main():
    req_hand = threading.Thread(target=request_handler, args=())
    req_hand.start()
    print("Started")
    async with websockets.serve(echo, None, 6000):
        await asyncio.Future()  # run forever

asyncio.run(main())


