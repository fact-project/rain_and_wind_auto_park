#!/usr/bin/env python
'''
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
    Get actual and planned schedule data as well.
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

    ##iNPUT IS ===> updated_rain_data.h5 or all_wind_data.h5
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


def determine_data_type( data):
    ''' Distinguish between rain data and wind data.
    Set the right threshold, hysteresis minimum and window.
    '''
    if 'rain' in data:
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
    #hyst_min, hyst_window, name


def make_decision( data, col, threshold,  window_size, hyst_min, hyst_window):
    '''Use a rolling sum above threshold to make a decision to park.
    '''
    data['rolling_sum'] = (col > threshold).rolling(window_size).sum()
    data['park'] =calculate_hyst(data['rolling_sum'], hyst_min,  hyst_window)
    return data


def wind_methods(data, threshold, window_size):
    '''Examine an alternative method for wind. Also include a mock shifter's decisions.
    '''



    data['quantile'] = data.v_max.rolling('1h').quantile(0.95)
    data['quantile_park'] = calculate_hyst(data['quantile'], 40, 10)

    data['quantile2'] = data.v_max.rolling('1h').quantile(0.90)
    data['quantile_park2'] = calculate_hyst(data['quantile2'], 40, 10)

    data['quantile3'] = data.v_max.rolling('30min').quantile(0.70)
    data['quantile_park3'] = calculate_hyst(data['quantile3'], 40, 10)



        ## Alternative method for wind:
        # Find rolling mean, and rolling std.
#    data = data[(data.v_max - data.v_max.rolling(window_size).mean()) >= (-1*data.v_max.rolling(window_size).std()) ]
    data['rolling_avg_gust'] = data.v_max.rolling(window_size).mean()
    data['rolling_sig_gust'] = data.v_max.rolling(window_size).std()
        # Look at Rolling mean + 2 std to make decision!
    data['rolling_gust'] = data.rolling_avg_gust + (data.rolling_sig_gust)*2
        # Add hysteresis. Interval is from 40 to 50 km/h.
    data['park_avg_plus_std'] = calculate_hyst(data['rolling_gust'], 40 , 10)

        ## THE FAKE SHIFTER PERSON###############################################################
    # shifter = data['shifter_dec'] = False
    #     #January
    # data.shifter_dec.loc["2018-01-01 17:00":"2018-01-02 08:00"] = True
    # data.shifter_dec.loc["2018-01-02 17:00":"2018-01-03 08:00"] = True
    # data.shifter_dec.loc["2018-01-03 18:50":"2018-01-04 08:00"] = True
    # data.shifter_dec.loc["2018-01-06 03:00":"2018-01-06 06:00"] = True
    # data.shifter_dec.loc["2018-01-06 17:00":"2018-01-07 08:00"] = True
    # data.shifter_dec.loc["2018-01-08 00:00":"2018-01-08 08:00"] = True
    # data.shifter_dec.loc["2018-01-15 17:00":"2018-01-16 08:00"] = True
    # data.shifter_dec.loc["2018-01-16 17:00":"2018-01-17 08:00"] = True
    # data.shifter_dec.loc["2018-01-17 17:00":"2018-01-18 08:00"] = True
    # data.shifter_dec.loc["2018-01-19 20:00":"2018-01-20 08:00"] = True
    # data.shifter_dec.loc["2018-01-22 01:30":"2018-01-22 08:00"] = True
    # data.shifter_dec.loc["2018-01-23 22:10":"2018-01-23 23:50"] = True
    # data.shifter_dec.loc["2018-01-27 05:25":"2018-01-27 08:00"] = True
    # data.shifter_dec.loc["2018-01-27 17:30":"2018-01-28 08:00"] = True
    # data.shifter_dec.loc["2018-01-28 17:00":"2018-01-29 08:00"] = True
    # data.shifter_dec.loc["2018-01-31 18:20":"2018-02-01 08:00"] = True
    # #February
    # data.shifter_dec.loc["2018-02-01 18:30":"2018-02-02 08:00"] = True
    # data.shifter_dec.loc["2018-02-03 01:45":"2018-02-03 08:00"] = True
    # data.shifter_dec.loc["2018-02-03 17:00":"2018-02-03 23:00"] = True
    # data.shifter_dec.loc["2018-02-05 07:15":"2018-02-05 08:00"] = True
    # data.shifter_dec.loc["2018-02-10 22:15":"2018-02-10 23:30"] = True
    # data.shifter_dec.loc["2018-02-24 23:57":"2018-02-25 08:00"] = True
    # data.shifter_dec.loc["2018-02-25 20:10":"2018-02-25 21:20"] = True
    # data.shifter_dec.loc["2018-02-26 17:00":"2018-02-27 08:00"] = True
    # data.shifter_dec.loc["2018-02-27 17:00":"2018-02-28 08:00"] = True
    # data.shifter_dec.loc["2018-02-28 17:00":"2018-03-01 08:00"] = True
    # #March
    # data.shifter_dec.loc["2018-03-01 23:00":"2018-03-01 08:00"] = True
    # data.shifter_dec.loc["2018-03-02 18:30":"2018-03-02 19:30"] = True
    # data.shifter_dec.loc["2018-03-03 01:30":"2018-03-01 03:30"] = True
    # data.shifter_dec.loc["2018-03-03 07:35":"2018-03-03 08:00"] = True
    # data.shifter_dec.loc["2018-03-03 17:00":"2018-03-04 06:00"] = True
    # data.shifter_dec.loc["2018-03-09 01:10":"2018-03-09 08:00"] = True
    # data.shifter_dec.loc["2018-03-09 17:00":"2018-03-10 01:00"] = True
    # data.shifter_dec.loc["2018-03-20 19:25":"2018-03-21 01:40"] = True
    # data.shifter_dec.loc["2018-03-24 20:40":"2018-03-24 21:40"] = True
    # data.shifter_dec.loc["2018-03-25 20:45":"2018-03-25 22:45"] = True
    # #April
    # data.shifter_dec.loc["2018-04-08 07:45":"2018-04-08 08:00"] = True
    # data.shifter_dec.loc["2018-04-08 18:55":"2018-04-09 05:30"] = True
    # data.shifter_dec.loc["2018-04-19 20:47":"2018-04-19 23:50"] = True
    # data.shifter_dec.loc["2018-04-20 01:45":"2018-04-20 02:50"] = True
    # data.shifter_dec.loc["2018-04-23 22:35":"2018-04-24 01:30"] = True
    # #May
    # #June
    # data.shifter_dec.loc["2018-06-16 22:20":"2018-06-17 01:30"] = True
    # #July
    # #August
    # data.shifter_dec.loc["2018-08-05 22:35":"2018-08-06 00:20"] = True
    # data.shifter_dec.loc["2018-08-06 01:15":"2018-08-06 04:10"] = True
    # data.shifter_dec.loc["2018-08-06 23:05":"2018-08-07 04:15"] = True
    # #September
    # data.shifter_dec.loc["2018-09-27 19:47":"2018-09-27 21:10"] = True
    # data.shifter_dec.loc["2018-09-27 21:55":"2018-09-28 00:00"] = True
    # #October
    # data.shifter_dec.loc["2018-10-07 17:00":"2018-10-08 08:00"] = True
    # data.shifter_dec.loc["2018-10-09 04:27":"2018-10-09 06:30"] = True
    # data.shifter_dec.loc["2018-10-24 19:15":"2018-10-24 20:30"] = True
    # #November
    # data.shifter_dec.loc["2018-11-02 20:30":"2018-11-03 00:00"] = True
    # data.shifter_dec.loc["2018-11-02 20:30":"2018-11-03 00:00"] = True
    # data.shifter_dec.loc["2018-11-03 00:35":"2018-11-03 08:00"] = True
    # #December
    # data.shifter_dec.loc["2018-12-06 04:00":"2018-12-06 06:30"] = True
    # data.shifter_dec.loc["2018-12-07 23:10":"2018-12-08 00:15"] = True
    # data.shifter_dec.loc["2018-11-02 20:30":"2018-11-03 00:00"] = True
    # data.shifter_dec.loc["2018-12-24 17:00":"2018-12-25 08:00"] = True
    # #January
    # #February
    # data.shifter_dec.loc["2019-02-13 18:25":"2019-02-13 20:15"] = True
    # data.shifter_dec.loc["2019-02-13 21:30":"2019-02-13 23:15"] = True
    # data.shifter_dec.loc["2019-02-14 00:40":"2019-02-14 08:00"] = True
    # data.shifter_dec.loc["2019-02-21 18:25":"2019-02-22 08:00"] = True
    # data.shifter_dec.loc["2019-02-22 17:10":"2019-02-22 18:30"] = True
    # #March
    # data.shifter_dec.loc["2019-03-08 20:47":"2019-03-08 21:50"] = True
    # data.shifter_dec.loc["2019-03-09 00:30":"2019-03-09 06:30"] = True
    # data.shifter_dec.loc["2019-03-09 17:25":"2019-03-10 08:00"] = True
    #############################################################################################

    return data


def calculate_hyst(rolling, hyst_min, hyst_window):
    '''Prevent decisions from happening "too quickly"
    '''
    hyst = []
    hyst_max = hyst_min + hyst_window
    previous = True
    for i in rolling:
        if i <= hyst_min:
            hyst.append(False)
        elif i >= hyst_max:
            hyst.append(True)
        elif (i >= hyst_min) & (i <= hyst_max):
            hyst.append(previous)
        else:
            # this only happens if i is not a number: np.nan
            hyst.append(previous)
        previous = hyst[-1]

    new_column = pd.Series( hyst, index = rolling.index )
    return new_column


def intervals(data_column):
    ''' Determine the length of intervals between decisions
    '''
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
    '''Determine the length and number of intervals that are less than 10 and 20 minutes
    '''
    small_intervals = []
    medium_intervals = []
    for i in np.array(intv_list):
        if i <= 10:
            small_intervals.append(i)
        if 10 <= i <= 20:
            medium_intervals.append(i)
    return len(small_intervals)

def plots(data, col, start_time, end_time, hyst_min, hyst_window, name, outfile_name):

    f, (ax1, ax2) = plt.subplots(nrows =2,sharex = True, figsize = (30,15),gridspec_kw={'height_ratios': [3, 2]} )
    sel = slice(start_time, end_time)



    ax1.plot(col[sel], '.',color = "C0",  label = name, alpha = 0.5)
    #ax2.set_ylabel("Raininess (??)", fontsize = 18)
### Wind Specific######################################
    #try:
    #ax1.plot((data.rolling_gust[sel]), '.', color = "C1", label = ' Rolling Average + 2 $\sigma$ ')
    ax1.plot((data['quantile'][sel]), '.:', color = "C5" , label = 'Rolling 95% Quantile ')
    ax1.plot((data['quantile2'][sel]), '.:', color = "C6" , label = 'Rolling 90% Quantile')
    ax1.plot((data['quantile3'][sel]), '.:', color = "C2" , label = 'Rolling 70% Quantile, 30 min ')
    ax1.axhspan(40, 50, facecolor = "C1", alpha = 0.2)
        #ax2.plot((data.quantile[sel]), '.', color = "C5", label = '.95 Quantile')
        #ax2.plot((data.quantile2[sel]), '.', color = "C6", label = '.90 Quantile')


    ax1.set_ylabel("Wind Speed (km/h)", fontsize = 18)

    #except:
    #    pass
###########################################################
    ax1.legend(fontsize = 18, loc = "upper right")
    ax1.tick_params( axis = 'both', which = "major", labelsize = 18)
    ax1.grid()



    #ax2.plot(((data[sel].park_avg_plus_std)+8), '.:', color = "C2", label = "  Rolling Sum Decision")
    ax2.plot(((data[sel].turned_off)+6), '.:', color ="C4", label = "Actual Schedule")

### Wind Specific##################################################################################
    try:
        ax2.plot(((data[sel].quantile_park3)+4), '.:', color = "C2" , label = "70% Quantile Decision")
        ax2.plot(((data[sel].quantile_park)+2), '.:', color = "C5" , label = "95% Quantile Decision")
        ax2.plot(((data[sel].quantile_park2)+0), '.:', color = "C6" , label = "90% Quantile Decision")


    except:
        pass
###################################################################################################
    ax2.legend(fontsize = 18, loc = "upper right")
    ax2.tick_params( axis = 'both', which = "major", labelsize = 18)
    ax2.set_yticklabels([])
    ax2.grid()



#    f.savefig('Wind_gust_Jan_comparison_part2.png', dpi = 300, figsize = (120,120))
    # plt.show(block=True)


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
#     ax3.plot(((data[sel].turned_off)+6), '.:', color ="C4", label = "Actual Schedule")
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
    f.savefig(outfile_name, dpi = 300, figsize = (120,120))
#     plt.show(block=True)





def main(input_data, start_time  , end_time , window_size , hyst_min, hyst_window, outfile_name):
    '''Run all the functions above to obtain plots
    '''
    data = get_data(input_data, start_time, end_time)
    type, threshold,   name = determine_data_type(data)
    #hyst_min, hyst_window,
    if type == "rain":
        col = data.rain
    else:
        col = data.v_max
        data = wind_methods(data, threshold, window_size)

    data = make_decision(data, col, threshold, window_size, hyst_min, hyst_window)
#    print(hyst_min + hyst_window)
    data1 = data[data['take_data'] == True]
    plots(data1, col, start_time, end_time, hyst_min, hyst_window, name, outfile_name)

    interval_lengths = intervals(data1['park'])
    result = get_no_small_intervals(interval_lengths)
    total_hours = (len(data.take_data))/60
    actual_data_taken = data[data['turned_off'] == False]
    actual_hours = len(actual_data_taken)
    print("total_hours:", total_hours)
    return result


if __name__ == "__main__":

    arguments = docopt(__doc__, version='autopark 0.3')
    print(arguments)
    main(
        input_data=arguments['<input_data>'],
        #number_of_steps=int(arguments['<number_of_steps>']),
        start_time=arguments['<start_time>'],
        end_time=arguments['<end_time>'],
        window_size=int(arguments['<window_size>']),
        hyst_min=int(arguments['<hyst_min>']),
        hyst_window=int(arguments['<hyst_window>']),
        outfile_name=arguments['<outfile_name>']
    )
