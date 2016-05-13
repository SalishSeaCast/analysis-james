import yaml
import f90nml
import salishsea_cmd.api
import os
from copy import deepcopy


namelist_changes = [{'nampismezo': {'zz_rate_mesozoo_alpha': 0}},
                    {'nampismezo': {'zz_rate_mesozoo_alpha': 0.5}},
                    {'nampismezo': {'zz_rate_mesozoo_alpha': 1}}]

reference_namelist_file = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/namelists/namelist_pisces_cfg_5x5_NewIC'

modified_namelist_dir = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/namelists_alpha_30_day/'

reference_yaml = '/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/jpetrie/SMELT5x5test.yaml'

iodef_file ='/data/jpetrie/MEOPAR/SS-run-sets/SS-SMELT/iofiles/iodef_bio_1hr.xml'

results_dir = '/data/jpetrie/MEOPAR/SalishSea/results/mesozoo_alpha_changes_30_day/'

stream = open(reference_yaml, 'r')
reference_run_desc = yaml.load(stream)

if not os.path.exists(modified_namelist_dir):
    os.makedirs(modified_namelist_dir)

for patch in namelist_changes:
    mod_run_desc = deepcopy(reference_run_desc)
    run_identifier = str(patch).replace("{", "").replace("}", "").replace("'","").replace(" ", "").replace(":", "_")
    modified_nml_file = modified_namelist_dir + run_identifier
    f90nml.patch(reference_namelist_file,patch, modified_nml_file)
    mod_run_desc['namelists']['namelist_pisces_cfg'][0] = modified_nml_file
    print(run_identifier)
    salishsea_cmd.api.run_in_subprocess(run_identifier,mod_run_desc,iodef_file,results_dir + run_identifier)