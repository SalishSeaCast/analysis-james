import yaml
import f90nml
import salishsea_cmd.api
import os
from copy import deepcopy
import numpy as np
import time
import psutil

namelist_changes = []
#zz_remin_D_DON  =  2.3e-6
#for param_scale in (10**(np.array(range(-20,0,2))/10)).tolist():
#    namelist_changes.append({'nampisrem':{'zz_remin_D_DON':(2.3*10**(-6))*param_scale}})
#    namelist_changes.append({'nampisrem':{'zz_remin_D_PON':(2.3*10**(-6))*param_scale}})
#    namelist_changes.append({'nampisrem':{'zz_remin_D_bSi':(3.24*10**(-6))*param_scale}})
#    namelist_changes.append({'nampisrem':{'zz_remin_NH':(4*10**(-7))*param_scale}})






reference_namelist_file = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/namelists/namelist_pisces_cfg_5x5_NewIC'

modified_namelist_dir = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/param/'

reference_yaml = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/SMELT5x5test.yaml'

iodef_file ='/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/iofiles/iodef_bio_1hr.xml'

results_dir = '/data/jpetrie/MEOPAR/SalishSea/results/param_search/'


reference_bio_params = f90nml.read(reference_namelist_file)

scale_vals = [0.1,0.5,0.9,1.1,2,10]
for var_name in reference_bio_params['nampissink']:
    val = reference_bio_params['nampissink'][var_name]
    if val != 0:
        for scale_factor in scale_vals:
            namelist_changes.append({"nampissink":{var_name: val*scale_factor}})

#scale_vals = [0.1,0.5,0.9,1.1,2,10]
#for var_name in reference_bio_params['nampisprod']:
#    val = reference_bio_params['nampisprod'][var_name]
#    if val != 0:
#        for scale_factor in scale_vals:
#            namelist_changes.append({"nampisprod":{var_name: val*scale_factor}})

stream = open(reference_yaml, 'r')
reference_run_desc = yaml.load(stream)

if not os.path.exists(modified_namelist_dir):
    os.makedirs(modified_namelist_dir)

# salishsea_cmd.api.run_in_subprocess("test",reference_run_desc,results_dir)

for patch in namelist_changes:
    cpu_percent = psutil.cpu_percent()
    print(cpu_percent)
    while(cpu_percent > 46):
        print('wait until cpu load is lower')
        print(cpu_percent)
        time.sleep(10)
        cpu_percent = psutil.cpu_percent()

    mod_run_desc = deepcopy(reference_run_desc)
    run_identifier = str(patch).replace("{", "").replace("}", "").replace("'","").replace(" ", "").replace(":", "_")
    modified_nml_file = modified_namelist_dir + run_identifier
    f90nml.patch(reference_namelist_file,patch, modified_nml_file)
    mod_run_desc['namelists']['namelist_pisces_cfg'][0] = modified_nml_file
    print(run_identifier)
    if not os.path.exists(results_dir + run_identifier) or os.listdir(results_dir + run_identifier) == []:
        salishsea_cmd.api.run_in_subprocess(run_identifier,mod_run_desc,results_dir + run_identifier)
        time.sleep(5) # Just to make sure the job has fully started before checking cpu_percent again
    else:
       print("Result already exists: " + results_dir + run_identifier)
