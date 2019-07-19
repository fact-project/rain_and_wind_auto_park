#!/usr/bin/env python
"""
Wind Analysis

Usage:
  wind_analysis.py [options] <input_data>

Options:
  -h --help         Show this screen.
  -o FILE           plot file name, if not given, no plot is made
  --version         Show version.
  --start=TIME      start time cut
  --end=TIME        end time cut
  --centered        if set, apply the rolling function in a centered manner
"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from docopt import docopt
from tools import calculate_hyst, intervals, get_no_small_intervals
from schedules import join_with_schedules


def load_wind_data(path):
    df = pd.read_hdf(path)
    df.rename(columns={'v_max':'v'}, inplace=True)
    df = pd.DataFrame(df.v.resample("min").mean())
    df[df.v == 0] = np.nan
    df = join_with_schedules(df)
    return df


def wind_plots(data, outfile_name):

    figure, (ax1, ax2) = plt.subplots(
        nrows=2, sharex=True, figsize=(30, 15), gridspec_kw={"height_ratios": [3, 2]}
    )
    ax1.plot(data.v, ".", label="Wind Gust", alpha=0.5)
    ax1.plot(data.quantile1, ".:", label="Rolling 95% Quantile")
    ax1.plot(data.quantile2, ".:", label="Rolling 90% Quantile")
    ax1.plot(data.quantile3, ".:", label="Rolling 70% Quantile, 30 min ")
    ax1.axhspan(40, 50, facecolor="C1", alpha=0.2)
    ax1.set_ylabel("Wind Speed (km/h)", fontsize=18)
    ax1.legend(fontsize=18, loc="upper right")
    ax1.tick_params(axis="both", which="major", labelsize=18)
    ax1.grid()

    ax2.plot(
        # the boolean here needs to be inverted!
        data.actual_observation + 0,
        ".:",
        label="Actual Schedule",
    )
    ax2.plot((1 - data.quantile1_park) + 2, ".:", label="95% Quantile Decision")
    ax2.plot((1 - data.quantile2_park) + 4, ".:", label="90% Quantile Decision")
    ax2.plot((1 - data.quantile3_park) + 6, ".:", label="70% Quantile Decision")

    ax2.legend(fontsize=18, loc="upper right")
    ax2.tick_params(axis="both", which="major", labelsize=18)
    ax2.set_yticks(list(range(8)))
    ax2.set_yticklabels(
        ["park", "observe", "park", "observe", "park", "observe", "park", "observe"]
    )
    ax2.grid()

    figure.savefig(outfile_name, dpi=300, figsize=(120, 120))


def wind_main(
    input_data,
    outfile_name=None,
    start_time=None,
    end_time=None,
    centered=False,
):
    data = load_wind_data(path=input_data)

    tasks = [
        ("quantile1", "1h", 0.95, 40, 10),
        ("quantile2", "1h", 0.90, 40, 10),
        ("quantile3", "30min", 0.70, 40, 10),
    ]

    if not centered:
        for name, window, percent, hyst_min, hyst_width in tasks:
            data[name] = data.v.rolling(window).quantile(percent)
            data[name+"_park"] = calculate_hyst(data[name], hyst_min, hyst_width)

    else:
        for name, window, percent, hyst_min, hyst_width in tasks:
            data[name] = data.v.rolling(min_periods=1, center=True, window=window).quantile(percent)
            data[name+"_park"] = calculate_hyst(data[name], hyst_min, hyst_width)

    data = data[start_time:end_time]
    hours_of_planned_observation = data.planned_observation.sum() / 60
    data = data[data.planned_observation]

    if outfile_name:
        wind_plots(data, outfile_name)

    data["park"] = data.quantile3_park
    interval_lengths = intervals(data.park)
    result = get_no_small_intervals(interval_lengths)

    return result, hours_of_planned_observation


if __name__ == "__main__":

    arguments = docopt(__doc__, version="wind_analysis")


    result, hours_of_planned_observation = wind_main(
        input_data=arguments["<input_data>"],
        outfile_name=arguments["-o"],
        start_time=arguments["--start"],
        end_time=arguments["--end"],
        centered=arguments["--centered"]
    )
    print("intervals result:", result)
    print("hours of planned observation:", hours_of_planned_observation)
