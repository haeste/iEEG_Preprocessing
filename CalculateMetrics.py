# Python module
import multiprocessing
import time
import scipy.io as sio
import os
# Import your local function
# This function should take a subject ID, the location of a 30 second segment 
# of raw iEEG data (all channels), locations for the output file and bad channels file, 
# and a sampling frequency. e.g. def process_file(subject,mat_file, out_path, bad_ch_path, fs):
# Your function should load the 30 second segment, calculate your metric on it, then save this output to file.
# Look at calculate_bandpowers.py as an example for how to save to file. 
# ------------ UPDATE THIS LINE --------------------- #
from bandpower_functions import calculate_bandpowers

RAW_INFO_DIR = './sample_data/info/' # pointer to info files
IN_RAW_DIR = './sample_data/raw_data/' # pointer to raw data 30 second segment files

# ------------ UPDATE THIS LINE --------------------- #
OUTPUT_DIR = './output/bandpowers/data/' # location to save output data
# ------------ UPDATE THIS LINE --------------------- #
BAD_CHANNELS_DIR = './output/bandpowers/bad_channels/' # location to save bad channels

if __name__ == '__main__':
    subject_list = [ 's001', 's002', 's003']
    
    for subject in subject_list:
        
        
        raw_info = sio.loadmat(os.path.join(RAW_INFO_DIR, "rawInfo_{}.mat".format(subject)))
        
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
        #
        # for file in raw_files:
        #     calculate_bandpowers.process_file(subject, os.path.join(IN_RAW_DIR,subject,file), out_path,badCh_path, fs)
   
        pool = multiprocessing.Pool(8)
        start = time.time()
    
        for file in raw_files:
            # ------------ UPDATE THIS LINE --------------------- # Add your own function
            pool.apply_async(calculate_bandpowers.process_file, [subject,os.path.join(IN_RAW_DIR,subject,file), out_path,badCh_path, fs])
    
        pool.close()
        pool.join()
    
        print("\n job done!!: {}".format(time.time()-start))








