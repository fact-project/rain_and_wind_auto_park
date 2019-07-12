# rain_and_wind_auto_park [![Build Status](https://travis-ci.org/fact-project/rain_and_wind_auto_park.svg?branch=master)](https://travis-ci.org/fact-project/rain_and_wind_auto_park)

A continously running process, which modifies the FACT schedule in order to park in case of adverse weather conditions

----

# Find your aux files and store the location in a shell variable
explain the guy to find where he has his aux files stored on his disk ... we use `your_aux_folder` for this from here on.

example

    AUX_FOLDER=/home/dneise/Downloads/blue_stick_21_06_2019/aux

# What to do first

    python fits_to_h5.py $AUX_FOLDER rain_data.h5 RAIN
    python fits_to_h5.py $AUX_FOLDER wind_data.h5 WEATHER


# Get the actual_schedule.h5 file

    Dominik gave this to Hazal and has to fucking find out how to generate that file from first principles!!!

# In order to create the report do:

    python autopark_quantiles.py wind_data.h5 2018-01-01 2019-03-31 60 40 10 overview_wind_performance.png
    python autopark_quantiles.py wind_data.h5 "2018-01-21 19:00" "2018-01-22 06:00" 60 40 10 20180121_performance.png
    python autopark_quantiles.py wind_data.h5 "2018-03-20 20:00" "2018-03-21 06:00" 60 40 10 20180320_performance.png
    python autopark_quantiles.py wind_data.h5 "2018-03-09 19:00" "2018-03-10 06:00" 60 40 10 20180309_performance.png
    python autopark_quantiles.py wind_data.h5 "2019-02-13 19:00" "2019-02-14 07:00" 60 40 10 20190213_performance.png
    python autopark_quantiles.py wind_data.h5 "2018-11-02 19:00" "2018-11-03 07:00" 60 40 10 20181102_performance.png


    python autopark_quantiles_centered.py wind_data.h5 2018-01-01 2019-03-31 60 40 10 overview_wind_performance_centered.png
    python autopark_quantiles_centered.py wind_data.h5 "2018-01-21 19:00" "2018-01-22 06:00" 60 40 10 20180121_performance_centered.png
    python autopark_quantiles_centered.py wind_data.h5 "2018-03-20 20:00" "2018-03-21 06:00" 60 40 10 20180320_performance_centered.png
    python autopark_quantiles_centered.py wind_data.h5 "2018-03-09 19:00" "2018-03-10 06:00" 60 40 10 20180309_performance_centered.png
    python autopark_quantiles_centered.py wind_data.h5 "2019-02-13 19:00" "2019-02-14 07:00" 60 40 10 20190213_performance_centered.png
    python autopark_quantiles_centered.py wind_data.h5 "2018-11-02 19:00" "2018-11-03 07:00" 60 40 10 20181102_performance_centered.png


# Good runs lost:

Get the file `hadron_rate.h5` somehow .. Dominik has to find out how again!!!

    python goodruns.py




###  Some notes for the weekend

 - maybe progress bar for autopark_quantiles?
 - the number of total hours or good hours should maybe be stored in a file.
 - for a study with different windows

