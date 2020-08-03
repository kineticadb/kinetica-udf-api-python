# Run UDF that outputs a Pandas data frame into a Kinetica table

This UDF tests the the output mechanism from Pandas data frame to an output table.

Follow the instructions in the examples home folder [README.md](../README.md) to setup your environment with the 
necessary Python packages.

For this example not data ingestion is necessary: the toy data frame will be instantiated inside the UDF itself, 
containing three columns with three rows of data. 

To run the example (supply Kinetica host, user, and password as necessary):
```
    python setup_db.py
    python register_execute_UDF.py [--host <kinetica-host> [--username <kinetica-user> --password <kinetica-pass>]]
```

You can monitor the UDF's log output under your logs directory:
```
    tail -f /opt/gpudb/core/logs/gpudb-proc.log
```

As a result you should be able to see a table "unittest_df_output" in Kinetica.