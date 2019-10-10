import sys
import time
import zmq
import os
import sys

if(len(sys.argv) == 2):
    fileName = sys.argv[1]
else:
    fileName = 'worker_process.id'

print(fileName)
context = zmq.Context()
f = open("process/"+fileName, "a+")
f.write(str(os.getpid()) + "\n")
f.close()
# # Socket to receive messages on
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5557")

# Socket to send messages to
sender = context.socket(zmq.PUSH)
sender.connect("tcp://localhost:5558")

while True:
    s = receiver.recv()

    # Simple progress indicator for the viewer
    sys.stdout.write('.')
    sys.stdout.flush()

    # Do the work
    time.sleep(int(s)*0.001)

    # Send results to sink
    sender.send(b'')
