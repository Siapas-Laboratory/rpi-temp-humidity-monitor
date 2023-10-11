# Temperature and Humidity Monitor
A simple application for monitoring temperature and humidity and notifying relevant personnel as needed. We leverage the [SHT45 Temperature and Humidity Sensor](https://www.adafruit.com/product/5665).

## Installation
First follow the instructions [here](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi) for installing the adafruit Blinka liibrary on a raspberry pi. Once this is instal run the following to install all dependencies:

```
pip3 install -r requirements.txt
```

This app uses SendGrid to send e-mail notification, so if you have not already done so, be sure to make an account with SendGrid, and setup the desired sender e-mail account as a verified sender through SendGrid. You will also need to get a SendGrid Web API key and run the following code to create a script for exporting the key as an environment variable:

```
echo "YOUR_API_KEY" > sendgrid.env
echo "sendgrid.env" >> .gitignore
```



## Usage
First create a config file called `config.json` to reflect the necessary settings for a given raspberry pi. The sender should be an e-mail address that has been verified through SendGrid. The settings have the following meanings:

* `sender` - The e-mail address that notifications will be sent from.
* `receivers` - A list of e-mail addresses to send notifications to.
* `temp_range` - The normal range of temperatures in Celsius. Readings outside of this range will trigger a notification.
* `humidity_range` - The normal range of humidities in percentages. Readings outside of this range will trigger a notification.
* `interval` - Time interval in seconds between reads from the sensors


The following is a sample config file:

```
{
    "root_dir": "path/to/root/for/logs"
    "room": "Room-Name",
    "sender": "sender@gmail.com",
    "receivers": ["receiver1@gmail.com", "receiver2@gmail.com"],
    "temp_range": [20, 30],
    "humidity_range": [30, 50],
    "interval": 300
}
```

Run the following to start the app in the background:

```
nohup python3 main.py &
```

The app stores all logs at `~/.temp_humidity_logs`.

To check that the script is still running, run:

```
ps ax | grep main.py
```

