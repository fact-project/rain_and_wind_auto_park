#!/usr/bin/env python
"""
Rain Analysis

Usage:
  rain_analysis.py [options] <input_data>

Options:
  -h --help         Show this screen.
  -o FILE           plot file name, if not given, no plot is made
  --version         Show version.
  --start=TIME      start time cut
  --end=TIME        end time cut
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

def load_wind_data(path):
    df = pd.read_hdf(path)
    df = pd.DataFrame(df.v_max.resample("min").mean())
    df = join_with_schedules(df)
    return df


def wind_plots(data, outfile_name):

    figure, (ax1, ax2) = plt.subplots(
        nrows=2,
        sharex=True,
        figsize=(30, 15),
        gridspec_kw={"height_ratios": [3, 2]}
    )
    ax1.plot(
        data.v_max,
        ".",
        label="Wind Gust",
        alpha=0.5
    )
    ax1.plot(
        data["quantile"],
        ".:",
        label="Rolling 95% Quantile"
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
        # the boolean here needs to be inverted!
        (1 - data.actual_observation) + 0,
        ".:",
        label="Actual Schedule"
    )
    ax2.plot(
        data.quantile_park + 2,
        ".:",
        label="95% Quantile Decision",
    )
    ax2.plot(
        data.quantile_park2 + 4,
        ".:",
        label="90% Quantile Decision",
    )
    ax2.plot(
        data.quantile_park3 + 6,
        ".:",
        label="70% Quantile Decision",
    )

    ax2.legend(fontsize=18, loc="upper right")
    ax2.tick_params(axis="both", which="major", labelsize=18)
    ax2.set_yticks(list(range(8)))
    ax2.set_yticklabels(['park', 'observe', 'park', 'observe', 'park', 'observe', 'park', 'observe'])
    ax2.grid()

    figure.savefig(outfile_name, dpi=300, figsize=(120, 120))



def wind_main(
    input_data,
    outfile_name,
    start_time=None,
    end_time=None,
):
    data = load_wind_data(path=input_data)
    data = data[start_time: end_time]

    data["quantile"] = data.v_max.rolling("1h").quantile(0.95)
    data["quantile_park"] = calculate_hyst(data["quantile"], 40, 10)

    data["quantile2"] = data.v_max.rolling("1h").quantile(0.90)
    data["quantile_park2"] = calculate_hyst(data["quantile2"], 40, 10)

    data["quantile3"] = data.v_max.rolling("30min").quantile(0.70)
    data["quantile_park3"] = calculate_hyst(data["quantile3"], 40, 10)

    total_hours = len(data.planned_observation) / 60

    print("total_hours:", total_hours)
    data = data[data.planned_observation]
    wind_plots(data, outfile_name)

    data['park'] = data.quantile_park3
    interval_lengths = intervals(data.park)
    result = get_no_small_intervals(interval_lengths)
    print('intervals result:', result)
    return result


if __name__ == "__main__":

    arguments = docopt(__doc__, version="wind_analysis")

    wind_main(
        input_data=arguments["<input_data>"],
        outfile_name=arguments["-o"],
        start_time=arguments["--start"],
        end_time=arguments["--end"],
    )
