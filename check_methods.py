
'''
Program to check which method is right.

'''
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import is_rainy as rn


def get_interval_length(data):
    '''get interval length in time
    '''
    col = data['hysteresis_rain']
    list_of_intervals = []
    true = 0
    trues = []
    false = 0
    falses = []
    time_of_edges = []
    for i in range(len(col)-1):
        y0 = col.iloc[i]
        y1 = col.iloc[i+1]
        if y0 != y1:
            time_of_edges.append(col.index[i])

            #This will only have one column, with name "0".
    #pd.DataFrame(time_of_edges)
    #turn into series so that you have no bs __name_
    #take difference of each value
    #get rid of first value, doesn't make sense
    interval_widths = pd.Series(time_of_edges).diff()[1:]
    #But this is datatime, not so good for histograms! Can;t histogram timestamps!!!
    interval_widths_inmin = interval_widths.values.astype('f')/1e9/60
    #1e9 is because iti s in nanosecs , 60 is for minutes!!
    return interval_widths_inmin






def intervals(data):
    list_of_intervals = []
    true = 0
    trues = []
    false = 0
    falses = []
    for rain in data['rains5']:
        if rain == False:
            false += 1
            if true != 0:
                list_of_intervals.append(true)
            true = 0
        else:
            true += 1
            if false != 0:
                list_of_intervals.append(false)
            false = 0
        falses.append(false)
        trues.append(true)
    return list_of_intervals, falses, trues

def get_no_small_intervals(intv_list):
    small_intervals = []
    for i in np.array(intv_list):
        if i < 10:
            small_intervals.append(i)
    return print("The number of intervals with length smaller than 10 units is",len(small_intervals))




def plot(intervals ):
    plt.subplot(2,1,1)
    plt.grid()
    plt.legend()
    plt.hist(intervals, bins = np.linspace(0,60,20))

    plt.grid()
    plt.show(block=True)



data1 = rn.get_data("updated_rain_data.h5" )
## I'm adding crazy columns
data1= rn.add_column( data1,  10)
data1 = rn.hyst(data1)
### Time to see how well these columns work!
#This shows number of changes per hour
change_data = rn.changes(data1, new_interval = 'h')
#With time
interv_list = get_interval_length(data1)
#List of lengths of intervals
interv = intervals(data1)
get_no_small_intervals(interv)
plot(interv)
#print(interv_list[2:15])
