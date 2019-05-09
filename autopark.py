#!/usr/bin/env python
'''
Program to decide whether FACT should autopark based on weather conditions.
Various methods are included for comparison. The preferred method uses hysteresis.
Plots these columns.


<input_data>   for example "foo.h5"
<start_time>  specify start of time interval
<end_time>  specify end of time interval
<window_size> specify the number of minutes for the rolling sum
<hyst_min>


Usage:
  autopark.py <input_data> <start_time> <end_time> <window_size> <hyst_min> <hyst_window>


Options:
  -h --help     Show this screen.
  --version     Show version.
'''



import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.table import Table
import astropy
from docopt import docopt
from matplotlib import get_backend
from matplotlib import interactive
get_backend()
interactive(True)

def get_data(input_data ):
    '''get data and clean it up for operation.
    If it is rain data, resample it so that there is one data point per minute.
    If it is wind data, delete an additional column
    '''
    ## all_rain_data.h5 or all_wind_data.h5
    stuff = pd.read_hdf(input_data)
    stuff['good_time'] = pd.to_datetime(stuff.Time*24*60*60*1e9)
    stuff.set_index('good_time', inplace=True)
    stuff.sort_index(inplace=True)
    del stuff['QoS']
    del stuff['Time']
    if 'rain' in stuff:
        resampled = pd.DataFrame()
        resampled['rain'] = stuff.rain.resample('min').mean()
        resampled['count'] = stuff['count'].resample('min').mean()
        stuff = resampled

    else:
        del stuff['stat']
    return stuff


def get_column( data):
    ''' Get the column 'rain' for the rain data, and 'v' for wind data.
    Set the right threshold.
    '''
    if 'rain' in data:
        col = data['rain']
        threshold = 0

    else:
        col = data['v']
        threshold = 50

    return col, threshold


def calculate_rolling( data, col, threshold,  window_size):
    '''Calculate the rolling sum or average
    '''
    if 'rain' in data:
        data['above_threshold'] = np.where(col > threshold, True, False)
    ### the rolling sum below has 39 "nan" items in the beginning, we get rid of those.
        col_rolling = data['rolling_sum'] = data.above_threshold.rolling(window_size).sum().fillna(0)
        col_sigma = 0

    else:
        col_rolling2 = data['rolling_avg'] = data.v.rolling(window_size).mean().fillna(0)
        col_sigma2 = data['rolling_sig'] = data.v.rolling(window_size).std().fillna(0)
        shifter = data['shifter_dec'] = False
        data.shifter_dec["2019-03-09 18:15":"2019-03-09 23:30"] = True
        data.shifter_dec["2019-02-14 03:20":"2019-02-15 02:30"] = True
        data.shifter_dec["2019-02-22 01:50":"2019-02-22 16:15"] = True
        data.shifter_dec["2018-12-24 21:45":"2018-12-25 01:00"] = True
        data.shifter_dec["2018-11-03 04:00":"2018-11-03 05:30"] = True
        #March 2018
        data.shifter_dec["2018-03-03 09:30":"2018-03-03 10:45"] = True
        data.shifter_dec["2018-03-03 11:20":"2018-03-03 13:00"] = True
        data.shifter_dec["2018-03-03 15:45":"2018-03-03 19:30"] = True
        data.shifter_dec["2018-03-09 06:25":"2018-03-09 17:45"] = True
        #February 2018
        data.shifter_dec["2018-02-25 06:10":"2018-02-25 23:50"] = True ## Data is gone for part of this!
        data.shifter_dec["2018-02-26 23:30":"2018-02-27 06:45"] = True
        data.shifter_dec["2018-02-27 08:55":"2018-03-01 02:00"] = True
        #January 2018
        data.shifter_dec["2018-01-01 19:24":"2018-01-02 23:30"] = True
        data.shifter_dec["2018-01-04 02:15":"2018-01-04 03:30"] = True
        data.shifter_dec["2018-01-15 21:24":"2018-01-16 03:30"] = True
        data.shifter_dec["2018-01-16 10:55":"2018-01-16 14:00"] = True
        data.shifter_dec["2018-01-27 11:30":"2018-01-27 12:45"] = True
        data.shifter_dec["2018-01-30 10:20":"2018-01-30 12:00"] = True








        # shifter = []
        # calls = 0
        # for wind in col:
        #     if wind > threshold:
        #         calls =+ 1
        #         if calls >2:
        #             shifter.append(True)
        #         else:
        #             shifter.append(False)

#These are actually the max and min of the rolling mean band
        col_rolling = col_rolling2 +(col_sigma2 *2 )
        col_sigma = col_rolling2 +(col_sigma2)



    return col_rolling, col_sigma , col_rolling2 , shifter



def calculate_hyst(rolling, hyst_min, hyst_window):
    '''Double windows on y axis using the rolling sum from above
    '''
#    rolling = data['rolling_sum']
    hyst = []
    hyst_max = hyst_min + hyst_window
    for i in rolling:
        if i <= hyst_min:
            hyst.append(False)
        elif i >= hyst_max:
            hyst.append(True)
        elif (i >= hyst_min) & (i <= hyst_max):
            hyst.append(3)
        else:
            print("enteresan!")
    for i,bool in enumerate(hyst):
        if bool == 3:
            hyst[i] = hyst[i-1]
        else:
            pass
    #data["hysteresis_rain"] = rain_hyst
    new_column = pd.Series( hyst, index = rolling.index )
    return new_column

def intervals(data_column):
    list_of_intervals = []
    true = 0
    false = 0
    for unit in data_column:
        if unit == False:
            false += 1
            if true != 0:
                list_of_intervals.append(true)
            true = 0
        else:
            true += 1
            if false != 0:
                list_of_intervals.append(false)
            false = 0
    return list_of_intervals

def get_no_small_intervals(intv_list):
    small_intervals = []
    medium_intervals = []
    for i in np.array(intv_list):
        if i <= 20:
            small_intervals.append(i)
        if 10 <= i <= 20:
            medium_intervals.append(i)
    return len(small_intervals)
    #return ("number of intervals < 10 : ",len(small_intervals), " and intervals btwn 10 and 15:", len(medium_intervals))





def plots(data, rol_sum, rol_sig, avgreal, intervals, start_time  , end_time   ):


    f, (ax1, ax2) = plt.subplots(nrows =2,sharex = True, figsize = (30,15))
    sel = slice(start_time, end_time)

    ax1.plot(data.v[sel], '.:', label = 'wind speed')
    ax1.plot((rol_sum[sel]),'.:', label = 'Rolling Average + two std')
#    ax1.plot((rol_sig[sel]),'.:', label = 'Rolling Average + one std')
    ax1.axhline(y=40, color = 'brown')
    ax1.axhline(y=50, color = 'brown')
    ax1.axhspan(40, 50, facecolor = "brown", alpha = 0.2, label = "hysteresis")
    ax1.legend(fontsize = 18)
    ax1.tick_params( axis = 'both', which = "major", labelsize = 18)
    ax1.set_ylabel("Wind Speed (km/h)", fontsize = 18)
    ax1.grid()

    ax2.plot((data[sel].hysteresis), '.:', color = "r", label = " hysterisis decision")
    ax2.plot(((data[sel].shifter_dec)/2), '.:', color = "b" , label = "shifter decision")
    ax2.legend(fontsize = 18)
    ax2.tick_params( axis = 'both', which = "major", labelsize = 18)
    ax2.grid()

#     (fig, axes) = plt.subplots(2, sharex = True)
#     #sel = slice('2018-10-09 20:00', '2018-10-10 00:00')
#     sel = slice(start_time, end_time)
#     plt = axes[0]
#     plt.plot(data.v[sel],'.:', label = 'wind speed')
#     plt.plot((rol_sum[sel]),'.:', label = 'rolling avg max')
#     plt.plot((rol_sig[sel]),'.:', label = 'rolling avg min')
#     #plt.plot((avgreal[sel]),'.:', label = 'rolling avg')
#     plt.axhline(y=40, color = 'brown', label = "hysteresis min")
#     plt.axhline(y=50, color = 'brown', label = "hysteresis max")
#
#     #plt.hist(intervals, range = [0,100], bins = 100)
# #    plt.xlim(0,20)
# #    plt.plot((data[sel].rolling_sum+1)*1000,'.:', label = 'rolling sum')
# #    plt.plot((data[sel].above_threshold+1)*800,'.:', label = 'rainy no counter')
#     #plt.plot((data[sel].rains5+1)*10000,'.:', label = 'rains5 Rolling')
# #    plt.title("Interval Length")
#     plt.grid()
#     plt.legend()
#
#     plt = axes[1]
#     plt.plot((data[sel].hysteresis), '.:', color = "r", label = " with hysterisis")
#
#     plt.title("Rains with Hysteresis and Rainy Rolling Sum")
#     plt.grid()
#     plt.legend()
    f.savefig('Wind_hyst_shifter_Feb_18_zoom.png', dpi = 300, figsize = (120,120))
    plt.show(block=True)





def main(input_data, start_time  , end_time , window_size, hyst_min, hyst_window ):
    '''Run all the functions above to obtain plots
    '''
    data = get_data(input_data)
    column , threshold = get_column( data)

    rol_column, rol_sig , avgreal , shifter = calculate_rolling(data, column, threshold,  window_size)
    data['hysteresis'] = calculate_hyst(rol_column, hyst_min, hyst_window)
    data['rolling_sum'] = rol_column
    data['rol_sig'] = rol_sig
    rol_sum = data['rolling_sum']
    rol_sig = data['rol_sig']



    interval_lengths = intervals(data['hysteresis'])
    result =  get_no_small_intervals(interval_lengths)
    plots(data, rol_sum, rol_sig, avgreal, interval_lengths,  start_time, end_time)
#    print(result)
    return interval_lengths


if __name__ == "__main__":

    arguments = docopt(__doc__, version='autopark 0.1')
    print(arguments)
    main(
        input_data=arguments['<input_data>'],
        #number_of_steps=int(arguments['<number_of_steps>']),
        start_time=arguments['<start_time>'],
        end_time=arguments['<end_time>'],
        window_size=int(arguments['<window_size>']),
        hyst_min=int(arguments['<hyst_min>']),
        hyst_window=int(arguments['<hyst_window>']),
    )
