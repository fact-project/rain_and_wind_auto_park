#!/usr/bin/env python
'''
Program to create dataframe with 'rain' column that is True when rain >0
also creates a dataframe 'changes' that keeps track of how often this column
changes. Plots these columns.


<input_data>   for example "foo.h5"
<number_of_steps>  the number of data points before the rain column updates
<start_time>  specify start of time interval
<end_time>  specify end of time interval

Usage:
  is_rainy.py <input_data> <number_of_steps> <start_time> <end_time>


Options:
  -h --help     Show this screen.
  --version     Show version.
'''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docopt import docopt
from matplotlib import get_backend
from matplotlib import interactive
get_backend()
interactive(True)


def get_data(input_data):
    '''get data and clean it up for operation.
    resample it so that there is one data point per minute.
    '''

    stuff = pd.read_hdf(input_data)
    stuff['good_time'] = pd.to_datetime(stuff.Time, unit='D')
    stuff.set_index('good_time', inplace=True)
    stuff.sort_index(inplace=True)
    del stuff['QoS']
    del stuff['Time']
    resampled = pd.DataFrame()
    resampled['rain'] = stuff.rain.resample('min').mean()
    resampled['count'] = stuff['count'].resample('min').mean()
    return resampled


def add_column(data, number_of_steps=10):
    count_rains = []
    count_drys = []
    count_rainy = 0
    count_dry = 0

    for rain in data['rain']:
        if rain > 0:
            count_rainy += 1
            count_dry = 0
        else:
            count_rainy = 0
            count_dry += 1
        count_rains.append(count_rainy)
        count_drys.append(count_dry)

    data['count_rains'] = count_rains
    data['count_drys'] = count_drys

    data['rains2'] = (
        (data['count_rains'] >= number_of_steps) |
        (data['count_drys'] < number_of_steps)
    )
    data['rains4'] = (
        (data['count_rains'] >= number_of_steps) &
        (data['count_drys'] < number_of_steps)
    )
    data['rainy_no_counter'] = np.where(data['rain'] > 0, True, False)
    data['rainy_rolling_sum'] = data.rainy_no_counter.rolling(40).sum()
    data['rains5'] = data['rainy_rolling_sum'] > 10
    return data


def timing(data):
    timing = pd.DataFrame()
    timing['rain_sum'] = data.rainy_no_counter.resample('40min').sum()
    timing['rain_change'] = timing['rain_sum'] > 10
    return timing


def changes(data, new_interval = 'h'):
    '''
    A new dataframe that keeps a record of the changes in the rain parameter.
    '''
    rain_values = data['rains5'].values
    copied_values = np.zeros_like(rain_values)
    copied_values[0] = rain_values[0]
    copied_values[1:] = rain_values[:-1]
    xor = rain_values ^ copied_values
    data['value_change'] = xor

    changes = pd.DataFrame()
    changes['change_per_hour'] = data.value_change.resample(new_interval).sum()
    return changes


def plots(data, changes, timing, start_time  , end_time   ):
    ''' Plot Data to verify
    '''
    #sel = slice('2018-10-19 00:00', '2018-10-21 00:00')
    sel = slice(start_time, end_time)
    plt.subplot(3,1,1)
    plt.plot(data[sel].rain - 100, '.:', label='rain - 100')
    plt.plot(data[sel].count_rains, '.:', label='count_rains')
    plt.plot(data[sel].count_drys, '.:', label='count_drys')
    plt.plot((data[sel].rains4+1)*600,'.:', label = 'rains4')
    plt.plot((data[sel].rains2+1)*600,'.:', label = 'rains2')
#    plt.plot((data[sel].rainy_no_counter+1)*800,'.:', label = 'rainy no counter')
    plt.plot((data[sel].rains5+1)*800,'.:', label = 'rains5 Rolling')

#    plt.plot((data[sel].rainchange_timing+1)*1000, '.:', label = 'rain change timing')

#

    plt.grid()
    plt.legend()
    plt.title("Rainy Days and Counters")
    plt.subplot(3,1,2)
    plt.plot(changes[sel].change_per_hour,'.:', label='changes per hour')
    #plt.hist(changes[sel].change_per_hour, log=True, bins =np.arange(10)-0.5, facecolor='g')
    ## , histtype='step'
    plt.grid()
    plt.legend()
    plt.title("Number of changes per Hour")

    plt.subplot(3,1,3)
    #plt.plot(timing[sel].rain_change,'.:', label = 'Changes every 10 min')
    #plt.hist(timing[sel].rain_sum, log= True, bins =40)
    plt.hist(data[sel].rainy_rolling_sum, log = True, bins = 40)
    plt.grid()
    plt.show(block=True)


def main(input_data, number_of_steps, start_time  , end_time ):
    '''Run all the functions above to obtain plots
    '''
    initial_data = get_data(input_data)
    final_data = add_column(initial_data, number_of_steps)
    changes_data = changes(final_data)
    timing_data = timing(final_data)
    plots(final_data, changes_data, timing_data, start_time, end_time)


if __name__ == "__main__":

    arguments = docopt(__doc__, version='is_rainy 0.2')
    print(arguments)
    main(
        input_data=arguments['<input_data>'],
        number_of_steps=int(arguments['<number_of_steps>']),
        start_time=arguments['<start_time>'],
        end_time=arguments['<end_time>'],
    )


'''
initial_data = get_data()
final_data = add_column(initial_data)
plot_rainy(final_data)
changes_data = changes(final_data)
plot_changes(changes_data)
'''
