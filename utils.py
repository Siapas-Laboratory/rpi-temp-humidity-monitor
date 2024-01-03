from enum import Enum
from datetime import datetime as dt
from datetime import timedelta

class Event(Enum):
    TEMP_OUT_OF_RANGE = 1
    HUM_OUT_OF_RANGE = 2
    ERROR = 3
    STARTING = 4
    END_OF_DAY = 5

def read_logfile(fpath):
    times = []
    temps = []
    hums = []
    with open(fpath, 'r') as f:
        for line in f:
            if 'INFO' in line and 'Temperature' in line:
                a, hum = line.split(';')
                ts, temp = a.split(' - INFO - ')
                tlabel, temp = temp.split(':')
                temp = float(temp)
                if 'C' in tlabel:
                    temp = (temp * 9/5) + 32
                _, hum = hum.split(':')
                hum = float(hum)
                ts, ms = ts.split(',')
                ts = dt.strptime(ts, "%Y-%m-%d %H:%M:%S")
                ts = ts + timedelta(milliseconds = float(ms))

                times.append(ts)
                temps.append(temp)
                hums.append(hum)
    return times, temps, hums
                
