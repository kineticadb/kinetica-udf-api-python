from kinetica_proc import ProcData

proc_data = ProcData()

# Loop through input and output tables (assume the same number)
for in_table, out_table in zip(proc_data.input_data, proc_data.output_data):
    out_table.size = in_table.size

    # Loop through columns in the input and output tables (assume the same number and types)
    for in_column, out_column in zip(in_table, out_table):
        out_column.extend(in_column)

# Copy any parameters from the input parameter map into the output results map (not necessary for table copying, just for illustrative purposes)
proc_data.results.update(proc_data.params)
proc_data.bin_results.update(proc_data.bin_params)

# Inform Kinetica that the proc has finished successfully
proc_data.complete()
