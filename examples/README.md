# Setup Environment And Run Examples #
This document describes how to setup your environment to be able to run example code
that involve the libraries pygdf, H2O, kinetica_proc and gpudb. 
Note current restrictions of pygdf: 
* does not run on MacOS
* requires Python 3 (Python 2 not supported)
* officially only runs inside a Conda environment (pip install works but pygdf code fails at runtime) 

## Install Conda ##
To install Conda visit https://conda.io/miniconda.html and download the respective 
installer for Python 3: 
```
  wget "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"
```

Then run the installer like:
```
  bash Miniconda3-latest-Linux-x86_64.sh
```

## Prepare Conda Environment ##
We need to prepare the Conda environment, for reference also see 
https://github.com/gpuopenanalytics/pygdf/blob/master/README.md

Move into the root folder of this project (.../gpudb-udf-api-python/). Create a Conda
environment that contains all dependencies required for pygdf, using the .yml file:
```
  conda env create --name proc_data_dev --file conda_env_py3.yml
```
Then activate the Conda environment:
```
  source activate proc_data_dev
```
Install pygdf:
```
  conda install -c numba -c conda-forge -c gpuopenanalytics/label/dev -c defaults pygdf=0.1.0a2
```
Also make sure to install gpudb:
```
  pip install gpudb
```

Then follow these instructions to install the latest version of H2O:
http://docs.h2o.ai/h2o/latest-stable/h2o-docs/downloading.html#install-in-python


## Prepare Database ##
Point the settings at test_environment.py (in project /util directory) to your Kinetica instance. 
A user "testuser" needs to be configured. Alternatively you can change the user name and password 
in that file. Note that the the example code will create tables with test data, and will
delete these after the examples have run. 

## Run Examples ##
Make sure to add the project home folder as content root to the PYTHONPATH:
```
  export PYTHONPATH=/<path-to-project>/gpudb-udf-api-python
```
### Standalone via UDF-simulator ###
These examples can be run (and debugged) without actually having to deploy a UDF to Kinetica. Instead
the UDF-simulator (located under the projects /util direcotry) is used. 
Move into the example folder of this project (/examples) and run any of them. Currently available are:
```
  python h2o_glm.py
```

### Deployable UDF examples ###
These examples are UDF implementations that will actually deploy to a Kinetica instance.
They are located in subdirectories /examples/UDF_* along with further instructions in a respective README file. 