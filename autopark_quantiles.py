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
from schedules import join_with_schedules, load_schedules_actual_planned

def load_wind_data(path):
    df = pd.read_hdf(path)
    df = pd.DataFrame(df.v_max.resample("min").mean())
    df = join_with_schedules(df)
    return df



def get_data(path):
    df = pd.read_hdf(path)
    df.set_index(pd.to_datetime(df.Time, unit="D"), inplace=True)
    df.sort_index(inplace=True)
    if "rain" in df:
        df = pd.DataFrame(df.rain.resample("min").mean())
    else:
        df = pd.DataFrame(df.v_max.resample("min").mean())

    df = join_with_schedules(df)
    return df


def determine_data_type(data):
    """ Distinguish between rain data and wind data.
    Set the right threshold, hysteresis minimum and window.
    """
    if "rain" in data:
        data_type = "rain"
        threshold = 0
        hyst_min = 10
        hyst_window = 10
        name = "Rain"
    else:
        data_type = "wind"
        threshold = 50
        hyst_min = 0
        hyst_window = 2
        name = "Wind Gust"
    return data_type, threshold, name
    # hyst_min, hyst_window, name


def add_rolling_sum__and__park(data, col, threshold, window_size, hyst_min, hyst_window):
    """Use a rolling sum above threshold to make a decision to park.
    """
    data["rolling_sum"] = (col > threshold).rolling(window_size).sum()
    data["park"] = calculate_hyst(data["rolling_sum"], hyst_min, hyst_window)
    return data


def attach_wind_methods(data, threshold, window_size):
    data["quantile"] = data.v_max.rolling("1h").quantile(0.95)
    data["quantile_park"] = calculate_hyst(data["quantile"], 40, 10)

    data["quantile2"] = data.v_max.rolling("1h").quantile(0.90)
    data["quantile_park2"] = calculate_hyst(data["quantile2"], 40, 10)

    data["quantile3"] = data.v_max.rolling("30min").quantile(0.70)
    data["quantile_park3"] = calculate_hyst(data["quantile3"], 40, 10)
    return data


def plots(data, col, start_time, end_time, hyst_min, hyst_window, name, outfile_name):

    f, (ax1, ax2) = plt.subplots(
        nrows=2, sharex=True, figsize=(30, 15), gridspec_kw={"height_ratios": [3, 2]}
    )
    sel = slice(start_time, end_time)

    ax1.plot(col[sel], ".", color="C0", label=name, alpha=0.5)
    # ax2.set_ylabel("Raininess (??)", fontsize = 18)
    ### Wind Specific######################################
    # try:
    # ax1.plot((data.rolling_gust[sel]), '.', color = "C1", label = ' Rolling Average + 2 $\sigma$ ')
    ax1.plot((data["quantile"][sel]), ".:", color="C5", label="Rolling 95% Quantile ")
    ax1.plot((data["quantile2"][sel]), ".:", color="C6", label="Rolling 90% Quantile")
    ax1.plot(
        (data["quantile3"][sel]),
        ".:",
        color="C2",
        label="Rolling 70% Quantile, 30 min ",
    )
    ax1.axhspan(40, 50, facecolor="C1", alpha=0.2)
    # ax2.plot((data.quantile[sel]), '.', color = "C5", label = '.95 Quantile')
    # ax2.plot((data.quantile2[sel]), '.', color = "C6", label = '.90 Quantile')

    ax1.set_ylabel("Wind Speed (km/h)", fontsize=18)

    # except:
    #    pass
    ###########################################################
    ax1.legend(fontsize=18, loc="upper right")
    ax1.tick_params(axis="both", which="major", labelsize=18)
    ax1.grid()

    # ax2.plot(((data[sel].park_avg_plus_std)+8), '.:', color = "C2", label = "  Rolling Sum Decision")
    ax2.plot(((data[sel].actual_observation) + 6), ".:", color="C4", label="Actual Schedule")

    ### Wind Specific##################################################################################
    try:
        ax2.plot(
            ((data[sel].quantile_park3) + 4),
            ".:",
            color="C2",
            label="70% Quantile Decision",
        )
        ax2.plot(
            ((data[sel].quantile_park) + 2),
            ".:",
            color="C5",
            label="95% Quantile Decision",
        )
        ax2.plot(
            ((data[sel].quantile_park2) + 0),
            ".:",
            color="C6",
            label="90% Quantile Decision",
        )

    except:
        pass
    ###################################################################################################
    ax2.legend(fontsize=18, loc="upper right")
    ax2.tick_params(axis="both", which="major", labelsize=18)
    ax2.set_yticklabels([])
    ax2.grid()

    #    f.savefig('Wind_gust_Jan_comparison_part2.png', dpi = 300, figsize = (120,120))

    ########## more general comparison plots
    # def plots(data, col,  start_time  , end_time  , hyst_min, hyst_window, name ):
    #
    #     f, (ax1, ax2, ax3) = plt.subplots(nrows =3,sharex = True, figsize = (30,15),gridspec_kw={'height_ratios': [1,3, 2]} )
    #     sel = slice(start_time, end_time)
    #
    #     ax1.plot((data.rolling_sum[sel]), '.', label = 'Rolling Sum Method: Events Above 50 km/h', color = "C2")
    #     ax1.axhspan(hyst_min, hyst_min + hyst_window, facecolor = "C2", alpha = 0.2)
    #     ax1.tick_params(axis = 'both', which = "major", labelsize = 18)
    #     ax1.legend(fontsize = 18, loc = "upper right")
    #     ax1.grid()
    #
    #
    #
    #     ax2.plot(col[sel], '.',color = "C0",  label = name)
    #     #ax2.set_ylabel("Raininess (??)", fontsize = 18)
    # ### Wind Specific######################################
    #     try:
    #         ax2.plot((data.rolling_gust[sel]), '.', color = "C1", label = ' Rolling Average + 2 $\sigma$ ')
    #         ax2.axhspan(40, 50, facecolor = "C1", alpha = 0.2)
    #         #ax2.plot((data.quantile[sel]), '.', color = "C5", label = '.95 Quantile')
    #         #ax2.plot((data.quantile2[sel]), '.', color = "C6", label = '.90 Quantile')
    #         ax2.set_ylabel("Wind Speed (km/h)", fontsize = 18)
    #
    #     except:
    #         pass
    # ###########################################################
    #     ax2.legend(fontsize = 18, loc = "upper right")
    #     ax2.tick_params( axis = 'both', which = "major", labelsize = 18)
    #     ax2.grid()
    #
    #
    #
    #     ax3.plot(((data[sel].park_avg_plus_std)+8), '.:', color = "C2", label = "  Rolling Sum Decision")
    #     ax3.plot(((data[sel].actual_observation)+6), '.:', color ="C4", label = "Actual Schedule")
    #
    # ### Wind Specific##################################################################################
    #     try:
    #     #    ax3.plot(((data[sel].shifter_dec)+2), '.:', color = "C0" , label = "Mock Shifter Decision")
    #         ax3.plot(((data[sel].park2)+4), '.:', color = "C1" , label = "Rolling Avg + 2$\sigma$ Decision")
    #
    #         ax3.plot(((data[sel].quantile_park)+2), '.:', color = "C5" , label = ".95 Quantile Decision")
    #         ax3.plot(((data[sel].quantile_park2)+0), '.:', color = "C6" , label = ".90 Quantile Decision")
    #
    #     except:
    #         pass
    # ###################################################################################################
    #     ax3.legend(fontsize = 18, loc = "upper right")
    #     ax3.tick_params( axis = 'both', which = "major", labelsize = 18)
    #     ax3.set_yticklabels([])
    #     ax3.grid()
    #
    #
    #
    f.savefig(outfile_name, dpi=300, figsize=(120, 120))


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
    window_size=10
):
    """Run all the functions above to obtain plots
    """
    data = load_wind_data(path=input_data)
    data = data[start_time: end_time]

    threshold = 50

    data = attach_wind_methods(data, threshold, window_size)
    total_hours = (len(data.planned_observation)) / 60

    print("total_hours:", total_hours)
    data = data[data.planned_observation]
    wind_plots(data, outfile_name)

    data['park'] = data.quantile_park3
    interval_lengths = intervals(data.park)
    result = get_no_small_intervals(interval_lengths)
    return result


def rain_main(
    input_data, start_time, end_time, window_size, hyst_min, hyst_window, outfile_name
):
    """Run all the functions above to obtain plots
    """
    data = get_data(input_data)
    data = data[start_time: end_time]
    type, threshold, name = determine_data_type(data)
    # hyst_min, hyst_window,
    if type == "rain":
        col = data.rain
    else:
        col = data.v_max
        data = attach_wind_methods(data, threshold, window_size)
    data = add_rolling_sum__and__park(data, col, threshold, window_size, hyst_min, hyst_window)
    data1 = data[data.planned_observation == True]
    plots(data1, col, start_time, end_time, hyst_min, hyst_window, name, outfile_name)

    interval_lengths = intervals(data1.park)
    result = get_no_small_intervals(interval_lengths)
    total_hours = (len(data.planned_observation)) / 60
    actual_data_taken = data[data.actual_observation == False]
    actual_hours = len(actual_data_taken)
    print("total_hours:", total_hours)
    return result

if __name__ == "__main__":

    arguments = docopt(__doc__, version="autopark 0.3")
    if 'wind' in arguments["<input_data>"]:

        wind_main(
            input_data=arguments["<input_data>"],
            outfile_name=arguments["<outfile_name>"],
            start_time=arguments["<start_time>"],
            end_time=arguments["<end_time>"],
        )
    else:
        rain_main(
            input_data=arguments["<input_data>"],
            # number_of_steps=int(arguments['<number_of_steps>']),
            start_time=arguments["<start_time>"],
            end_time=arguments["<end_time>"],
            window_size=int(arguments["<window_size>"]),
            hyst_min=int(arguments["<hyst_min>"]),
            hyst_window=int(arguments["<hyst_window>"]),
            outfile_name=arguments["<outfile_name>"],
        )
