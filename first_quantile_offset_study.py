# coding: utf-8
import numpy as np
import matplotlib.pyplot as plt
from wind_analysis import load_wind_data

df = load_wind_data('wind_data.h5')
df['v_med'] = df.v.rolling('30min').median().shift(periods=-15, freq='min')
diff = df.v_med - df.v

plt.hist(diff, bins=np.linspace(-50, +50, 200), log=True)
plt.grid()


#as one can see below, the 70% quantile seems to be systematically ~4km/h less than
# the 95% quantile therefore we subtract 4km/h in wind_analysis around line 80

plt.figure()
percentiles = np.linspace(0.01, 1-0.01, 101)
plt.plot(diff.quantile(percentiles), '.:')
plt.grid()

percentiles = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99]
offsets = diff.quantile(percentiles)
for perc, off in offsets.iteritems():
    print(f'{perc*100:.0f}% --> {off:.1f}km/h')

plt.show()
