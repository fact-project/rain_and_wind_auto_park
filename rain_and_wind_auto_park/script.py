'''
This script will be the executable program, which is supposed to run 24/7 on
La Palma (probably on newdaq) and which is supposed to modify the Scheduling
DB, in order to automatically park FACT in case of adverse weather conditions

Usage:
    auto_park
'''
from docopt import docopt


def main(**kwargs):
    print('doing nothing yet, but my arguments are:', kwargs)


def entry():
    '''entry point to the automatic park program
    '''
    arguments = docopt(__doc__)
    main(**arguments)


if __name__ == '__main__':
    entry()
