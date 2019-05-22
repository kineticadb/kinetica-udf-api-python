# Setup Environment And Run Examples #
This document describes how to setup your environment to be able to run example code that involve *PyGDF* and *H2O* libraries interacting with the *Kinetica* *Python* API and the *Kinetica Python UDF* API. For more information on these examples as well as tutorials and how UDFs work, refer to the [Kinetica documentation site](https://www.kinetica.com/docs/udf/index.html).

**Note:** Current restrictions of *PyGDF* include:
* *PyGDF* does not run on MacOS
* *PyGDF* requires *Python 3* (*Python 2* not supported)
* *PyGDF* officially only runs inside a Conda environment (`pip install` works but *PyGDF* code fails at runtime)

**Important:** *H2O* must be installed on all *Kinetica* cluster nodes for the UDFs that utilize *H2O* libraries to run successfully.


## Install Conda ##
Visit the [Conda website](https://conda.io/miniconda.html) and download the respective *Miniconda* installer for *Python 3*, e.g.,:
```
  wget "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"
```

Then run the installer:
```
  bash Miniconda3-latest-Linux-x86_64.sh
```


## Install H2O ##
Install *H2O* dependencies on all nodes:
```
  /opt/gpudb/bin/gpudb_pip install requests
  /opt/gpudb/bin/gpudb_pip install tabulate
  /opt/gpudb/bin/gpudb_pip install "colorama>=0.3.8"
  /opt/gpudb/bin/gpudb_pip install future
```
Install the *H2O Python* module on all nodes:
```
  /opt/gpudb/bin/gpudb_pip install -f http://h2o-release.s3.amazonaws.com/h2o/latest_stable_Py.html h2o
```


## Prepare Environment ##
**Note:** For additional reference, see the *PyGDF* [README](https://github.com/gpuopenanalytics/pygdf/blob/master/README.md)

Move into the root folder of this project (`cd kinetica-udf-api-python/`). Create a Conda environment that contains all dependencies required for *PyGDF* using the included `.yml` file:
```
  conda env create --name proc_data_dev --file conda_env_py3.yml
```
Then activate the Conda environment:
```
  source activate proc_data_dev
```
Install *PyGDF*:
```
  conda install -c numba -c conda-forge -c gpuopenanalytics/label/dev -c defaults pygdf=0.1.0a2
```
Install the *Kinetica Python* API where *n* is the desired [version from PyPI](https://pypi.org/project/gpudb/#history):
```
  pip install gpudb==6.2.0.n
```
Add the *Kinetica Python UDF* API repo's root directory to the PYTHONPATH:
```
export PYTHONPATH=$(pwd):$PYTHONPATH
```
Point the settings in `test_environment.py` (located in the `kinetica-udf-api-python/util/` directory) to your *Kinetica* instance. Either update the user and password default values as desired or configure a user `testuser` in *Kinetica*. Note that the the example code will create tables with test data.


## Run Examples ##
These examples are UDF implementations that will actually deploy to a *Kinetica* instance. Change into one of the example directories listed, and use the instructions included in the respective README to get started.

* `kinetica-udf-api-python/examples/UDF_distributed_model` -- builds multiple models based on distributed data and combines them into an ensemble
* `kinetica-udf-api-python/examples/UDF_h2o_glm` -- builds a generalized linear model (GLM) using the *H2O* libraries
* `kinetica-udf-api-python/examples/UDF_h2o_rf` -- builds a random forest model using the *H2O* libraries
* `kinetica-udf-api-python/examples/UDF_pandas` -- creates a *pandas* dataframe and inserts it into a table in *Kinetica*


### Standalone via UDF-simulator ###
The following example can be run (and debugged) without actually having to deploy a UDF to Kinetica. Instead the UDF Simulator (located in the `kinetica-udf-api-python/util/` directory) is used. Move into the `kinetica-udf-api-python/examples/` directory and run:
```
  python h2o_glm.py
```

## UDF Tutorial
A *Kinetica Python UDF* tutorial that outlines a sample workflow for developing, testing, and running UDFs is available in the [Kinetica UDF documentation](https://www.kinetica.com/docs/udf/python/tutorial.html). There's also a corresponding [GitHub repo](https://github.com/kineticadb/kinetica-tutorial-python-udf-api) that you can clone and try out for yourself.  
