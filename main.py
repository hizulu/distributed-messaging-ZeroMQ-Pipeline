from log import Log
from ventilator import Ventilator
import time
import json
import sys
import env
import time
import datetime

log = Log()
ven = Ventilator()
print("[{}] Service menyala".format(
    datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
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
