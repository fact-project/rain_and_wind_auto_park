# coding: utf-8
import pandas as pd
import numpy as np
from astropy.table import Table
import astropy
import matplotlib.pyplot as plt
from matplotlib import interactive
from matplotlib import get_backend
get_backend()
interactive(True)
#from IPython import get_ipython
#get_ipython().run_line_magic('matplotlib', '')


stuff = pd.read_hdf('updated_rain_data.h5')
# just to be sure!

stuff['good_time'] = pd.to_datetime(stuff.Time * 24 * 60 * 60 * 1e9)
stuff.set_index('good_time', inplace=True)
stuff.sort_index(inplace=True)
del stuff['QoS']
del stuff['Time']


# nice to describe
# stuff['count'].describe()

count_rains = []
count_drys = []
count_rain = 0
count_dry = 0
for rain in stuff.rain:
    if rain > 0:
        count_rain += 1
        count_dry = 0
    else:
        count_dry += 1
        count_rain = 0

    count_rains.append(count_rain)
    count_drys.append(count_dry)

stuff['count_rains'] = count_rains
stuff['count_drys'] = count_drys

# may this:

## alternative to list ... prepare some arrays
"""
import numpy as np
count_rains = np.zeros(len(stuff), dtype=np.int64)
count_drys = np.zeros(len(stuff), dtype=np.int64)


count_rain = 0
count_dry = 0
for i, rain in enumerate(stuff.rain):
    if rain > 0:
        count_rain += 1
        count_dry = 0
    else:
        count_dry += 1
        count_rain = 0

    count_rains[i] = count_rain
    count_drys[i] = count_dry

stuff['count_rains'] = count_rains
stuff['count_drys'] = count_drys
"""

sel = slice('2018-10-19 00:00', '2018-10-21 00:00')
sel = slice(None, None)

# we plot rain - 100 so it does not overlap with count_rains
plt.plot(stuff[sel].rain - 100, '.:', label='rain - 100')
plt.plot(stuff[sel].count_rains, '.:', label='count_rains')
plt.plot(stuff[sel].count_drys, '.:', label='count_drys')
plt.grid()
plt.legend()
plt.show(block=True)
#plt.savefig('trial_april1st.png')
