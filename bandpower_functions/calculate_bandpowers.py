#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 14 15:58:35 2023

@author: nct76
"""

import scipy.io as sio
import os
# internal modules
from bandpower_functions.artefactsMetrics import *
from bandpower_functions.Welch_with_NaNs_abnormalities import *
from bandpower_functions.IIR_notch_filter import *

def bandpower_process(EEGdata, fs, badch_indx):

    # Define EEG bands - those where used for SWEC data processing
    frange_bands = {'Delta': (1, 4),
                    'Theta': (4, 8),
                    'Alpha': (8, 13),
                    'Beta': (13, 30),
                    'Gamma1': (30, 47.5),
                    'Gamma2': (52.5, 57.5),
                    'Gamma3': (62.5, 77.5)
                    }

    butter_cutoff = [0.5, 80]

    butter_order = 2 # The 4th order of the (IIR) Butterworth filter, bandpass filter,
    #because this filter is forward-backward

    # this was used for SWEC data processing
    winLength = 2  # The window length in seconds for the Welch's method
    # this was used for SWEC data processing
    overlap = 0  # The percentage of overlapping to be performed in the windowing method

    notch = True
    #base_notch = 50 # 50Hz for the UCLH and GLAS data, while for the Canine data is 60Hz
    # THIS NEEDS TO BE SPECIDIED BY THE USER
    notch_freq = 50.0 # remove line noise and its harmonics

    quality_factor = 35
    NaNthreshold = 0

    print("Computing band power for this segment of data")
    list_all = EEG_Python_Welch_allChannels_abnormalities(EEGdata, badch_indx, fs, frange_bands,
                                            winLength, butter_cutoff, butter_order, overlap, notch,
                                            notch_freq, quality_factor, NaNthreshold)
    super_list = list_all["all_bp"]
    return super_list


# Go and read the raw data
def process_file(subject,mat_file, out_path, bad_ch_path, fs):

    raw_file = mat_file

    iEEGraw_data = sio.loadmat(raw_file)["EEG"]
    z_threshold = 3 # if z-score is above 3 or below -3 then the channel is flagged as outlier/bad

    if np.sum(np.isnan(iEEGraw_data)) ==0:
        # Compute amplitude range for every 30s windows
        ampl_range_all = amplrange_axis1(iEEGraw_data)

        # standradise each 30s window amplitude ranges across channels (range - mean(range of all channels))/std(range of all channels)
        ampl_range_all_stand = standardise(ampl_range_all)

        bad_ch_ind = [i for i,v in enumerate(ampl_range_all_stand) if abs(v) > z_threshold]

    else:
        bad_ch_ind = []

    bp_computed = bandpower_process(iEEGraw_data, fs, bad_ch_ind)
    print("Processing:{}".format(mat_file))

    # Save band power for the 30s segment
    idd = str(os.path.basename(mat_file).split("raw_")[1].split(".mat")[0])
    sio.savemat(os.path.join(out_path, "BPall_{}_{}.mat".format(subject, idd)), bp_computed, do_compression = True)

    if len(bad_ch_ind) !=0:
        # Save bad channels info for the 30s segment
        bad_ch_ind_strct = {"BadChan": bad_ch_ind}
        sio.savemat(os.path.join(bad_ch_path, "BadChan_{}_{}.mat".format(subject, idd)), bad_ch_ind_strct, do_compression = True)
