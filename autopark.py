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

    stuff = pd.read_hdf(input_data)
    stuff['good_time'] = pd.to_datetime(stuff.Time*24*60*60*1e9)
    stuff.set_index('good_time', inplace=True)
    stuff.sort_index(inplace=True)
    del stuff['QoS']
    del stuff['Time']
    if stuff.rain is None:
        del stuff['stat']
    else:
        resampled = pd.DataFrame()
        resampled['rain'] = stuff.rain.resample('min').mean()
        resampled['count'] = stuff['count'].resample('min').mean()
        stuff = resampled
    return stuff


def get_column( data):
    ''' Get the column 'rain' for the rain data, and 'v' for wind data.
    Set the right threshold.
    '''
    if data.rain is None:
        col = data['v']
        threshold = 50
    else:
        col = data['rain']
        threshold = 0

    return col, threshold


def calculate_rolling_sum( data, col, threshold,  window_size):
    '''Calculate the rolling sum
    '''
    data['above_threshold'] = np.where(col > threshold, True, False)
    ### the rolling sum below has 39 "nan" items in the beginning, we get rid of those.
    col_rolling = data['rolling_sum'] = data.above_threshold.rolling(window_size).sum().fillna(0)


    return col_rolling



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





def plots(data, intervals, start_time  , end_time , hyst_min, hyst_window  ):


    #sel = slice('2018-10-09 20:00', '2018-10-10 00:00')
    sel = slice(start_time, end_time)
    plt.subplot(2,1,1)
    plt.hist(intervals, range = [0,100], bins = 100)
#    plt.xlim(0,20)
#    plt.plot((data[sel].rolling_sum+1)*1000,'.:', label = 'rolling sum')
#    plt.plot((data[sel].above_threshold+1)*800,'.:', label = 'rainy no counter')
    #plt.plot((data[sel].rains5+1)*10000,'.:', label = 'rains5 Rolling')
    plt.title("Interval Length")
    plt.grid()
    plt.legend()

    plt.subplot(2,1,2)
    plt.plot((data[sel].rolling_sum),'.:', label = 'rolling sum')
    plt.plot((data[sel].hysteresis)*20, '.:', color = "r", label = " with hysterisis")
#    plt.plot(10,'-', color = "g", label = "lower threshold")
#    plt.plot(15, '-', color = "y", label = "upper threshold")
    plt.title("Rains with Hysteresis and Rainy Rolling Sum")
    plt.grid()
    plt.legend()
    plt.show(block=True)




def main(input_data, start_time  , end_time , window_size, hyst_min, hyst_window ):
    '''Run all the functions above to obtain plots
    '''
    data = get_data(input_data)
    column , threshold = get_column( data)

    rol_column = calculate_rolling_sum(data, column, threshold,  window_size)
    # Below, hyst takes in the rolling sum and
    data['hysteresis'] = calculate_hyst(rol_column, hyst_min, hyst_window)
    data['rolling_sum'] = rol_column
    interval_lengths = intervals(data['hysteresis'])
    result =  get_no_small_intervals(interval_lengths)
    plots(data, interval_lengths,  start_time, end_time, hyst_min, hyst_window)
#    print(result)
    return interval_lengths
    #("with threshold", threshold, "and window size", window_size, ", the number of small intervals:" ,result)



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
