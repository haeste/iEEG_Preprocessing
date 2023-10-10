# Python module
import multiprocessing
import time
import scipy.io as sio
import os
import numpy as np
from bandpower_functions import artefactsMetrics


# Import your local function
# This function should take the raw iEEG data (n.o chan x n.o samples) for the 30 second segment, a sample rate, and a list of bad channels (these can be ignored).
# It should return the computed metric for the 30 second segment, in a dict. 
# Each key should refer to a variable in your metric (if you metric computes only one thing per 30 seconds, then it will just has one key)
# ------------ UPDATE THIS LINE --------------------- #
from bandpower_functions import calculate_bandpowers
from fooof_csaba import fooof_computation


import json
##-----UPDATE---------#
f = open('./config_fooof.json')  # change to config_fooof.json to merge fooof outputs
config = json.load(f) 
RAW_INFO_DIR = config['RAW_INFO_DIR'] 
IN_RAW_DIR = config['IN_RAW_DIR'] 
OUTPUT_DIR = config['OUTPUT_DIR'] 
BAD_CHANNELS_DIR = config['BAD_CHANNELS_DIR'] 
OUT_PREFIX = config['OUT_PREFIX']
OUTPUT_CONCAT_DIR = config['OUTPUT_CONCAT_DIR']
DATA_TEMP_DIR= './temp_data/'

# Go and read the raw data
def process_file(subject,mat_file, out_path, bad_ch_path, fs):

    raw_file = mat_file

    iEEGraw_data = sio.loadmat(raw_file)["EEG"]
    z_threshold = 3 # if z-score is above 3 or below -3 then the channel is flagged as outlier/bad

    if np.sum(np.isnan(iEEGraw_data)) ==0:
        # Compute amplitude range for every 30s windows
        ampl_range_all = artefactsMetrics.amplrange_axis1(iEEGraw_data)

        # standradise each 30s window amplitude ranges across channels (range - mean(range of all channels))/std(range of all channels)
        ampl_range_all_stand = artefactsMetrics.standardise(ampl_range_all)

        bad_ch_ind = [i for i,v in enumerate(ampl_range_all_stand) if abs(v) > z_threshold]

    else:
       
       bad_ch_ind = []
    
    #--------- UPDATE Add your own function --------------------#
    #metric_computed = calculate_bandpowers.bandpower_process(iEEGraw_data, fs, bad_ch_ind)
    
    features = open('./fooof_csaba/fooof_features.json') 
    fooof_features = json.load(features) 
    
    metric_computed = fooof_computation.run_fooof_calc(iEEGraw_data, fs, fooof_features)
    #print("Processing:{}".format(mat_file))
    # Save band power for the 30s segment
    idd = str(os.path.basename(mat_file).split("raw_")[1].split(".mat")[0])
    sio.savemat(os.path.join(out_path, OUT_PREFIX+"{}_{}.mat".format(subject, idd)), metric_computed, do_compression = True)

    if len(bad_ch_ind) !=0:
        # Save bad channels info for the 30s segment
        bad_ch_ind_strct = {"BadChan": bad_ch_ind}
        sio.savemat(os.path.join(bad_ch_path, "BadChan_{}_{}.mat".format(subject, idd)), bad_ch_ind_strct, do_compression = True)
# ------------ UPDATE THIS LINE --------------------- #

if __name__ == '__main__':
    #subject_list = ['s001','s002','s003', 's004', 's005']
    subject_list = os.listdir(IN_RAW_DIR)
    subject_list = ['1038']
    for subject in subject_list:
        print(subject)
        
        raw_info = sio.loadmat(os.path.join(RAW_INFO_DIR, subject,"rawInfo_{}.mat".format(subject)))
        
        # The channels to keep; these are the ones that are included in the list and in at least one edf file.
        # The final channels included in the raw data
        channelsKeep = list(raw_info["channelsKeep"])
        
        # The final fs
        fs = raw_info["fs"][0][0]
        
        
        # The path where the raw data are
        raw_data_path = os.path.join(IN_RAW_DIR, subject)
        
        # Read the list of files exist in RAW_DATA_DIR
        raw_files = os.listdir(raw_data_path)
        
        
        out_path = os.path.join(OUTPUT_DIR, subject)
        os.makedirs(out_path, exist_ok=True)
        
        badCh_path = os.path.join(BAD_CHANNELS_DIR, subject)
        os.makedirs(badCh_path, exist_ok=True)
        
        # This can be uncommented and used for testing - processes in serial, allowing easier debugging.
        # for file in raw_files:
        #     process_file(subject, os.path.join(IN_RAW_DIR,subject,file), out_path,badCh_path, fs)
   
        pool = multiprocessing.Pool()
        start = time.time()
        results = []
        for file in raw_files:
            result = pool.apply_async(process_file, [subject,os.path.join(IN_RAW_DIR,subject,file), out_path,badCh_path, fs])
            results.append(result)
                    
        pool.close()
        pool.join()
        ready = [result.ready() for result in results]
        successful = [result.successful() for result in results]
        
        if all(ready) and all(successful):
            print('All files successfully processed.')
        print("\n job done!!: {}".format(time.time()-start))
        
        raw_info_path = os.path.join(RAW_INFO_DIR)
        raw_info = sio.loadmat(os.path.join(raw_info_path, subject, "rawInfo_{}.mat".format(subject)))

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

        # for ff in sorted_metric_files:
        #     os.remove(os.path.join(metric_path, ff))






