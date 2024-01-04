from enum import Enum
from datetime import datetime, date, timedelta
import typing
import os
import matplotlib.figure
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


class Event(Enum):
    TEMP_OUT_OF_RANGE = 1
    HUM_OUT_OF_RANGE = 2
    ERROR = 3
    STARTING = 4
    END_OF_DAY = 5

def read_logfile(fpath: typing.Union[str, os.PathLike] ) -> typing.Tuple[list, list, list]:
    """
    read the temperature and humdity logs in a provided file

    Args:
        fpath: typing.Union[str, os.PathLike]
            path to the logfile to read

    Returns:
        times: list
            list of datetimes corresponding to temperature
            and humidity readings
        temps: list
            list of temperatures in farenheit
        hums: list
            list of humidities
    """

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
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                ts = ts + timedelta(milliseconds = float(ms))
                
                times.append(ts)
                temps.append(temp)
                hums.append(hum)
    return times, temps, hums

def plot_day_measurements(fpath: typing.Union[str, os.PathLike], 
                          show:bool = False)-> typing.Tuple[matplotlib.figure.Figure, plt.Axes, plt.Axes, list, list, list]:
    """
    read the temperature and humdity logs in a provided file
    and plot the measurements over time

    Args:
        fpath: typing.Union[str, os.PathLike]
            path to the logfile to read
        show: bool (optional)
            whether or not to show the figure (defaults: False)

    Returns:
        fig: matplotlib.figure.Figure
            the figure containing the plot
        ax: plt.Axes
            axis for temperature plot
        ax2: plt.Axes
            axis for humidity plot
        times: list
            list of datetimes corresponding to temperature
            and humidity readings
        temps: list
            list of temperatures in farenheit
        hums: list
            list of humidities
    """

    times, temps, hums = read_logfile(fpath)
    fig, ax = plt.subplots(1,1)
    ax.plot(times, temps, color = 'b')
    ax2 = ax.twinx()
    ax2.plot(times, hums, color = 'r')
    ax2.set_ylabel("Humidity (%)", color = 'r')
    ax.set_ylabel("Temperature (˚F)", color = 'b')
    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[15,30,45]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%-I%p'))
    for l in ax.xaxis.get_ticklabels()[::2] + ax.xaxis.get_ticklabels()[1::4]: 
        l.set_visible(False)
    if show: fig.show()
    return fig, ax, ax2, times, temps, hums
    
def get_daily_stats(func: typing.Callable, start: date, n_days: int, 
                    root_dir: typing.Union[str, os.PathLike]) -> typing.Tuple[list, list, list]:
    """
    get stats for each day of a span of days

    Args:
        func: typing.Callable
            function to summarize the readings on a given day
        start: date
            datetime.date object indicating the start date
        n_days: int
            number of days to get stats for
        root_dir: typing.Union[str, os.PathLike]
            directory containing the logfiles

    Returns:
        existing_dates: list
            list of dates in the specified range for which data was found
        temps: list
            list of stats computed for the temperatures in farenheit
        hums: list
            list of stats computed for the humidities
    """

    dates = [start + timedelta(days = n) for n in range(n_days)]
    files = [os.path.join(root_dir, d.strftime('%m-%d-%Y.log')) for d in dates]
    existing_dates = []
    temps = []
    hums = []
    for d, f in zip(dates, files):
        if os.path.exists(f):
            _, _temps, _hums = read_logfile(f)
            existing_dates.append(d)
            temps.append(func(_temps))
            hums.append(func(_hums))
    
    return existing_dates, temps, hums

def plot_daily_stats(func: typing.Callable, start: date, n_days: int, 
                     root_dir: typing.Union[str, os.PathLike]):
    """
    ploy stats for each day of a span of days

    Args:
        func: typing.Callable
            function to summarize the readings on a given day
        start: date
            datetime.date object indicating the start date
        n_days: int
            number of days to get stats for
        root_dir: typing.Union[str, os.PathLike]
            directory containing the logfiles
    """

    dates, temps, hums = get_daily_stats(func, start, n_days, root_dir)
    fig, ax = plt.subplots(1,1)
    ax.plot(dates, temps, c = 'b')
    ax2 = ax.twinx()
    ax2.plot(dates, hums, c = 'r')
    ax.set_ylabel("Temperature (˚F)", c = 'b')
    ax2.set_ylabel("Humidity (%)", c = 'r')
    fig.show()

def plot_daily_means(start: date, n_days: int, root_dir: typing.Union[str, os.PathLike]):
    """
    convenience function for plotting daily means

    Args:
        start: date
            datetime.date object indicating the start date
        n_days: int
            number of days to get stats for
        root_dir: typing.Union[str, os.PathLike]
            directory containing the logfiles
    """
    plot_daily_stats(lambda x: sum(x)/len(x), start, n_days, root_dir)


def plot_daily_mins(start: date, n_days: int, root_dir: typing.Union[str, os.PathLike]):
    """
    convenience function for plotting daily mins

    Args:
        start: date
            datetime.date object indicating the start date
        n_days: int
            number of days to get stats for
        root_dir: typing.Union[str, os.PathLike]
            directory containing the logfiles
    """
    plot_daily_stats(min, start, n_days, root_dir)

def plot_daily_maxes(start: date, n_days: int, root_dir: typing.Union[str, os.PathLike]):
    """
    convenience function for plotting daily maxes

    Args:
        start: date
            datetime.date object indicating the start date
        n_days: int
            number of days to get stats for
        root_dir: typing.Union[str, os.PathLike]
            directory containing the logfiles
    """
    plot_daily_stats(max, start, n_days, root_dir)