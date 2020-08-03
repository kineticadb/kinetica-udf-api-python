## Run Distributed Model Ensemble Example ##
This example demonstrates how to build a distributed model and combine the predictions in an ensemble.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the 
necessary Python packages.


Run the data ingestion (from within this folder under /examples/UDF_distributed_model/) to setup the table 
for this example:
```
  python setup_db.py
```

Then you're ready to run the scripts that register and execute dt_train.py and dt_test as two separate, distributed 
UDFs (supply Kinetica host, user, and password as necessary):

```
 python register_execute_train.py [--host <kinetica-host> [--username <kinetica-user> --password <kinetica-pass>]]
 python register_execute_test.py [--host <kinetica-host> [--username <kinetica-user> --password <kinetica-pass>]]
```
You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
``` 
The log shows accuracy statistics of the ensemble.

The models and combined inference results are located in tables 'ensemble_models' and 'example_loan_inference_result'.