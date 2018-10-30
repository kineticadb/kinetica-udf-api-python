# Kinetica UDF Python API #
This document describes how to use the Kinetica UDF Python API.

The source code for this project can be found at
https://github.com/kineticadb/kinetica-udf-api-python

## UDF Reference Documentation ##
For information about UDFs in Kinetica, please see the User-Defined Functions
section of the Kinetica documentation
(https://www.kinetica.com/docs/concepts/udf.html).

## Installing the Kinetica UDF APIs for Python ##
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
  /opt/gpudb/udf/api/python/gpudb-pip.sh install simplejson
  ```

### Installing Python Modules Using easy_install ###

If you cannot use pip (because the package is not available on PyPI, or there is
no internet connectivity, then you can use easy_install instead.  In this
instance, you can place the whell or tgz file into the /opt/gpudb/thirdparty
folder on the head node and use the
/opt/gpudb/core/bin/gpudb_hosts_rsync_to.sh command to copy just the one file
to all hosts.  Then use the /opt/gpudb/core/bin/gpudb_hosts_ssh_execute.sh
command combined with the /opt/gpudb/core/bin/gpudb_env.sh command to install
the module.

  ```
  # Assumes that you have already downloaded the python module to the head
  # node of the cluster, and it is in the current folder and named
  # 'python-module.tgz'
  /opt/gpudb/core/bin/gpudb_hosts_rsync_to.sh python-module.tgz /tmp/python-module.tgz
  /opt/gpudb/core/bin/gpudb_hosts_ssh_execute.sh /opt/gpudb/core/bin/gpudb_env.sh easy_install /tmp/python-module.tgz
  ```

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

## Apache Arrow ##

The Kinetica Python UDF API supports Apache Arrow natively. A few examples
that demonstrate using Apache Arrow with Kinetica are available:

* [UDF Distributed Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_distributed_model)
* [UDF H2O Generalized Linear Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_h2o_glm)
* [UDF H2O Random Forest Model](https://github.com/kineticadb/kinetica-udf-api-python/tree/master/examples/UDF_h2o_rf)
