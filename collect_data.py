#!/usr/bin/env python
'''
Program to collect all <name> fits files and bundle them up in an h5 file.
<out_file_name>    for example "rain.h5"
<name>             static part of file name, e.g. RAIN
<path_to_aux_folder>   the path where your fact aux file tree starts

Example:
    python collect_data.py ../aux RAIN_SENSOR_DATA rain.h5
    python collect_data.py ../aux MAGIC_WEATHER_DATA wind.h5

Usage:
  collect_data.py <path_to_aux_folder> <name> <out_file_name>

Options:
  -h --help     Show this screen.
  --version     Show version.
'''
import glob
from astropy.table import Table
import pandas as pd
from tqdm import tqdm
from docopt import docopt


def main(path_to_aux_folder, name, out_file_name):
    '''collect all RAIN fits files from `path_to_aux_folder`
    and bundle them into an HDF5 file in `out_file_name`
    '''

    try:
        glob_expression = path_to_aux_folder + "/*/*/*/*" + name + "*"

        frame = []
        for path in tqdm(sorted(glob.glob(glob_expression))):
            table = Table.read(path)
            dataframe = table.to_pandas()
            frame.append(dataframe)

        result = pd.concat(frame)

        result.sort_values('Time', inplace=True)
        result.to_hdf(out_file_name, key='data')
    except ValueError:
        print('no fits files found, maybe wrong path?')


if __name__ == "__main__":

    arguments = docopt(__doc__, version='collect_data 0.1')

    main(
        path_to_aux_folder=arguments['<path_to_aux_folder>'],
        name=arguments['<name>'],
        out_file_name=arguments['<out_file_name>'],
    )
