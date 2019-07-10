#!/usr/bin/env python
'''
Program to decide whether FACT should autopark based on weather conditions.
Methods compared: Rolling sum, rolling average + 2std, mock shifter. 
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
from datetime import timedelta
get_backend()
interactive(True)

def get_data(input_data, start_time, end_time ):
    '''get data and clean it up for operation.
    If it is rain data, resample it so that there is one data point per minute.
    If it is wind data, delete an additional column
    '''


    ## Actual times when data was taken
    actual = pd.read_hdf("actual_schedule.h5")
    actual.set_index('fStart', inplace = True)
    actual.sort_index(inplace=True)
    actual = actual[start_time: end_time]

    ## Planned schedule for data taking
    planned = pd.read_hdf("planned_schedule.h5")
    planned.set_index('fStart', inplace = True)
    planned.sort_index( inplace = True)
    planned = planned[start_time: end_time]

    ##iNPUT IS ===> all_rain_data.h5 or all_wind_data.h5
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
        resampled = pd.DataFrame()
        resampled['v'] = stuff.v.resample('min').mean()
        resampled['v_max'] = stuff.v_max.resample('min').mean()
        stuff = resampled

    ## Join the planned schedule to the data
    stuff = stuff.join(planned, how='outer')
    take_data = []
    column = stuff['fMeasurementTypeName']
    previous = True
    for element in column:
        if element == 'Startup':
            take_data.append(True)
        elif element == 'Shutdown':
            take_data.append(False)
        else:
            take_data.append(previous)
        previous = take_data[-1]

    stuff['take_data'] = take_data


### Add actual schedule
    actual.rename(columns = {'fMeasurementTypeName':'ActualMeasurement'}, inplace= True)
    del actual['fUser']
    del actual['fSourceName']
    stuff = stuff.join(actual, how='outer')
    actual_sch = []
    column = stuff['ActualMeasurement']
    previous = True
    for element in column:
        if element in ('Startup','Resume'):
            actual_sch.append(False)
        elif element in ('Shutdown','Sleep','Suspend'):
            actual_sch.append(True)
        else:
            actual_sch.append(previous)
        previous = actual_sch[-1]

    stuff['turned_off'] = actual_sch

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
        #col_rolling =
        data['rolling_sum'] = data.above_threshold.rolling(window_size).sum().fillna(0)
        col_sigma = 0
    else:

        ### THEN IT IS WIND DATA!!!!!! #############################################################################################
        ## THE FAKE SHIFTER PERSON!!!
        shifter = data['shifter_dec'] = False
                                # W = data[~((data.index.hour > 7) & (data.index.hour < 17))]
                                # W.index = W.index + timedelta(hours=12)
                                # W.index = W.index - timedelta(hours=12)
                                # data = W
        #January
        data.shifter_dec["2018-01-01 17:00":"2018-01-02 08:00"] = True
        data.shifter_dec["2018-01-02 17:00":"2018-01-03 08:00"] = True
        data.shifter_dec["2018-01-03 18:50":"2018-01-04 08:00"] = True
        data.shifter_dec["2018-01-06 03:00":"2018-01-06 06:00"] = True
        data.shifter_dec["2018-01-06 17:00":"2018-01-07 08:00"] = True
        data.shifter_dec["2018-01-08 00:00":"2018-01-08 08:00"] = True
        data.shifter_dec["2018-01-15 17:00":"2018-01-16 08:00"] = True
        data.shifter_dec["2018-01-16 17:00":"2018-01-17 08:00"] = True
        data.shifter_dec["2018-01-17 17:00":"2018-01-18 08:00"] = True
        data.shifter_dec["2018-01-19 20:00":"2018-01-20 08:00"] = True
        data.shifter_dec["2018-01-22 01:30":"2018-01-22 08:00"] = True
        data.shifter_dec["2018-01-23 22:10":"2018-01-23 23:50"] = True
        data.shifter_dec["2018-01-27 05:25":"2018-01-27 08:00"] = True
        data.shifter_dec["2018-01-27 17:30":"2018-01-28 08:00"] = True
        data.shifter_dec["2018-01-28 17:00":"2018-01-29 08:00"] = True
        data.shifter_dec["2018-01-31 18:20":"2018-02-01 08:00"] = True
        #February
        data.shifter_dec["2018-02-01 18:30":"2018-02-02 08:00"] = True
        data.shifter_dec["2018-02-03 01:45":"2018-02-03 08:00"] = True
        data.shifter_dec["2018-02-03 17:00":"2018-02-03 23:00"] = True
        data.shifter_dec["2018-02-05 07:15":"2018-02-05 08:00"] = True
        data.shifter_dec["2018-02-10 22:15":"2018-02-10 23:30"] = True
        data.shifter_dec["2018-02-24 23:57":"2018-02-25 08:00"] = True
        data.shifter_dec["2018-02-25 20:10":"2018-02-25 21:20"] = True
        data.shifter_dec["2018-02-26 17:00":"2018-02-27 08:00"] = True
        data.shifter_dec["2018-02-27 17:00":"2018-02-28 08:00"] = True
        data.shifter_dec["2018-02-28 17:00":"2018-03-01 08:00"] = True
        #March
        data.shifter_dec["2018-03-01 23:00":"2018-03-01 08:00"] = True
        data.shifter_dec["2018-03-02 18:30":"2018-03-02 19:30"] = True
        data.shifter_dec["2018-03-03 01:30":"2018-03-01 03:30"] = True
        data.shifter_dec["2018-03-03 07:35":"2018-03-03 08:00"] = True
        data.shifter_dec["2018-03-03 17:00":"2018-03-04 06:00"] = True
        data.shifter_dec["2018-03-09 01:10":"2018-03-09 08:00"] = True
        data.shifter_dec["2018-03-09 17:00":"2018-03-10 01:00"] = True
        data.shifter_dec["2018-03-20 19:25":"2018-03-21 01:40"] = True
        data.shifter_dec["2018-03-24 20:40":"2018-03-24 21:40"] = True
        data.shifter_dec["2018-03-25 20:45":"2018-03-25 22:45"] = True
        #April
        data.shifter_dec["2018-04-08 07:45":"2018-04-08 08:00"] = True
        data.shifter_dec["2018-04-08 18:55":"2018-04-09 05:30"] = True
        data.shifter_dec["2018-04-19 20:47":"2018-04-19 23:50"] = True
        data.shifter_dec["2018-04-20 01:45":"2018-04-20 02:50"] = True
        data.shifter_dec["2018-04-23 22:35":"2018-04-24 01:30"] = True
        #May
        #June
        data.shifter_dec["2018-06-16 22:20":"2018-06-17 01:30"] = True
        #July
        #August
        data.shifter_dec["2018-08-05 22:35":"2018-08-06 00:20"] = True
        data.shifter_dec["2018-08-06 01:15":"2018-08-06 04:10"] = True
        data.shifter_dec["2018-08-06 23:05":"2018-08-07 04:15"] = True
        #September
        data.shifter_dec["2018-09-27 19:47":"2018-09-27 21:10"] = True
        data.shifter_dec["2018-09-27 21:55":"2018-09-28 00:00"] = True
        #October
        data.shifter_dec["2018-10-07 17:00":"2018-10-08 08:00"] = True
        data.shifter_dec["2018-10-09 04:27":"2018-10-09 06:30"] = True
        data.shifter_dec["2018-10-24 19:15":"2018-10-24 20:30"] = True
        #November
        data.shifter_dec["2018-11-02 20:30":"2018-11-03 00:00"] = True
        data.shifter_dec["2018-11-02 20:30":"2018-11-03 00:00"] = True
        data.shifter_dec["2018-11-03 00:35":"2018-11-03 08:00"] = True
        #December
        data.shifter_dec["2018-12-06 04:00":"2018-12-06 06:30"] = True
        data.shifter_dec["2018-12-07 23:10":"2018-12-08 00:15"] = True
        data.shifter_dec["2018-11-02 20:30":"2018-11-03 00:00"] = True
        data.shifter_dec["2018-12-24 17:00":"2018-12-25 08:00"] = True
        #January
        #February
        data.shifter_dec["2019-02-13 18:25":"2019-02-13 20:15"] = True
        data.shifter_dec["2019-02-13 21:30":"2019-02-13 23:15"] = True
        data.shifter_dec["2019-02-14 00:40":"2019-02-14 08:00"] = True
        data.shifter_dec["2019-02-21 18:25":"2019-02-22 08:00"] = True
        data.shifter_dec["2019-02-22 17:10":"2019-02-22 18:30"] = True
        #March
        data.shifter_dec["2019-03-08 20:47":"2019-03-08 21:50"] = True
        data.shifter_dec["2019-03-09 00:30":"2019-03-09 06:30"] = True
        data.shifter_dec["2019-03-09 17:25":"2019-03-10 08:00"] = True


###### NEW METHOD: Rolling sum for when v_max > 50 .
## Similar to the case for rain!

    #    data['v_max'] = np.where(data.v_max == 0 , np.nan, None)
        data['foo'] = (data.v_max > 50).rolling('1h').sum()
        data['bar'] =calculate_hyst(data['foo'], 0, 2)
    #    data = data[(data.v_max - data.v_max.rolling(window_size).mean()) >= (-1*data.v_max.rolling(window_size).std()) ]

        data['rolling_avg'] = data.v.rolling(min_periods = 1, center = False, window = window_size).mean()
        #.fillna(0)
        #col_sigma2 =
        data['rolling_sig'] = data.v.rolling(min_periods = 1, center = False, window = window_size).std()
        #.fillna(0)
        data['rolling_avg_gust'] = data.v_max.rolling(min_periods = 1, center = False, window = window_size).mean()
        #.fillna(0)
        data['rolling_sig_gust'] = data.v_max.rolling(min_periods = 1, center = False, window = window_size).std()
        #.fillna(0)

        data['rolling2'] = data.rolling_avg + (data.rolling_sig)*2
        data['rolling2_gust'] = data.rolling_avg_gust + (data.rolling_sig_gust)*2
#        data['rolling_max'] = data.v_max.rolling(min_periods = 1, center = False, window = window_size).max()

        #
        # W = data[~((data.index.hour > 7) & (data.index.hour < 17))]
        #
        # W.index = W.index + timedelta(hours=12)
        # W.index = W.index - timedelta(hours=12)
        # data = W
#These are actually the max and min of the rolling mean band
        #col_rolling = col_rolling2 +(col_sigma2 *2 )
        #col_sigma = col_rolling2 +(col_sigma2)



    return data



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
            # this only happens if i is not a number: np.nan
            hyst.append(3)
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





def plots(data,  intervals, start_time  , end_time   ):


    f, (ax1, ax2, ax3) = plt.subplots(nrows =3,sharex = True, figsize = (30,15),gridspec_kw={'height_ratios': [1,3, 2]} )
#    f, (a0, a1) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})
    sel = slice(start_time, end_time)
    data1 = data[data['take_data'] == True]

        # W = data[~((data.index.hour > 7) & (data.index.hour < 17))]
        #
        # W.index = W.index + timedelta(hours=12)
        # W.index = W.index - timedelta(hours=12)
        # data = W
    if 'rain' in data:
        ax1.plot((data1.rolling_sum[sel]), '.', label = 'Events Above Threshold', color = "C2")
        ax1.axhspan(10, 20, facecolor = "C2", alpha = 0.2)
    else:
        ax1.plot((data1.foo[sel]), '.', label = 'Events Above Threshold', color = "C2")
    #ax1.axhline(y=0, color = "C2")
    #ax1.axhline(y=2, color = "C2")
        ax1.axhspan(0, 2, facecolor = "C2", alpha = 0.2)

        ax1.set_yticklabels(["0","2"], fontsize = 18)
    ax1.grid()
    ax1.legend(fontsize = 18)

    if 'rain' in data:
        ax2.plot(data1[sel].rain, '.',color = "C0",  label = 'Rain')
        ax2.set_ylabel("Raininess (??)", fontsize = 18)
    else:
        ax2.plot(data1[sel].v_max, '.',color = "C0",  label = 'Wind Gust')

    #ax1.plot(data.rolling_max[sel], '.:', label = "Gust Rolling Max")
    #ax1.plot(data.v[sel], '.:', label = 'wind speed')
        ax2.plot((data1.rolling2_gust[sel]), '.', color = "C1", label = 'Gust Rolling Average + 2 $\sigma$ ')
        ax2.set_ylabel("Wind Speed (km/h)", fontsize = 18)

    #ax1.plot((data.rolling2[sel]),'.:', label = 'Rolling Average + two std')

#    ax1.plot((rol_sig[sel]),'.:', label = 'Rolling Average + one std')
    #ax2.axhline(y=40, color = "xkcd:orange")
    #ax2.axhline(y=50, color = "xkcd:orange")
        ax2.axhspan(40, 50, facecolor = "C1", alpha = 0.2)
    ax2.legend(fontsize = 18)
    ax2.tick_params( axis = 'both', which = "major", labelsize = 18)

    ax2.grid()


#    ax2.plot(data[sel].v_max, '.:', color = "r", label = 'wind gust')
#    ax2.plot(data[sel].v, '.:', color = "g", label = 'wind speed')

    if 'rain' in data:
        ax3.plot((data1[sel].hysteresis), '.:', color = "C1", label = " Average Method Decision")
    else:
        ax3.plot((data1[sel].hysteresis_gust), '.:', color = "C1", label = " Average Method Decision")

        ax3.plot(((data1[sel].shifter_dec)+2), '.:', color = "C0" , label = "Mock Shifter Decision")
        ax3.plot(((data1[sel].bar)+4), '.:', color = "C2" , label = "Sum Method Decision")
        ax3.plot(((data1[sel].turned_off)+6), '.:', color ="C4", label = "Actual Schedule")
    ax3.legend(fontsize = 18, loc = "upper right")
    ax3.tick_params( axis = 'both', which = "major", labelsize = 18)
    ax3.set_yticklabels([])
    ax3.grid()


    # ax3.plot(data[sel].v_max - data[sel].v_max.rolling(30).mean(), '.:', color = "b" , label = "difference")
    # ax3.plot((data[sel].v_max.rolling(30).std()), '.:', color = "r" , label = "-3 std")
    # ax3.legend()


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
    f.savefig('Wind_gust_Jan_comparison_part2.png', dpi = 300, figsize = (120,120))
    plt.show(block=True)





def main(input_data, start_time  , end_time , window_size, hyst_min, hyst_window ):
    '''Run all the functions above to obtain plots
    '''
    data = get_data(input_data, start_time, end_time)
    column , threshold = get_column( data)
#rol_column, rol_sig , avgreal , shifter,

    data = calculate_rolling(data, column, threshold,  window_size)
    if 'rain' in data:
        data['hysteresis'] = calculate_hyst(data.rolling_sum, hyst_min, hyst_window)
    else:
        data['hysteresis'] = calculate_hyst(data.rolling2, hyst_min, hyst_window)
        data['hysteresis_gust'] = calculate_hyst(data.rolling2_gust, hyst_min, hyst_window)
    # data['rolling_sum'] = rol_column
    # data['rol_sig'] = rol_sig
    # rol_sum = data['rolling_sum']
    # rol_sig = data['rol_sig']
    interval_lengths = intervals(data['hysteresis'])
    result =  get_no_small_intervals(interval_lengths)
    plots(data, interval_lengths,  start_time, end_time)
    print(result)
    return result


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
