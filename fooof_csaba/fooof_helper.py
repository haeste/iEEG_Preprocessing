#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 10:16:00 2023

@author: c2056366
"""

import numpy as np
from bandpower_functions import artefactsMetrics
from bandpower_functions.IIR_notch_filter import *
from bandpower_functions.FilterEEG import *
from bandpower_functions import Pyweltch_method_abnormalities

def fooof_clean_prep(fooof_features,EEG,fs):
   
                  
    # Data for the "which_channel" channel
    
    EEGdata_Channel = EEG
    
    
    # time vector
    N = EEGdata_Channel.shape[0]
    timevec = np.arange(0,N)/fs
    overlap = fooof_features["overlap"]
    winLength = fooof_features["winLength"]
    # window length in seconds*srate
    winlength = int(winLength*fs)

    # number of points to overlap
    nOverlap = np.round(winlength * overlap)

    # Get the non-NaN values
    partnonNaN = ~np.isnan(EEGdata_Channel)
                      
    notched_data = iirnotch_filter(fs, fooof_features["notch_freq"], 35, EEGdata_Channel[partnonNaN])
    # Butterworth bandpass filter
    butter_filtered_data = FilterEEG_Channel(notched_data, fooof_features["butter_cutoff"], fs, "bandpass", fooof_features["butter_order"])
    srate_new = 200
    # Downsample the data to 200Hz
    downsampled_data = Pyweltch_method_abnormalities.downsample_decimate(signal = butter_filtered_data, fs=fs, target_fs=srate_new, method = "decimate")
    ## The Welch's method will be applied to the filtered data from previous step
    winlength_new = int(winLength*srate_new)
    # number of points to overlap
    downsample_length = np.shape(downsampled_data)[0]/np.shape(partnonNaN)[0]
    downsampled_data=downsampled_data.reshape(np.shape(partnonNaN)[0],int(downsample_length))
    nOverlap_new = np.round(winlength_new * overlap)
    return downsampled_data, srate_new, winlength_new, nOverlap_new


