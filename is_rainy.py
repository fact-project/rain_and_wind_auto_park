import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.table import Table
import astropy

#Get data, convert time

def get_data(data):
    stuff = pd.read_hdf(data)
    stuff['good_time'] = pd.to_datetime(stuff.Time*24*60*60*1e9)
    stuff.set_index('good_time', inplace=True)
    stuff.sort_index(inplace=True)
    return stuff

def plot(stuff):
    plt.figure(figsize=(12, 4))
    plt.plot(stuff['2018-11-23 ':'2018-11-23 12'].rainy, '-', alpha=0.5);

def add_column(column):
    # column is stuff['rain']
    count_rainy = 0
    count_dry = 0
    rains = []
    for rain in column:
    if rain >0:
        count_rainy += 1
        count_dry = 0
        if count_rainy >= 10:
            rains.append(True)
        else:
            rains.append(False)
    else:
        count_rainy = 0
        count_dry += 1
        if count_dry >= 10:
            rains.append(False)
        else:
            rains.append(True)
    stuff['raining'] = rains
    stuff.raining = stuff.raining.astype('float')
    return stuff
