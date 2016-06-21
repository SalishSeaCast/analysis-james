import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from os import listdir
import os
import sys
from threading import Thread

def create_notebook(reference_ipynb, dest_file_path, result_dir, var_name):
    result_dir_placeholder = "INSERT_RESULTS_DIRECTORY"
    var_name_placeholder = "INSERT_PARAM_NAME"
    with open(dest_file_path, 'w') as new_file:
        with open(reference_ipynb) as template_file:
            for line in template_file:
                new_file.write(line.replace(result_dir_placeholder, result_dir).replace(var_name_placeholder, var_name))


def run_notebook(notebook_filename):
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
    try:
        ep.preprocess(nb, {'metadata': {'path': '/ocean/jpetrie/MEOPAR/analysis-james/notebooks/'}})
        with open(notebook_filename, 'wt') as f:
            nbformat.write(nb, f)
    except:
        print(notebook_filename + " failed to run")


def create_and_run_notebooks(analysis_dir, result_dir, reference_ipynb):
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)

    var_names = set()
    for file_name in listdir(result_dir):
        last_underscore = file_name.rfind("_")
        var_name = file_name[:last_underscore]
        var_names.add(var_name)

    for var_name in var_names:
        print(var_name)
        notebook_file = analysis_dir + '/' + var_name + '.ipynb'
        create_notebook(reference_ipynb, notebook_file, result_dir, var_name)
        print("running " + var_name)
        run_notebook(notebook_file)

if __name__ == '__main__':
    analysis_dir = sys.argv[1]
    result_dir = sys.argv[2]
    if len(sys.argv) > 3:
        reference_ipynb = sys.argv[3]
    else:
        reference_ipynb = '/ocean/jpetrie/MEOPAR/analysis-james/notebooks/parameter_analysis_template.ipynb'
    print(analysis_dir)
    create_and_run_notebooks(analysis_dir, result_dir, reference_ipynb)
