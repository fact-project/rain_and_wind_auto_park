'''Find out the total number of hours of data taking for the Rain + Wind Algorithm.
Compare it with the planned number of hours and actual number of hours.
For wind, can compare different methods as shown below in the comments (~ line 46)

Additionally, look at a quality plot for the runs that would be eliminated if the algorithm were to be in used.
Can change the window size, hyst min, hyst max below (~line 9 for window size, ~line 28 for hyst parameters)

'''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import autopark2 as auto


windows = np.array([20, 30, 40, 50 , 60])
window = 20

#Get the rain and the wind data both!
## Rain data starts from 2018-05-24
wind = auto.get_data("all_wind_data.h5","2018-05-24", "2019-03-30")
rain = auto.get_data("updated_rain_data.h5","2018-05-24", "2019-03-30")

    ## New Data! <3
hadron_rates = pd.read_hdf("hadron_rate.h5")
quality = hadron_rates.query('on_time > 100 & fZenithDistanceMean < 40 & fRunTypeKey==1 & hadron_rate < 4.8')
series1 = quality["fRunStart"].astype(str)
runstart = series1.tolist()
series2 = quality["fRunStop"].astype(str)
runstop = series2.tolist()
##Use Autopark2 for both data sets...

lost_good_run_list = []
for w in windows:
    for data in [wind,rain]:
        type, threshold, name = auto.determine_data_type(data)
        if type == "rain":
            col = data.rain
            hyst_min = 10
            hyst_window = 10
        else:
            col = data.v_max
            data = auto.wind_methods(data, threshold, window)
            hyst_min = 0
            hyst_window = 2
        data = auto.make_decision(data, col,threshold, w, hyst_min, hyst_window)
        ## Here cut the morning data. We only need data from observation time
        ## (The decisions were already made in previous lines using all data)
        data = data[data['take_data'] == True]

    ## Just to make sure , cut data again
    rain = rain[rain.take_data == True]
    wind = wind[wind.take_data == True]

    ## Rename the decisions properly
    # We will compare "parked due to rain", "parked due to storm", "actually parked" and "parked due to rain or storm"
    rain["rain_park"]= rain.park
    wind['planned_take_data'] = wind.take_data
    wind['actual_parked'] =wind.turned_off

    ### Decide on wind method Here
    # method = wind.park
    method = wind.park_avg_plus_std
    # method = wind.quantile_park
    # method = wind.quantile_park2
    wind['wind_park'] = method
    ## Wind


    ## Create a new clean data frame for this comparison
    data_taking = pd.DataFrame(index=data.index)
    data_taking = data_taking.join(rain.rain_park,how = 'outer')
    data_taking = data_taking.join(wind.wind_park, how = 'outer')
    data_taking = data_taking.join(wind.actual_parked, how = 'outer')
    data_taking = data_taking.join(wind.planned_take_data, how = 'outer')

    data_taking = data_taking[~data_taking.rain_park.isna()]

    #Create the "parked due to rain or storm" column
    data_taking["algorithm_parked"] = data_taking.rain_park | data_taking.wind_park


    ###Now calculate total hours...
    data_taking[data_taking.algorithm_parked == True]
    # print("###############################################################################")
    # print("TOTAL NUMBER OF HOURS OF DATA TAKING")
    ## For the PLANNED number of total_hours
    total_hours_planned = data_taking[data_taking.planned_take_data == True]
    total_hours = (len(total_hours_planned))/60
    total_hours_h = (len(data_taking.algorithm_parked))/60
    # print("Planned = ",total_hours, " hours")


    ## For the ACTUAL
    actual_data_taken = data_taking[data_taking['actual_parked'] == False]
    actual_hours = (len(actual_data_taken))/60
    # print("Actual = ",actual_hours, " hours")

    algorithm_parked = data_taking[data_taking.algorithm_parked == False]
    algorithm_parked_hours = (len(algorithm_parked))/60
    # print("Algorithm = ",algorithm_parked_hours," hours")

    ###############################################################################################################
    ## Data Quality PLOT
    ## Takes a while :/



    ## Specifically for rain...
    parked = []
    for start, stop in zip(runstart, runstop):
        sumTrue = rain.park[start:stop].sum()
        sumAll = rain.park[start:stop].count()
        parked_ratio = sumTrue/sumAll
        if parked_ratio >= 0.2:
            parked.append(True)
        else:
            parked.append(False)

    #quality.set_index('fRunStart', inplace = True)
    quality['parked'] = parked
    # print( " ")
    # print("###############################################################################")
    # print("Total Parked runs & Run Quality")
    parked_runs = quality[quality.parked == True].parked.count()
    total_runs = quality.parked.count()
    # print("Number of runs that were parked is ",parked_runs)
    # print("Total number of runs is ", total_runs)
    # print("Total saved is ",(parked_runs/total_runs)*100)

    ### GOOD RUNS LOST
    #lost_good_runs = quality[(quality.hadron_rate >3.5) & (quality.parked == True)].parked.count()
    good_run = quality[(quality.hadron_rate >3.5) & (quality.parked == True)].fRunStart
    lost_good_runs = good_run.count()

    good_run_time = good_run.values
    lost_good_run_list.append(lost_good_runs)
    print("Good Runs Lost For Window = ",w,":")
    print("|| Window size  ||  # Good runs lost || # Parked Runs || % Of parked runs ||")
    print("||",w, "    || ",lost_good_runs,"      ||   ", parked_runs,"   ||   ", (parked_runs/total_runs)*100, "   ||")
    print("Good runs lost are ", good_run)
    print("Times of lost good runs are ", good_run_time)
    print(" #############################################################################3")

fig, ax = plt.subplots()
ax.plot(windows, lost_good_run_list, 'o', label = "lost_good_runs")
ax.legend(fontsize = 22)
ax.set_xlabel("Window size (minutes)", fontsize = 22)
plt.show(block=True)

# ### Run quality plot
# plt.figure(figsize=(12, 4))
# plt.hist(quality[quality.parked == True]['hadron_rate'], alpha = 0.7, bins=np.arange(0, 5, 0.03), label='Parked', color = "orange", log = True)
# plt.hist(quality[quality.parked == False]['hadron_rate'], alpha = 0.2, bins=np.arange(0,5, 0.03), label='Taking Data', log = True)
# plt.title("Parked runs with the Rain method, 20 minute Window", fontsize = 30)
# plt.legend( fontsize = 22)
# plt.xlabel('hadron rate (1/s)', fontsize = 22)
# plt.show(block = True)
