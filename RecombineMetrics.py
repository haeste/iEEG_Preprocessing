# Python module
import scipy.io as sio
import json
import numpy as np

import sys
import os
# internal modules

RAW_INFO_DIR = './sample_data/info/'
IN_RAW_DIR = './sample_data/raw_data/'

# ------------ UPDATE THIS LINE --------------------- #
OUTPUT_DIR = './output/bandpowers/data/'
# ------------ UPDATE THIS LINE --------------------- #
OUTPUT_CONCAT_DIR = './output/bandpowers/concat_data/'
# ------------ UPDATE THIS LINE --------------------- #
BAD_CHANNELS_DIR = './output/bandpowers/bad_channels/'
# ------------ UPDATE THIS LINE --------------------- #
OUT_PREFIX = 'BPall_'
DATA_TEMP_DIR= './temp_data/'

subject_list = [ 's001', 's002', 's003']


def main(subject):

    raw_info_path = os.path.join(RAW_INFO_DIR)
    raw_info = sio.loadmat(os.path.join(raw_info_path, "rawInfo_{}.mat".format(subject)))

    # The channels to keep; these are the ones that are included in the list and in at least one edf file.
    # The final channels included in the raw data
    channelsKeep = list(raw_info["channelsKeep"])

    # The final fs
    fs = 200

    bp_path = os.path.join(OUTPUT_DIR, subject)

    bp_files = os.listdir(bp_path)
    sorted_bp_files = sorted(bp_files, key = lambda x: int(x.split(OUT_PREFIX)[1].split(".mat")[0].split("_")[1]))

    n_files = len(bp_files)
    # n_files = len(t_start)
    
    path_memmap = os.path.join(DATA_TEMP_DIR, subject)
    os.makedirs(path_memmap, exist_ok=True)
    
    bp_computed = sio.loadmat(os.path.join(bp_path, sorted_bp_files[0]))
    metrics = list(bp_computed.keys())
    metrics = [m for m in metrics if not m.startswith('__')]
    target_data = {}
    for m in metrics:
        target_data[m] = np.memmap(os.path.join(path_memmap, m+"{}.buffer".format(subject)), mode='w+',
                                      dtype=np.float32,
                                      # dtype=np.double,
                                      shape=(len(channelsKeep), n_files))

    idx = 0
    for ff in sorted_bp_files:
        
        bp_computed = sio.loadmat(os.path.join(bp_path, ff))
        for m in metrics:
            target_data[m][:, idx:idx+1] = bp_computed[m].reshape((len(channelsKeep), 1)) 

        idx += 1

    for m in metrics:
        target_data[m].flush()

    super_dict_ch = target_data
    super_dict_ch['channels'] = channelsKeep
    super_dict_ch['subject'] = subject
    bp_concat_path = os.path.join(OUTPUT_CONCAT_DIR, subject)
    os.makedirs(bp_concat_path, exist_ok=True)

    sio.savemat(os.path.join(bp_concat_path, OUT_PREFIX+"{}.mat".format(subject)), super_dict_ch)


    # Remove temporary files
    for m in metrics:
        os.remove(os.path.join(path_memmap, m+"{}.buffer".format(subject)))


if __name__ == '__main__':
    for subject in subject_list:
        main(subject)