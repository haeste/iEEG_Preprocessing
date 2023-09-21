# Python module
import scipy.io as sio
import json
import numpy as np

import sys
import os
# internal modules

import json
##-----UPDATE---------#
f = open('./config_bp.json') # change to config_fooof.json to merge fooof outputs
config = json.load(f) 
RAW_INFO_DIR = config['RAW_INFO_DIR'] 
IN_RAW_DIR = config['IN_RAW_DIR'] 
OUTPUT_DIR = config['OUTPUT_DIR'] 
BAD_CHANNELS_DIR = config['BAD_CHANNELS_DIR'] 
OUT_PREFIX = config['OUT_PREFIX']
OUTPUT_CONCAT_DIR = config['OUTPUT_CONCAT_DIR']

DATA_TEMP_DIR= './temp_data/'

subject_list = ['s001', 's002', 's003']


for subject in subject_list:
    print(subject)
    raw_info_path = os.path.join(RAW_INFO_DIR)
    raw_info = sio.loadmat(os.path.join(raw_info_path, "rawInfo_{}.mat".format(subject)))

    # The channels to keep; these are the ones that are included in the list and in at least one edf file.
    # The final channels included in the raw data
    channelsKeep = list(raw_info["channelsKeep"])

    # The final fs
    fs = 200

    metric_path = os.path.join(OUTPUT_DIR, subject)

    metric_files = os.listdir(metric_path)
    sorted_metric_files = sorted(metric_files, key = lambda x: int(x.split(OUT_PREFIX)[1].split(".mat")[0].split("_")[1]))

    n_files = len(metric_files)
    # n_files = len(t_start)
    
    path_memmap = os.path.join(DATA_TEMP_DIR, subject)
    os.makedirs(path_memmap, exist_ok=True)
    
    metric_computed = sio.loadmat(os.path.join(metric_path, sorted_metric_files[0]))
    metrics = list(metric_computed.keys())
    metrics = [m for m in metrics if not m.startswith('__')]
    target_data = {}
    for m in metrics:
        target_data[m] = np.memmap(os.path.join(path_memmap, m+"{}.buffer".format(subject)), mode='w+',
                                      dtype=np.float32,
                                      # dtype=np.double,
                                      shape=(len(channelsKeep), n_files))

    idx = 0
    for ff in sorted_metric_files:
        
        metric_computed = sio.loadmat(os.path.join(metric_path, ff))
        for m in metrics:
            target_data[m][:, idx:idx+1] = metric_computed[m].reshape((len(channelsKeep), 1)) 

        idx += 1

    for m in metrics:
        target_data[m].flush()

    super_dict_ch = target_data
    super_dict_ch['channels'] = channelsKeep
    super_dict_ch['subject'] = subject
    metric_concat_path = os.path.join(OUTPUT_CONCAT_DIR, subject)
    os.makedirs(metric_concat_path, exist_ok=True)

    sio.savemat(os.path.join(metric_concat_path, OUT_PREFIX+"{}.mat".format(subject)), super_dict_ch)


    # Remove temporary files
    for m in metrics:
        os.remove(os.path.join(path_memmap, m+"{}.buffer".format(subject)))

