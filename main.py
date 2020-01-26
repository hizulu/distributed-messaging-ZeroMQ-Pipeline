from log import Log
from ventilator import Ventilator
import time
import json
import sys
import env


log = Log()
ven = Ventilator()
task = log.getUnproceessLog()
if(task['execute_status']):
    if(task['data']):
        startTime = int(round(time.time() * 1000))
        ven.send(task['data'])
        print("start time : {}".format(startTime))
        sys.exit()
else:
    print('Error retrieving data')
