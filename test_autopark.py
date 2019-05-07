###
### PLOT 2D PLOTS TO DETERMINE THE BEST PARAMETERS:
# Hysteresis window size, rolling window size, hysteresis minimum

import autopark as auto
import matplotlib.pyplot as plt
import numpy as np


windows = np.array([20, 30, 40, 50, 60])
minimums = np.array([0, 5, 10, 15,20 ])
hyst_windows = np.array([0,2.5,5,7.5,10])


result = np.zeros((len(minimums), len(hyst_windows)))
#len(windows)))


for w,window in enumerate(hyst_windows):
         for m,min in enumerate(minimums):
             result[m,w] = auto.main("updated_rain_data.h5","2018-03-01", "2019-03-05", 40, min, window )



fig, ax = plt.subplots()
im = ax.imshow(result)

ax.set_xticks(np.arange(len(hyst_windows)))
ax.set_yticks(np.arange(len(minimums)))
ax.set_xticklabels(hyst_windows)
ax.set_yticklabels(minimums)

plt.setp(ax.get_xticklabels(), rotation = 45, ha= "right", rotation_mode = "anchor")

for i in range(len(minimums)):
    for j in range(len(hyst_windows)):
        text = ax.text(j , i, result[i,j], ha = "center", va="center", color = "w")


ax.set_title("Number of Intervals <= 20 minutes")
ax.set_xlabel("Hysteresis Window")
ax.set_ylabel("Minimum value of the Hysteresis Interval")
fig.tight_layout()
plt.show(block = True)





###########################3
# plt.pcolor(windows, minimums, result)
# plt.title("Number of Small Intervals")
# plt.xlabel("window size")
# plt.ylabel("Hysteresis Minimum")
# plt.colorbar()
# plt.show(block=True)


'''
small_intvs = []
for window in windows:
    for min  in minimums:
        small_int = main("updated_rain_data.h5","2018-03-01", "2019-03-05", window, min )
        d = {'w': window, 'm':min, 'r': small_int}
        small_intvs.append(d)

df = pd.DataFrame(small_intvs)
df.to_csv('dict_parameters.csv')

print(small_intvs)
#plt.plot(windows, small_intvs)
#plt.plot(small_intvs)
#plt.pcolormesh(windows,minimums,small_intvs)
#plt.contour(windows, minimums, small_intvs, colors = 'k', levels = [0])

#plt.show(block=True)
'''
