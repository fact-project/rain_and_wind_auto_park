#!/usr/bin/env python
'''
Program to collect all RAIN fits files and bundle them up in an h5 file.

Usage: ./rain_collect_data.py <path_to_aux_folder> <out_file_name>

out_file_name: for example "foo.h5"
'''
import sys
import glob
from astropy.table import Table
import pandas as pd
from tqdm import tqdm


def main(path_to_aux_folder, out_file_name):
    '''collect all RAIN fits files from `path_to_aux_folder`
    and bundle them into an HDF5 file in `out_file_name`
    '''

    try:
        glob_expression = path_to_aux_folder + "/*/*/*/*RAIN*"

        frame = []
        for path in tqdm(glob.glob(glob_expression)):
            table = Table.read(path)
            dataframe = table.to_pandas()
            frame.append(dataframe)

        result = pd.concat(frame)
        result.to_hdf(out_file_name, key='data')
    except ValueError:
        print('no fits files found, maybe wrong path?')


if __name__ == "__main__":

    main(
        path_to_aux_folder=sys.argv[1],
        out_file_name=sys.argv[2],
    )
