'''
This script will be the executable program, which is supposed to run 24/7 on
La Palma (probably on newdaq) and which is supposed to modify the Scheduling
DB, in order to automatically park FACT in case of adverse weather conditions

Usage:
    auto_park <base_path>
'''
from docopt import docopt
from datetime import datetime


def main(**kwargs):
    credentials = read_credentials_from_config_file()
    base_path = kwargs['<base_path>']


    we_should_park = False
    we_are_parking = False

    while True:
        current_time = datetime.utcnow()
        rain_update = fetch_sensor_update(current_time, base_path, 'RAIN_SENSOR_DATA')
        is_rainy = make_rain_decision(rain_update)

        wind_update = fetch_sensor_update(current_time, base_path, 'MAGIC_WEATHER_DATA')
        is_stormy = make_storm_decision(wind_update)

        we_should_park = is_rainy or is_stormy

        if we_should_park and not we_are_parking:
            enter_suspend_task_into_schedule(credentials, current_time)
            we_are_parking = True
        elif we_should_park and we_are_parking:
            # nothing to be done
            pass
        elif not we_should_park and we_are_parking:
            enter_resume_task_into_schedule(credentials, current_time)
            we_are_parking = False
        elif not we_should_park and not we_are_parking:
            # nothing to be done
            pass
        else:
            # there are only 4 combinations so this else should never happen
            raise Exception('we should never reach this line!')


def read_credentials_from_config_file(path=None):
    '''
    find the little trext file with username / password for
    Database access. Open this file and get the credentials.
    '''

    return ('username', 'password')


def fetch_sensor_update(current_time, base_path, service_name):
    '''fetch sensor update from just before current_time from the
    corresponding aux file, which belongs to the service_name-
    the base_path defines where to start searching for the aux files
    a typical base_path is = "/fact/aux"
    and a typical location for aux files looks like:
    "/fact/aux/2019/12/15/20191215.SERVICE_NAME.fits"

    the date of a telescope changes at noon.

    a pandas.Dataframe ...

    it should have:
     - row.Time
     - row.rain
     - row.counts
     - ...
    '''
    return None


def make_rain_decision(rain_update):
    '''make a decision if based on this update we assume it is rainy right now
    or not.

    Returns True if we assume it is rainy and False otherwise
    '''
    return False




def make_storm_decision(wind_update):
    '''make a decision if based on this update we assume it is stormy right now
    or not.

    Returns True if we assume it is stormy and False otherwise
    '''
    return False


def enter_suspend_task_into_schedule(db_credentials):
    '''make an entry in the scheduling DB, which is represented on this website:
    https://www.fact-project.org/schedule/

    In particular, make a "SUSPEND" entry for "right now"
    and in addition make a "RESUME" entry
    after the most recent "SHUTDOWN" entry.
    '''
    pass


def enter_resume_task_into_schedule(db_credentials):
    '''make an entry in the scheduling DB, which is represented on this website:
    https://www.fact-project.org/schedule/

    In particular, make a "RESUME" entry for "right now"
    and in addtion remove the "RESUME" task
    after the most recent "SHUTDOWN" entry,
    if it exists. It should exist. If it does not exist, print a warning.
    '''
    pass


def entry():
    '''entry point to the automatic park program
    '''
    arguments = docopt(__doc__)
    main(**arguments)


if __name__ == '__main__':
    entry()
