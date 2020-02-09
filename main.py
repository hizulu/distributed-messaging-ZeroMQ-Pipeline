from log import Log
from ventilator import Ventilator
import time
import json
import sys
import env
import time

log = Log()
ven = Ventilator()
while True:
    task = log.getUnproceessLog()
    if(task['execute_status']):
        if(task['data']):
            print("{} Data being send".format(len(task['data'])))
            ven.send(task['data'])
            # sys.exit()
        else:
            time.sleep(1)
    else:
        print('Error retrieving data')
    # sys.exit()
