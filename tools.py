import numpy as np
import pandas as pd

def calculate_hyst(rolling, hyst_min, hyst_window):
    """Prevent decisions from happening "too quickly"
    """
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

    new_column = pd.Series(hyst, index=rolling.index)
    return new_column


def intervals(data_column):
    """ Determine the length of intervals between decisions
    """
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
    """Determine the length and number of intervals that are less than 10 and 20 minutes
    """
    small_intervals = []
    medium_intervals = []
    for i in np.array(intv_list):
        if i <= 10:
            small_intervals.append(i)
        if 10 <= i <= 20:
            medium_intervals.append(i)
    return len(small_intervals)
