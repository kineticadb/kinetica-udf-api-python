# Run H2O Random Forest Example #
This example demonstrates how to deploy and run a UDF that uses the *H2O* framework for model training and inference and uses the *Kinetica File System* (*KiFS*) for model storage.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the
necessary Python packages.

Follow the instructions in the [documentation](https://www.kinetica.com/docs/tools/kifs.html) to make sure *KiFS* is setup and configured.

Run the data ingestion script from within this folder to setup the table for the UDF:
```
  python setup_table.py
```

Run the script that registers and executes `h2o_rf_train_test.py` as a UDF (modify *Kinetica* instance IP and port accordingly):

```
 python register_execute_train_test.py
```
You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
```
You are also able to observe the stored model in the *KiFS* browser in *GAdmin* under the `RF_model` directory.

## Additional Documentation ##
Visit the [corresponding page in the Kinetica documentation](https://kinetica.com/docs/udf/python/examples/github_examples/h2o_rf/h2o_rf.html) for more information.
