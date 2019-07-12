#!/usr/bin/env python
'''
Program to create dataframe with 'rain' column that is True when rain >.
Various methods are included for comparison. The preferred method uses hysteresis.
also creates a dataframe 'changes' that keeps track of how often this column changes
Plots these columns.


<input_data>   for example "foo.h5"
<start_time>  specify start of time interval
<end_time>  specify end of time interval
<window_size> specify the number of minutes for the rolling sum
<hyst_min>
<hyst_max>

Usage:
  is_rainy.py <input_data> <start_time> <end_time> <window_size> <hyst_min> <hyst_max>


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
    resample it so that there is one data point per minute.
    '''

    stuff = pd.read_hdf(input_data)
    stuff['good_time'] = pd.to_datetime(stuff.Time*24*60*60*1e9)
    stuff.set_index('good_time', inplace=True)
    stuff.sort_index(inplace=True)
    del stuff['QoS']
    del stuff['Time']
    resampled = pd.DataFrame()
    resampled['rain'] = stuff.rain.resample('min').mean()
    resampled['count'] = stuff['count'].resample('min').mean()
    return resampled



#Get data, convert time

def add_column( data,  window_size, number_of_steps = 10):
    '''Add different methods to decide on "true" or "false" for rain
    '''
    rains =[]
    count_rains = []
    count_drys = []
    count_rainy = 0
    count_dry = 0

    for rain in data['rain']:
        if rain >0:
            count_rainy += 1
            count_dry = 0
        else:
            count_rainy = 0
            count_dry += 1
        count_rains.append(count_rainy)
        count_drys.append(count_dry)

    data['count_rains'] = count_rains
    data['count_drys'] = count_drys

    data['rains2'] = (data['count_rains']>= number_of_steps) | (data['count_drys'] < number_of_steps)
    data['rains4'] = (data['count_rains']>= number_of_steps) & (data['count_drys'] < number_of_steps)
    data['rainy_no_counter'] = np.where(data['rain']>0, True, False)
    ### the rolling sum below has 39 "nan" items in the beginning, we get rid of those.
    data['rainy_rolling_sum'] = data.rainy_no_counter.rolling(window_size).sum().fillna(0)
    #data['rainy_rolling_sum'] = data['rainy_rolling_sum'].fillna(0)
    data['rains5'] = np.where(data['rainy_rolling_sum'] >10, True,False)
    #data['rainchange_timing'] = np.where(timing['rain_change']== True, True, False)
    return data


def calculate_hyst(col, hyst_min, hyst_max):
    '''Double windows on y axis using the rolling sum from above
    '''
#    col = data['rainy_rolling_sum']
    hyst = []
    for i in col:
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
    new_column = pd.Series( hyst, index = col.index )
    return new_column



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

'''

def plots(data, changes, hsyt_data, start_time, end_time):

sel = slice(start_time, end_time)

cols_to_plot = [
    'rain',
    'count_rains',
    'count_drys',
    'rainy_rolling_sum',
    'rains5',
    'hysteresis_rain'
]

fig, axes = plt.subplots(
    len(cols_to_plot),
    sharex=True,
    gridspec_kw={'hspace': 0}
)
plt.suptitle("Rainy Days and Counters")

for i, name in enumerate(cols_to_plot):
    ax = axes[i]
    ax.plot(data[sel][name], '.:', color="C{}".format(i), label=name)
    ax.grid()
    ax.legend(loc='upper left')

fig, axes = plt.subplots(2)

ax = axes[0]
ax.plot(changes[sel].change_per_hour, '.:', label='changes per hour')
ax.grid()
ax.legend(loc='upper left')
ax.set_title("Number of changes per Hour")

ax = axes[1]
ax.hist(
    data[sel].rainy_rolling_sum,
    log=True,
    bins=np.arange(
        data[sel].rainy_rolling_sum.max() + 1
    ) - 0.5
)
ax.grid()
ax.legend(loc='upper left')
ax.set_title("Number of changes per Hour")

plt.grid()

plt.show(block=True)
'''


def plots(data, changes, start_time  , end_time   ):


    #sel = slice('2018-10-19 00:00', '2018-10-21 00:00')
    sel = slice(start_time, end_time)
    plt.subplot(2,1,1)
    #plt.plot(data[sel].rain - 1000, '.:', label='rain - 100')
    #plt.plot(data[sel].count_rains, '.:', label='count_rains')
    #plt.plot(data[sel].count_drys, '.:', label='count_drys')
    #plt.plot((data[sel].rains4+1)*10000,'.:', label = 'rains4')
    #plt.plot((data[sel].rains2+1)*5000,'.:', label = 'rains2')
    plt.plot((data[sel].rainy_rolling_sum+1)*1000,'.:', label = 'rolling sum')
#    plt.plot((data[sel].rainy_no_counter+1)*800,'.:', label = 'rainy no counter')
    plt.plot((data[sel].rains5+1)*10000,'.:', label = 'rains5 Rolling')
    plt.title("Rains5 and Rainy rolling sum")
    plt.grid()
    plt.legend()

    plt.subplot(2,1,2)
    plt.plot((data[sel].rainy_rolling_sum+1)*1000,'.:', label = 'rolling sum')
    plt.plot((data[sel].hysteresis_rain+1)*10000, '.:', color = "r", label = "rains with hysterisis")
    plt.title("Rains with Hysteresis and Rainy Rolling Sum")
    plt.grid()
    plt.legend()
    plt.show(block=True)




def main(input_data, start_time  , end_time , window_size, hyst_min, hyst_max ):
    '''Run all the functions above to obtain plots
    '''
    initial_data = get_data(input_data)
    final_data = add_column(initial_data, window_size)
    # Below, hyst takes in the rolling sum and
    final_data['hysteresis_rain'] = calculate_hyst(final_data['rainy_rolling_sum'], hyst_min, hyst_max)
    changes_data = changes(final_data)

    plots(final_data, changes_data,  start_time, end_time)




if __name__ == "__main__":

    arguments = docopt(__doc__, version='is_rainy 0.2')
    print(arguments)
    main(
        input_data=arguments['<input_data>'],
        #number_of_steps=int(arguments['<number_of_steps>']),
        start_time=arguments['<start_time>'],
        end_time=arguments['<end_time>'],
        window_size=int(arguments['<window_size>']),
        hyst_min=int(arguments['<hyst_min>']),
        hyst_max=int(arguments['<hyst_max>']),
    )

### Execute as
