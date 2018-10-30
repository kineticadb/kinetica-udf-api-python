# Run Distributed Model Ensemble Example #
This example demonstrates how to build a distributed model and combine the predictions in an ensemble.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the
necessary Python packages.

Run the data ingestion script from within this folder to setup the table for this example:
```
  python setup_table.py
```

Then you're ready to run the scripts that register and execute `dt_train.py` and `dt_test.py` as two separate, distributed
UDFs (modify Kinetica instance IP and port accordingly):

```
 python register_execute_train.py
 python register_execute_test.py
```
You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
```
The log shows accuracy statistics of the ensemble.

The models and combined inference results are located in tables `ensemble_models` and `example_loan_inference_result`.

## Additional Documentation ##
Visit the [corresponding page in the Kinetica documentation](https://kinetica.com/docs/udf/python/examples/github_examples/dist_model/dist_model.html) for more information.
