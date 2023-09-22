# Temperature and Humidity Monitor
A simple application for monitoring temperature and humidity and notifying relevant personnel as needed. We leverage the [SHT45 Temperature and Humidity Sensor](https://www.adafruit.com/product/5665).

## Installation
First follow the instructions [here](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) for installing the adafruit Blinka liibrary on a raspberry pi. Once this is instal run the following to install all dependencies:

```
pip3 install -r requirements.txt
```

This app uses SendGrid to send e-mail notification, so if you have not already done so, be sure to make an account with SendGrid, and setup the desired sender e-mail account as a verified sender through SendGrid. You will also need to get a SendGrid Web API key and run the following code to create a script for exporting the key as an environment variable:

```
echo "export SENDGRID_API_KEY='YOUR_API_KEY'" > sendgrid.env
echo "sendgrid.env" >> .gitignore
```



## Usage
First edit the config file to reflect the necessary settings for a given raspberry pi. The sender should be an e-mail address that has been verified through SendGrid. The settings have the following meanings:

* `sender` - The e-mail address that notifications will be sent from.
* `receivers` - A list of e-mail addresses to send notifications to.
* `temp_range` - The normal range of temperatures in Celsius. Readings outside of this range will trigger a notification.
* `humidity_range` - The normal range of humidities in percentages. Readings outside of this range will trigger a notification.
* `interval` - Time interval in seconds between reads from the sensors


Before starting the app set up your environment by running:

```
source ./sendgrid.env
```

Finally run the following to start the app:

```
python3 main.py
```

The app stores all logs at `~/.temp_humidity_logs`.

