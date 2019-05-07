###
### PLOT 2D PLOTS TO DETERMINE THE BEST PARAMETERS:
# Hysteresis window size, rolling window size, hysteresis minimum

import autopark as auto
import matplotlib.pyplot as plt
import numpy as np
import pylab

windows = np.array([ 40, 50, 60])
minimums = np.array([0, 5, 10, 15 ])
hyst_windows = np.array([0,5,7,8,10])



data = auto.get_data("updated_rain_data.h5")
column , threshold = auto.get_column( data)


rol_column40 = auto.calculate_rolling_sum(data, column, threshold,  40)
rol_column50 = auto.calculate_rolling_sum(data, column, threshold,  50)
rol_column60 = auto.calculate_rolling_sum(data, column, threshold,  60)
    # Below, hyst takes in the rolling sum and
data['hysteresis_5_5'] = auto.calculate_hyst(rol_column40, 5, 5)
data['hysteresis_5_7'] = auto.calculate_hyst(rol_column40, 5, 7)
data['rolling_sum40'] = rol_column40
data['rolling_sum50'] = rol_column50
data['rolling_sum60'] = rol_column60

sel = slice('2018-10-09 17:00', '2018-10-10 08:00')

f, (ax1, ax2) = plt.subplots(nrows =2,sharex = True)
ax1.plot((data[sel].rolling_sum40),'.:', label = 'rolling sum')
ax1.plot((data[sel].hysteresis_5_5)*20, '.:', color = "g", label = " Hysteresis window = 5")
ax1.axhline(y=5, color = 'brown', label = "hysteresis min")
ax1.axhline(y=10, color = 'brown', label = "hysteresis max")
ax1.legend()
ax1.grid()
ax2.plot((data[sel].hysteresis_5_7)*20, '.:', color = "r", label = " Hysteresis window = 7")
ax2.plot((data[sel].rolling_sum40),'.:', label = 'rolling sum')
ax2.axhline(y=5, color = 'brown', label = "hysteresis min")
ax2.axhline(y=12, color = 'brown', label = "hysteresis max")
ax2.grid()


#plt.subplot(1,1,1)

#plt.plot((data[sel].rolling_sum40),'.:', label = 'rolling sum')
#plt.plot((data[sel].hysteresis_5_5)*20, '.:', color = "r", label = " Hysteresis window = 5")
#plt.plot((data[sel].hysteresis_5_7+0.5)*20, '.:', color = "g", label = " Hysteresis window = 7")

#    plt.plot(10,'-', color = "g", label = "lower threshold")
#    plt.plot(15, '-', color = "y", label = "upper threshold")
plt.title("Rains with Window = 40 min & Hysteresis minimum 5 min")
plt.legend()
plt.savefig("comparison_Sum40_5_5and7")
plt.show(block=True)
