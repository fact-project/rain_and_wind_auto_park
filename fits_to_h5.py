#!/usr/bin/env python
'''
Program to collect all RAIN fits files and bundle them up in an h5 file.
<out_file_name>    for example "foo.h5"
<path_to_aux_folder>   the path where your fact aux file tree starts

Usage:
  fits_to_h5.py <path_to_aux_folder> <out_file_name> <type_name>

Options:
  -h --help     Show this screen.
  --version     Show version.
'''
import sys
import glob
from astropy.table import Table
import pandas as pd
from tqdm import tqdm
from docopt import docopt
from fact.auxservices import AuxService

def main(path_to_aux_folder, out_file_name, type_name):
    '''collect all RAIN fits files from `path_to_aux_folder`
    and bundle them into an HDF5 file in `out_file_name`

    type_name should be either "RAIN" or "WEATHER"
    '''
    glob_expression = path_to_aux_folder + f"/*/*/*/*{type_name}*"

    frames = []
    for path in tqdm(sorted(glob.glob(glob_expression))):
        try:
            dataframe = AuxService.read_file(path)
        except Exception as e:
            print(f'error in {path}')
        frames.append(dataframe)

    result = pd.concat(frames, sort=False)
    result.sort_values('Time', inplace=True)
    result.set_index(
        pd.to_datetime(result.Time, unit="D"),
        inplace=True
    )
    result.sort_index(inplace=True)  # this should not be necessary
    del result['Time']

    result.to_hdf(out_file_name, key='data')


if __name__ == "__main__":

    arguments = docopt(__doc__, version='rain_collect_data 0.1')

    main(
        path_to_aux_folder=arguments['<path_to_aux_folder>'],
        out_file_name=arguments['<out_file_name>'],
        type_name=arguments['<type_name>'],
    )
