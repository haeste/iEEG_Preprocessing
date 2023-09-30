#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 13:18:21 2023
Fooof function to run on continuus iEEG data
Inputs: 
    EEG:raw data,
    fs: sampling frequency,
    fooof_features: fooof model parameters
Returns:
    Aperiodic components: Offset and Exponent
    Fooofed PSD
@author: Csaba Kozma
"""


def run_fooof_calc(EEG,fs,fooof_features):


   
    
    # Import the FOOOF object
    import fooof
    # Import some internal functions
    from fooof.sim.gen import gen_aperiodic
    from fooof_csaba import fooof_helper
    #Data org libraries
    import scipy
    import pandas as pd
    import numpy as np
    
    #Preallocation of varables and model
    fm = fooof.FOOOF(fooof_features["peak_width_limits"], fooof_features["max_n_peaks"],
               fooof_features["min_peak_height"], fooof_features["peak_threshold"],
               fooof_features["aperiodic_mode"])
    Offsets_channel = []
    Slope_channel = []
    Goodness_of_fit = []
    Error_of_fit = []
    final_fit = []
   

    fooof_aperiodic_cmps = {'Offsets': [], 'Slopes': [],'GOF': [],'EOF': []}
    fooof_features_output = pd.DataFrame(fooof_aperiodic_cmps)
    if np.any(np.isnan(EEG)) or np.any(np.isinf(EEG)):
        fooof_features_output['Offsets']=[np.nan]*EEG.shape[0]
        fooof_features_output['Slopes']=[np.nan]*EEG.shape[0]
        fooof_features_output['GOF']=[np.nan]*EEG.shape[0]
        fooof_features_output['EOF']=[np.nan]*EEG.shape[0]
        ## Concatonate final fit channels
        final_fit=[np.nan]*EEG.shape[0]
        print('NaN present.')
    else:
        downsampled_data, srate_new, winlength_new, nOverlap_new = fooof_helper.fooof_clean_prep(fooof_features,EEG,fs)
        f, Pxx_den = scipy.signal.welch(downsampled_data, fs=srate_new, nperseg=winlength_new,
                                noverlap=nOverlap_new, detrend=False,average='median')
        
        for i in range(Pxx_den.shape[0]):
            
            fm.fit(f, Pxx_den[i,:], fooof_features["freq_range"])
            init_ap_fit = gen_aperiodic(fm.freqs, fm._robust_ap_fit(fm.freqs, fm.power_spectrum))
            final_fit.append(fm.fooofed_spectrum_)
            Offsets_channel.append( fm.aperiodic_params_[0])
            Slope_channel.append(fm.aperiodic_params_[1])
            Goodness_of_fit.append(fm.r_squared_)
            Error_of_fit.append(fm.error_)
           
           
        fooof_features_output['Offsets']=Offsets_channel
        fooof_features_output['Slopes']=Slope_channel
        fooof_features_output['GOF']=Goodness_of_fit
        fooof_features_output['EOF']=Error_of_fit
        ## Concatonate final fit channels
        #final_fit=np.vstack(final_fit)

    output = {'Offsets': list(fooof_features_output['Offsets']), 'Slopes':list(fooof_features_output['Slopes']),'EOF': list(fooof_features_output['EOF']), 'GOF':list(fooof_features_output['GOF'])}
    return output
