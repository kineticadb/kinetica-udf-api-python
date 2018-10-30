# Run UDF that outputs a Pandas data frame into a Kinetica table #

This UDF tests the the output mechanism from *Pandas* data frame to an output table.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the necessary Python packages.

For this example, no data ingestion is necessary; the toy data frame containing three columns with three rows of data will be instantiated inside the UDF itself.

To run the example:
```
    python setup_db.py
    python register_execute_UDF.py
```

You can monitor the UDF's log output under your logs directory:
```
 tail -f /opt/gpudb/core/logs/gpudb-proc.log
```

As a result you should be able to see a table `unittest_df_output` in *Kinetica*.

## Additional Documentation ##
Visit the [corresponding page in the Kinetica documentation](https://kinetica.com/docs/udf/python/examples/github_examples/pandas/pandas.html) for more information.
