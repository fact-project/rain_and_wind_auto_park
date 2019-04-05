'''
This script will be the executable program, which is supposed to run 24/7 on
La Palma (probably on newdaq) and which is supposed to modify the Scheduling
DB, in order to automatically park FACT in case of adverse weather conditions

Usage:
    auto_park
'''
from docopt import docopt


def main(**kwargs):

    credentials = read_credentials_from_config_file()

    we_should_park = False
    we_are_parking = False

    while True:
        rain_update = fetch_rain_sensor_update()
        is_rainy = make_rain_decision(rain_update)

        wind_update = fetch_wind_sensor_update()
        is_stormy = make_storm_decision(wind_update)

        we_should_park = is_rainy or is_stormy

        if we_should_park and not we_are_parking:
            enter_suspend_task_into_schedule(credentials)
            we_are_parking = True
        elif we_should_park and we_are_parking:
            # nothing to be done
            pass
        elif not we_should_park and we_are_parking:
            enter_resume_task_into_schedule(credentials)
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


def fetch_rain_sensor_update():
    '''fetch new rain sensor data from tonights AUX file.
    if there is no update, i.e. if there is no new line yet in the AUX file
    return None

    if there is a new line, return a row, from a pandas.Dataframe ...

    it should have:
     - row.Time
     - row.rain
     - row.counts
    '''
    return None


def make_rain_decision(rain_update):
    '''make a decision if based on this update we assume it is rainy right now
    or not.

    Returns True if we assume it is rainy and False otherwise
    '''
    return False


def fetch_wind_sensor_update():
    '''fetch new wind sensor data from tonights AUX file.
    if there is no update, i.e. if there is no new line yet in the AUX file
    return None

    if there is a new line, return a row, from the astropy.Table object
    '''
    return None


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
