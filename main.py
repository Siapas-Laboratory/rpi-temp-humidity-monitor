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


eod_report_template = """
Today the temperature was as follows:
Mean: {mean_temp: .3f}
Min: {min_temp: .3f}
Max: {max_temp: .3f}

The humidity was as follows:
Mean: {mean_hum: .3f}
Min: {min_hum: .3f}
Max: {max_hum: .3f}
"""

class Event(Enum):
    TEMP_OUT_OF_RANGE = 1
    HUM_OUT_OF_RANGE = 2
    ERROR = 3
    STARTING = 4
    END_OF_DAY = 5

class Monitor:
    def __init__(self):
        with open("config.json", "r") as f:
            config = json.load(f)
        for k, v in config.items():
            setattr(self, k, v)

        self.sensor = adafruit_sht4x.SHT4x(board.I2C())
        self.temp = None
        self.humidity = None
        self.temp_out_of_range = False
        self.hum_out_of_range = False
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
        log_dir = os.path.join(self.root_dir, self.room, str(now.year), now.strftime("%m-%Y"))
        log_filename = os.path.join(log_dir, f"{now.strftime('%m-%d-%Y.log')}")
        os.makedirs(log_dir, exist_ok = True) # create the log dir if needed

        self.logger = logging.getLogger()
        self.logger.handlers.clear() # clear any existing handlers
        self.logger.setLevel(logging.INFO)

        log_file_handler = logging.FileHandler(log_filename)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_file_handler.setFormatter(log_formatter)
        self.logger.addHandler(log_file_handler)

        self.day_temps = []
        self.day_humidities = []

    def start(self):
        self.notify(Event.STARTING)
        while True:
            try:
                # get current measurements
                self.temp, self.humidity = self.sensor.measurements
                self.day_temps.append(self.temp)
                self.day_humidities.append(self.humidity)

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
                    self.notify(Event.END_OF_DAY)
                    self.get_new_logger()
                    self.day_temps = []
                    self.day_humidities = []

                # log the measurements
                self.logger.info(f"Temperature (C): {self.temp}; Humidity (%): {self.humidity}")
                time.sleep(self.interval)

            except BaseException as e:
                self.notify(Event.ERROR, err_msg = str(e))
                break

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
            self.logger.warning(f"Error caught: {err_msg}. Notifying...")
        elif event == Event.STARTING:
            subj = f"[START NOTIFICATION]: Room {self.room}"
            msg = f"Temperature and humidity monitor in room {self.room} has started successfully."
            self.logger.info("Starting monitor. Notifying...")
        elif event == Event.END_OF_DAY:
            subj = f"[END OF DAY REPORT]: Room {self.room} - {self.date.strftime('%m-%d-%Y')}"

            msg = eod_report_template.format(
                mean_temp = sum(self.day_temps)/len(self.day_temps),
                mean_hum = sum(self.day_humidities)/len(self.day_humidities), 
                min_temp = min(self.day_temps), 
                min_hum = min(self.day_humidities),
                max_temp = max(self.day_temps)
                max_hum = max(self.day_humidities)
                )
                
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        for receiver in self.receivers:
            try:
                email = Mail(from_email = self.sender, 
                             to_emails = receiver,
                             subject = subj,
                             html_content = msg)
                response = sg.send(email)
                # TODO: look into status codes to make sure the status is success
            except BaseException as e:
                self.logger.warning(f"Error caught while notifying {receiver}: {str(e)}")

if __name__  == '__main__':
    with open("sendgrid.env", 'r') as f:
        os.environ["SENDGRID_API_KEY"] = f.readline()
    m = Monitor()
    m.start()

