# Kinetica UDF Python API #
This document describes how to use the Kinetica UDF Python API.

## UDF Reference Documentation ##
For information about UDFs in Kinetica, please see the Concepts/User Defined Functions section of the Kinetica documentation (http://www.kinetica.com/docs/concepts/index.html#user-defined-functions).

## Installing Proc Dependencies ##
Note that the UDF API is pre-loaded in the provided Kinetica Python environment.  However, any dependencies of the procs themselves must be installed on *all* of the machines in the Kinetica cluster if running UDFs in distributed mode, as each rank will run procs locally.

### Installing Python Modules with gpudb_pip.sh ###
Kinetica provides pip preinstalled in our python environment and also the "gpudb-pip.sh" script which can be used automate running pip on all machines in the Kinetica cluster.  It should be run as the gpudb user on the head node of the cluster and will ensure that any dependent modules are available on all machines.  This method is preferred if you have internet connectivity and the module is available on PyPI.  The following example demonstrates installing the "simplejson" module:

  ```
  /opt/gpudb/udf/api/python/gpudb-pip.sh install simplejson
  ```

### Installing Python Modules Using easy_install ###

If you cannot use pip (because the package is not available on PyPI, or there is no internet connectivity, then you can use easy_install instead.  In this instance, you should use the easy_install provided as part of the Kinetica installation by running the "gpudb_env.sh" command.  For example, this command can be run on all machines in the Kinetica cluster to install simplejson from a local tgz, rather than depending on an internet connection.

  ```
  /opt/gpudb/core/bin/gpudb_env.sh easy_install ./simplejson-3.10.0.tar.gz
  ```

## Using Packages Without Installing Them ##
Python does not require you to install packages in order to use dependent modules.  One method to get Python to find dependent modules is to use the PYTHONPATH environment variable.  As a convenience, Kinetica will add the /opt/gpudb/udf/thirdparty/lib/python2.7 path to the PYTHONPATH when executing procs.  If you have the same dependencies across the cluster and place the required files in the /opt/gpudb/udf/thirdparty/lib/python2.7 folder on the head node, you can use the /opt/gpudb/core/bin/gpudb_udf_distribute_thirdparty.sh script to copy those dependencies to all the nodes in the cluster.  Note that this will completely replace the contents of the /opt/gpudb/udf/thirdparty folder in all worker nodes of the cluster, but Kinetica will make a backup of the existing folder(s) before replacing them.

Alternate directories can be used as well, however you will likely have to edit the /opt/gpudb/core/bin/gpudb_execute_proc.sh script to add the path to the dependencies and you cannot use the gpudb_udf_distribute_thirdparty.sh script to copy the dependencies across the cluster.

## Using an Alternate Python Environment ##

If you require an alternate version of python than what Kinetica provides, you must install the UDF APIs in your python environment.  A setup.py is provided at /opt/gpudb/udf/api/python/setup.py which can be used with easy_install to add the UDF API to python.

  ```
  PATH=/path/to/your/python/environment/bin:$PATH easy_install /opt/gpudb/udf/api/python
  ```

You may also need to adjust the /opt/gpudb/core/bin/gpudb_execute_proc.sh script on all the machines in the Kinetica cluster to enable the required version of Python.  In this case, you should add any relevant paths to PATH, PYTHONPATH and PYTHONHOME after the call to gpudb_env.sh.

