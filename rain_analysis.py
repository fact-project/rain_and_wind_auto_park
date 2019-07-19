#!/usr/bin/env python
"""
Program to decide whether FACT should autopark based on weather conditions.
The plots compare quantile methods 90%, 95% and 70%(has smaller window)


<input_data>   for example "foo.h5"
<start_time>  specify start of time interval
<end_time>  specify end of time interval
<window_size> specify the number of minutes for the rolling sum



Usage:
  autopark_quantiles.py <input_data> <start_time> <end_time> <window_size> <hyst_min> <hyst_window> <outfile_name>

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import matplotlib.pyplot as plt
import pandas as pd
from docopt import docopt
from tools import (
    calculate_hyst,
    intervals,
    get_no_small_intervals,
)
from schedules import join_with_schedules

def load_rain_data(path):
    df = pd.read_hdf(path)
    df = pd.DataFrame(df.rain.resample("min").mean())
    df = join_with_schedules(df)
    return df


def rain_plots(data, outfile_name):

    figure, (ax1, ax2) = plt.subplots(
        nrows=2, sharex=True, figsize=(30, 15), gridspec_kw={"height_ratios": [3, 2]}
    )

    ax1.plot(
        data.rain,
        ".",
        label="Rain",
        alpha=0.5
    )
    ax1.plot(
        data["quantile"],
        ".:",
        label="Rolling 95% Quantile "
    )
    ax1.plot(
        data.quantile2,
        ".:",
        label="Rolling 90% Quantile"
    )
    ax1.plot(
        data.quantile3,
        ".:",
        label="Rolling 70% Quantile, 30 min ",
    )
    ax1.axhspan(40, 50, facecolor="C1", alpha=0.2)
    ax1.set_ylabel("Wind Speed (km/h)", fontsize=18)
    ax1.legend(fontsize=18, loc="upper right")
    ax1.tick_params(axis="both", which="major", labelsize=18)
    ax1.grid()


    ax2.plot(
        data.actual_observation + 6,
        ".:",
        color="C4",
        label="Actual Schedule"
    )
    ax2.legend(fontsize=18, loc="upper right")
    ax2.tick_params(axis="both", which="major", labelsize=18)
    ax2.set_yticklabels([])
    ax2.grid()

    figure.savefig(outfile_name, dpi=300, figsize=(120, 120))


def rain_main(
    input_data,
    start_time,
    end_time,
    window_size,
    hyst_min,
    hyst_window,
    outfile_name
):
    data = load_rain_data(input_data)
    data = data[start_time: end_time]

    threshold = 0
    data["rolling_sum"] = (data.rain > threshold).rolling(window_size).sum()
    data["park"] = calculate_hyst(data["rolling_sum"], hyst_min, hyst_window)

    total_hours = len(data.planned_observation) / 60

    data = data[data.planned_observation == True]

    rain_plots(data, outfile_name)
    interval_lengths = intervals(data.park)
    result = get_no_small_intervals(interval_lengths)

    print("total_hours:", total_hours)
    print("intervals result:", result)
    return result

if __name__ == "__main__":

    arguments = docopt(__doc__, version="rain_analysis")
    rain_main(
        input_data=arguments["<input_data>"],
        start_time=arguments["<start_time>"],
        end_time=arguments["<end_time>"],
        window_size=int(arguments["<window_size>"]),
        hyst_min=int(arguments["<hyst_min>"]),
        hyst_window=int(arguments["<hyst_window>"]),
        outfile_name=arguments["<outfile_name>"],
    )
