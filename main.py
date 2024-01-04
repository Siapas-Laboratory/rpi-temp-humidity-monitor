import board
import adafruit_sht4x
import json
import time
import logging
from datetime import datetime as dt
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
from utils import *
import traceback

eod_report_template = """Today the temperature was as follows:
Mean: {mean_temp: .3f}˚F
Min: {min_temp: .3f}˚F
Max: {max_temp: .3f}˚F

The humidity was as follows:
Mean: {mean_hum: .3f}%
Min: {min_hum: .3f}%
Max: {max_hum: .3f}%

<img src=\'data:image/png;base64,{plot}\'>
""".replace('\n', '<br>')

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
        self.log_dir = os.path.join(self.root_dir, self.room)
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
        self.log_filename = os.path.join(self.log_dir, f"{now.strftime('%m-%d-%Y.log')}")
        os.makedirs(self.log_dir, exist_ok = True) # create the log dir if needed

        self.logger = logging.getLogger()
        self.logger.handlers.clear() # clear any existing handlers
        self.logger.setLevel(logging.INFO)

        log_file_handler = logging.FileHandler(self.log_filename)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_file_handler.setFormatter(log_formatter)
        self.logger.addHandler(log_file_handler)
        self.date = dt.now().date()
        

    def start(self):
        self.notify(Event.STARTING)
        while True:
            try:
                # get current measurements
                _temp, self.humidity = self.sensor.measurements
                self.temp = (_temp * 9/5) + 32

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
                
                # log the measurements
                self.logger.info(f"Temperature (˚F): {self.temp}; Humidity (%): {self.humidity}")
                time.sleep(self.interval)

            except BaseException as e:
                tb = traceback.format_exc()
                self.logger.exception(e)
                self.notify(Event.ERROR, tb = tb)
                break

    def notify(self, event: Event, tb:str = ""):
        """
        function for notifying designated receivers when a specified event occurs
        """
        if event == Event.TEMP_OUT_OF_RANGE:
            subj = f"[TEMPERATURE WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"Temperature is out of range in room {self.room}. The current temperature reading is {self.temp:.3f} ˚F"
            self.logger.warning("Temperature out of range. Notifying...")
        elif event == Event.HUM_OUT_OF_RANGE:
            subj = f"[HUMIDITY WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"Humidity is out of range in room {self.room}. The current humidity reading is {self.humidity:.3f} %"
            self.logger.warning("Humidity out of range. Notifying...")
        elif event == Event.ERROR:
            tb = tb.replace('\n', '<br>')
            subj = f"[ERROR WARNING]: ROOM {self.room} - {dt.now().strftime('%m-%d-%Y %H:%M:%S')}"
            msg = f"The following message was caught on the pi in room {self.room}:<br><br>{tb}"
        elif event == Event.STARTING:
            subj = f"[START NOTIFICATION]: Room {self.room}"
            msg = f"Temperature and humidity monitor in room {self.room} has started successfully."
            self.logger.info("Starting monitor. Notifying...")
        elif event == Event.END_OF_DAY:
            subj = f"[END OF DAY REPORT]: Room {self.room} - {self.date.strftime('%m-%d-%Y')}"

            # plot temperatures and humidity over the course of the day
            fig, _, _, _, day_temps, day_humidities = plot_day_measurements(self.log_filename)
            tmp = BytesIO()
            fig.savefig(tmp, format = 'png')
            plot = base64.b64encode(tmp.getvalue()).decode('utf-8')
            plt.close(fig)

            msg = eod_report_template.format(
                mean_temp = sum(day_temps)/len(day_temps),
                mean_hum = sum(day_humidities)/len(day_humidities), 
                min_temp = min(day_temps), 
                min_hum = min(day_humidities),
                max_temp = max(day_temps),
                max_hum = max(day_humidities),
                plot = plot
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