# Kinetica UDF Python API #
This document describes how to use the Kinetica UDF Python API.

The source code for this project can be found at 
https://github.com/kineticadb/kinetica-udf-api-python

## UDF Reference Documentation ##
For information about UDFs in Kinetica, please see the Concepts/User Defined 
Functions section of the Kinetica documentation 
(http://www.kinetica.com/docs/concepts/index.html#user-defined-functions).

## Installing the Kinetic UDF APIs for Python ##
Note that the UDF API must be installed on *all* of the machines in the Kinetica 
cluster if running UDFs in distributed mode, as each rank will run procs locally.

### Installing Python Modules with gpudb_pip.sh ###
Kinetica provides pip preinstalled in our python environment and also a 
"gpudb_pip.sh" script which will automate running pip on all machines in the 
Kinetica cluster.  It should be run as the gpudb user on the head node of the 
cluster and will ensure that any dependent modules are available on all 
machines.  This method is preferred if you have internet connectivity and the 
module is available on PyPI.  The following example demonstrates installing the 
"simplejson" module:

  ```
  /opt/gpudb/core/bin/gpudb_pip.sh install simplejson
  ```

### Installing Python Modules Using easy_install ###

If you cannot use pip (because the package is not available on PyPI, or there is
 no internet connectivity, then you can use easy_install instead.  In this 
 instance, you can use the 

If you require an alternate version of python, you can replace the path as 
needed, but you may also need to adjust the /opt/gpudb/core/bin/gpudb_execute_proc.sh 
script on all the machines in the Kinetica cluster to ensure that the required 
version of python is executed at runtime.

## Using the UDF API without installing ##
If you do not wish to install the API, or do not have permission, you can add 
the UDF API to your PYTHONPATH by editing the /opt/gpudb/core/bin/gpudb_execute_proc.sh 
script on each machine in the Kinetica cluster.  By default, the gpudb_execute_proc.sh 
script will add a PYTHONPATH of /opt/gpudb/udf/thirdparty/lib/python2.7.  You 
can place any dependencies there on the head node and run the 
gpudb_distribute_thirdparty.sh script to copy it to all worker nodes.  As a 
warning, this will replace the entire contents of that thirdparty directory 
with the contents on the head node, but it will also make a backup of the 
thirdparty folder and place it in the udf folder before overwriting.

