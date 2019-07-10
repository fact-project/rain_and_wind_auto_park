###
### PLOT 2D PLOTS TO DETERMINE THE BEST PARAMETERS:
# Hysteresis window size, rolling window size, hysteresis minimum

import autopark2 as auto
import matplotlib.pyplot as plt
import numpy as np


windows = np.array([30,45,60])
#[20, 30, 40, 50, 60])
#[5, 10,20, 30, 40]
minimums = np.array([0,1,2,3,4])
#[0, 5, 10, 15, 20])
hyst_windows = np.array([0, 1, 2,3,4])


result = np.zeros((len(minimums), len(hyst_windows)))
#len(windows)))


for w,window in enumerate(hyst_windows):
#for w,window in enumerate(windows):
         for m,min in enumerate(minimums):
             result[m,w] = auto.main("all_wind_data.h5","2018-01-01", "2019-03-30", 60, min, window )



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


ax.set_title("Wind: Number of Intervals <= 10 minutes")
ax.set_xlabel("Hysteresis Window")
ax.set_ylabel("Minimum value of the Hysteresis Region")
fig.tight_layout()
plt.show(block = True)




##############################################################
###########################
# plt.pcolor(windows, minimums, result)
# plt.title("Number of Small Intervals", fontsize = 45)
# plt.xlabel("window size", fontsize = 40)
# plt.ylabel("Hysteresis Minimum", fontsize = 40)
# plt.set_xticks(fontsize = 30)
# plt.set_yticks(fontsize = 30)
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
