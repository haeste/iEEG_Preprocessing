# iEEG_Preprocessing
This repository contains short sample data for 3 subjects, in 30 second segments, along with methods to calculate metrics on these 30 second segments. 
Bandpowers are an initial example of metrics that can be calculated but more will be added. 
To calculate the bandpowers on the sample data, first run CalculateMetrics.py, this will load each 30 second segment, calculate the band powers on it, then store these in an output directory. 
You will then need to run RecombineMetrics.py to pull the output files together to create a single timeseries per subject. 

To use this code to calculate a custom metric:
1. First write a function to do the calculation. Use the bandpower_functions/calculate_bandpowers.py file as an template. Cleaning code from the bandpower_functions/ directory can be reused. 
2. Then update the CalculateMetrics.py file to use your new function instead of calculate_bandpowers.bandpower_process.
3. Update the config file to point to a new OUTPUT_DIR, BAD_CHANNELS_DIR, and have a new OUT_PREFIX to indicate a prefix for the files containing your metric.
4. Run CalculateMetrics.py, then RecombineMetrics.py. Your output timeseries should be stored in the location specified. 
