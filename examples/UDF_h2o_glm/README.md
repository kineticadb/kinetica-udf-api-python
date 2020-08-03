## Run H2O GLM Example ##
This example demonstrates how to deploy and run a UDF that uses the H2O framework.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the 
necessary Python packages.

This demo uses the Kinetica File System (KiFS) for model storage. Follow the instructions in the 
documentation to make sure KiFS is setup and configured:  https://www.kinetica.com/docs/7.1/tools/kifs.html

Run the data ingestion (from within this folder under /examples/UDF_h2o_glm/) to setup the table for the UDF:
```
  python setup_table.py
```

Then you're ready to run the script that registers and executes H2O_train.py as an UDF (supply Kinetica host, user, and password as necessary):

```
 python register_execute_train.py [--host <kinetica-host> [--username <kinetica-user> --password <kinetica-pass>]]
```
You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
``` 
You are also able to observe the stored model in GAdmin under schema 'filesystem' in table '__kifs__GLM_model'. 

Alternatively, the UDF can also be run from a jupyter notebook UDF.ipynb. 