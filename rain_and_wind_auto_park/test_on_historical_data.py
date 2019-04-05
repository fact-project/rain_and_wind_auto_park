'''
This script will be an executable program, just like `auto_park`
which is implemented in `script.py`.

But it will look at historical data from old aux files, instead of looking at
current data.

Also instead of really modifying the scheduling DB it will just write
out the booleans from the main:

 - is_rainy
 - is_stormy
 - we_should_park = is_rainy or is_stormy
 - we_are_parking

and the current **time** into an HDF5 file, for testing.

In addition it might write out (maybe into a simple text file?) when
ever it would have scheduled a suspend or a RESUME.

... or maybe it would need some fake schedule data for this.
... not yet clear

'''
from docopt import docopt
from script import (
    make_rain_decision,
    make_storm_decision,
)


def main(**kwargs):

    we_should_park = False
    we_are_parking = False

    while True:
        rain_update = fake_fetch_rain_sensor_update()
        is_rainy = make_rain_decision(rain_update)

        wind_update = fake_fetch_wind_sensor_update()
        is_stormy = make_storm_decision(wind_update)

        we_should_park = is_rainy or is_stormy

        if we_should_park and not we_are_parking:
            enter_suspend_task_into_schedule()
            we_are_parking = True
        elif we_should_park and we_are_parking:
            # nothing to be done
            pass
        elif not we_should_park and we_are_parking:
            enter_resume_task_into_schedule()
            we_are_parking = False
        elif not we_should_park and not we_are_parking:
            # nothing to be done
            pass
        else:
            # there are only 4 combinations so this else should never happen
            raise Exception('we should never reach this line!')


def fake_fetch_rain_sensor_update(current_time):
    '''fake fetch new rain sensor data from tonights AUX file.

    find the correct AUX file, based on the current time and read the
    correct line from the file, i.e. the line which is just a bit younger
    than the current time.
    '''
    return None

def fake_fetch_wind_sensor_update(current_time):
    '''fetch new wind sensor data from tonights AUX file.

    find the correct AUX file, based on the current time and read the
    correct line from the file, i.e. the line which is just a bit younger
    than the current time.
    '''
    return None


def fake_enter_suspend_task_into_schedule(current_time):
    '''fake making an entry in the schedule DB. I do not yet know how.
    We could actually have a copy of the real DB, and make entries in that
    copy ... and in the end, we just store that copy.
    This would allow us to see, how the decision makers would have performed
    during the last few years.


    Yep .. that sounds nice.

    Of course we must not forget this special:
        - put a RESUME after the next SHUTDOWN
    '''
    pass


def fake_enter_resume_task_into_schedule(current_time):
    '''same as above, just for resume. and of course we must not forget
    the special treatment of the RESUME, which should be after the next SHUTDOWN,
    which needs to be removed by us.
    '''
    pass


def entry():
    '''entry point to the automatic park program
    '''
    arguments = docopt(__doc__)
    main(**arguments)


if __name__ == '__main__':
    entry()
