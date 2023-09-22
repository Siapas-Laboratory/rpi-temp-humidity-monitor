import board
import adafruit_sht4x
import json
import time
import logging
from datetime import datetime as dt
import os
from enum import Enum
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class Event(Enum):
    TEMP_OUT_OF_RANGE = 1
    HUM_OUT_OF_RANGE = 2
    ERROR = 3

class Monitor:
    def __init__(self):
        with open("config.json", "r") as f:
            config = json.load(f)
        for k, v in config.items():
            setattr(self, k, v)

        self.sensor = adafruit_sht4x.SHT4x(board.I2C())
        self.temp, self.humidity = self.sensor.measurements
        self.temp_out_of_range = not (self.temp_range[0] < self.temp < self.temp_range[1])
        self.hum_out_of_range = not (self.humidity_range[0] < self.humidity < self.humidity_range[1])

        self.get_new_logger()


    def get_new_logger(self):
        """
        create a new logger for logging information
        this gets called at the start of everyday to
        create a new log file
        """

        now = dt.now()
        self.date = now.date()
        # get the new log directory
        log_dir = os.path.join(os.path.expanduser('~'), ".temp-humidity-logs", str(now.year), now.strftime("%m-%Y"))
        log_filename = os.path.join(log_dir, f"{now.strftime('%m-%d-%Y.log')}")
        os.makedirs(log_dir, exist_ok = True) # create the log dir if needed

        self.logger = logging.getLogger()
        self.logger.handlers.clear() # clear any existing handlers
        self.logger.setLevel(logging.INFO)

        log_file_handler = logging.FileHandler(log_filename)
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file_handler.setFormatter(log_formatter)
        self.logger.addHandler(log_file_handler)
        self.logger.addHandler(logging.StreamHandler())

    def start(self):
        while True:
            try:
                # get current measurements
                self.temp, self.humidity = self.sensor.measurements

                # check if the measurements are in range and notify if necessary
                # temperature
                if not (self.temp_range[0] < self.temp < self.temp_range[1]):
                    if not self.temp_out_of_range:
                        # if we were not already out of range notify
                        self.temp_out_of_range = True
                        self.notify(Event.TEMP_OUT_OF_RANGE)
                else:
                    self.temp_out_of_range = False
                #humidity
                if not (self.humidity_range[0] < self.humidity < self.humidity_range[1]):
                    if not self.hum_out_of_range:
                        # if we were not already out of range notify
                        self.hum_out_of_range = True
                        self.notify(Event.HUM_OUT_OF_RANGE)
                else:
                    self.hum_out_of_range = False

                # if it's a new day create a new log file
                if dt.now().date() != self.date: 
                    self.get_new_logger()

                # log the measurements
                self.logger.info(f"Temperature (C): {self.temp}; Humidity (%): {self.humidity}")
                time.sleep(self.interval)

            except Exception as e:
                self.notify(Event.ERROR, err_msg = str(e))

    def notify(self, event: Event, err_msg = "Error"):
        """
        function for notifying designated receivers when a specified event occurs
        """
        if event == Event.TEMP_OUT_OF_RANGE:
            subj = f"[TEMPERATURE WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"Temperature is out of range in room {self.room}. The current temperature reading is {self.temp:.3f} ˚C"
            self.logger.warning("Temperature out of range. Notifying...")
        elif event == Event.HUM_OUT_OF_RANGE:
            subj = f"[HUMIDITY WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"Humidity is out of range in room {self.room}. The current humidity reading is {self.humidity:.3f} %"
            self.logger.warning("Humidity out of range. Notifying...")
        elif event == Event.ERROR:
            subj = f"[ERROR WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"The following message was caught on the pi in room {self.room}:\n{err_msg}"
            self.logger.warning("Error caught: {err_msg}. Notifying...")
        
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        for receiver in self.receivers:
            try:
                email = Mail(from_email = self.sender, 
                             to_emails = receiver,
                             subject = subj,
                             html_content = msg)
                response = sg.send(email)
                # TODO: look into status codes to make sure the status is success
            except Exception as e:
                self.logger.warning(f"Error caught while notifying {receiver}: {str(e)}")

if __name__  == '__main__':
    
    m = Monitor()
    m.start()

