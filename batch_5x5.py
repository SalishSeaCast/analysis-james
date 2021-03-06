# This script creates a set of changes from the default parameter values
# and runs the model once for each change set. Model runs are done in parallel
# and cpu usage is monitored so as not to exceed a preset threshold.

import yaml
import f90nml
import salishsea_cmd.api
import os
from copy import deepcopy
import time
import psutil
from numbers import Number

# Make sure CPU usage doesn't exceed a threshold.
# Stays in function until CPU usage drops below value
def wait_until_cpu_avail(max_usage = 47):
    cpu_percent = psutil.cpu_percent()
    print(cpu_percent)
    while(cpu_percent > max_usage):
        print('wait until cpu load is lower')
        print(cpu_percent)
        time.sleep(10)
        cpu_percent = psutil.cpu_percent()

reference_namelist_file = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/namelists/namelist_pisces_cfg_5x5_NewIC'
temp_namelist_dir = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/temp_namelist/'
reference_yaml = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/SMELT5x5test.yaml'
#Change this to the directory where results should go
results_dir = '/data/jpetrie/MEOPAR/SalishSea/results/all_params_AprIC_june_22/'

reference_bio_params = f90nml.read(reference_namelist_file)
reference_run_desc = yaml.load(open(reference_yaml, 'r'))

section_names = list(reference_bio_params.keys())
namelist_changes = [] #List of the patches
scale_vals = [0.1, 0.5, 0.9, 1.1, 2, 10]

# Iterate through parameters, select applicable ones and make a patch
# with each scale value.
# Each patch is a python dict specifying changes from the reference namelist
for section_name in section_names:
    for param_name in reference_bio_params[section_name]:
        val = reference_bio_params[section_name][param_name]
        # Don't change values that are already 0
        # Also avoid frac_waste params for now because they are coupled
        if val != 0 and "zz_frac_waste" not in param_name: 
            if type(val) is list:
                # If it is a list just modify the first value and leave the rest the same
                for scale_factor in scale_vals:
                    namelist_changes.append({section_name: {param_name: [val[0]*scale_factor] + val[1:]}})
            elif isinstance(val, Number):
                for scale_factor in scale_vals:
                    namelist_changes.append({section_name: {param_name: val*scale_factor}})

# Run the model for every patch and store results
# in a descriptive directory
for patch in namelist_changes:
    wait_until_cpu_avail()
    mod_run_desc = deepcopy(reference_run_desc)
    mod_bio_params = deepcopy(reference_bio_params)

    for section_name in patch:
        for param_name in patch[section_name]:
            val = patch[section_name][param_name]
            mod_bio_params[section_name][param_name] = val
            if type(val) is list:
                run_identifier = section_name + "_" + param_name + "_" + str(val[0])
            else:
                run_identifier = section_name + "_" + param_name + "_" + str(val)
    modified_nml_file = temp_namelist_dir + "/" + run_identifier
    mod_bio_params.write(modified_nml_file)

    mod_run_desc['namelists']['namelist_pisces_cfg'][0] = modified_nml_file
    print(run_identifier)
    
    # Make sure this result doesn't already exist
    if not os.path.exists(results_dir + "/" + run_identifier) or os.listdir(results_dir + "/" + run_identifier) == []:
        salishsea_cmd.api.run_in_subprocess(run_identifier, mod_run_desc, results_dir + "/" + run_identifier)
        time.sleep(5)  # Just to make sure the job has fully started before checking cpu_percent again
    else:
        print("Result already exists: " + results_dir + run_identifier)
    os.remove(modified_nml_file)
