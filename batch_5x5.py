import yaml
import f90nml
import salishsea_cmd.api
import os
from copy import deepcopy
import time
import psutil
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def create_analysis_ipynb(template_file_path, dest_file_path, result_dir, var_name):
    result_dir_placeholder = "INSERT_RESULTS_DIRECTORY"
    var_name_placeholder = "INSERT_PARAM_NAME"
    with open(dest_file_path, 'w') as new_file:
        with open(template_file_path) as template_file:
            for line in template_file:
                new_file.write(line.replace(result_dir_placeholder, result_dir).replace(var_name_placeholder, var_name))

def run_notebook(notebook_filename):
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': '/ocean/jpetrie/MEOPAR/analysis-james/notebooks/'}})
    with open(notebook_filename, 'wt') as f:
        nbformat.write(nb, f)

reference_namelist_file = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/namelists/namelist_pisces_cfg_5x5_NewIC'

temp_namelist_dir = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/temp_namelist/'

reference_yaml = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/SMELT5x5test.yaml'

iodef_file ='/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/iofiles/iodef_bio_1hr.xml'

results_dir = '/data/jpetrie/MEOPAR/SalishSea/results/nampissink_june_8/'

analysis_dir = '/ocean/jpetrie/MEOPAR/analysis-james/notebooks/nampissink_june_8_analysis/'

reference_ipynb = '/ocean/jpetrie/MEOPAR/analysis-james/notebooks/parameter_analysis_template.ipynb'


if not os.path.exists(temp_namelist_dir):
    os.makedirs(temp_namelist_dir)

if not os.path.exists(analysis_dir):
    os.makedirs(analysis_dir)

reference_bio_params = f90nml.read(reference_namelist_file)

namelist_changes = []

section_name = 'nampissink'
scale_vals = [0.1, 0.5, 0.9, 1.1, 2, 10]
for var_name in reference_bio_params[section_name]:
    val = reference_bio_params[section_name][var_name]
    if val != 0:
        for scale_factor in scale_vals:
            namelist_changes.append({section_name: {var_name: val*scale_factor}})

reference_run_desc = yaml.load(open(reference_yaml, 'r'))

new_notebooks = []

for patch in namelist_changes:
    cpu_percent = psutil.cpu_percent()
    print(cpu_percent)
    while(cpu_percent > 44):
        print('wait until cpu load is lower')
        print(cpu_percent)
        time.sleep(10)
        cpu_percent = psutil.cpu_percent()

    mod_run_desc = deepcopy(reference_run_desc)
    mod_bio_params = deepcopy(reference_bio_params)
    run_identifier = str(patch).replace("{", "").replace("}", "").replace("'","").replace(" ", "").replace(":", "_")
    modified_nml_file = temp_namelist_dir + run_identifier

    last_underscore = run_identifier.rfind("_")
    patch_var_identifier = run_identifier[:last_underscore]
    if not os.path.exists(analysis_dir + patch_var_identifier):
        create_analysis_ipynb(reference_ipynb, analysis_dir + patch_var_identifier + '.ipynb', results_dir, patch_var_identifier)
        new_notebooks.append(analysis_dir + patch_var_identifier + '.ipynb')
    for key1 in patch:
        for key2 in patch[key1]:
            mod_bio_params[key1][key2] = patch[key1][key2]
    mod_bio_params.write(modified_nml_file)

# f90nml.patch(reference_namelist_file,patch, modified_nml_file)

    mod_run_desc['namelists']['namelist_pisces_cfg'][0] = modified_nml_file
    print(run_identifier)
    if not os.path.exists(results_dir + run_identifier) or os.listdir(results_dir + run_identifier) == []:
        salishsea_cmd.api.run_in_subprocess(run_identifier, mod_run_desc, results_dir + run_identifier)
        time.sleep(5)  # Just to make sure the job has fully started before checking cpu_percent again
    else:
        print("Result already exists: " + results_dir + run_identifier)
    os.remove(modified_nml_file)

for notebook_filename in new_notebooks:
    print("running " + notebook_filename)
    run_notebook(notebook_filename)
