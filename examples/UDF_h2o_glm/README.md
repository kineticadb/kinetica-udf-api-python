# Run H2O GLM Example #
This example demonstrates how to deploy and run a UDF that uses the H2O framework.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the
necessary Python packages.

This demo uses the *Kinetica File System* (*KiFS*) for model storage. Follow the instructions in the [documentation](https://www.kinetica.com/docs/tools/kifs.html) to make sure *KiFS* is setup and configured.

Run the data ingestion script from within this folder to setup the table for the UDF:
```
  python setup_table.py
```

Run the script that registers and executes `h2o_glm_train.py` as an UDF (modify *Kinetica* instance IP and port accordingly):

```
 python register_execute_train.py
```
You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
```
You are also able to observe the stored model in the *KiFS* browser in *GAdmin* under the `GLM_model` directory.

Alternatively, the UDF can also be run from a jupyter notebook UDF.ipynb.

## Additional Documentation ##
Visit the [corresponding page in the Kinetica documentation](https://kinetica.com/docs/udf/python/examples/github_examples/h2o_glm/h2o_glm.html) for more information.
