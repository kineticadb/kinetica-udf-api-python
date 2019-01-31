from kinetica_proc import ProcData

"""Copies the data from input_data to output_data.
    Refer to the official documentation: https://www.kinetica.com/docs/udf/example_table_copy.html
"""


proc_data = ProcData()

for in_table, out_table in zip(proc_data.input_data, proc_data.output_data):
    out_table.size = in_table.size

    for in_column, out_column in zip(in_table, out_table):
        out_column.extend(in_column)

proc_data.results.update(proc_data.params)
proc_data.bin_results.update(proc_data.bin_params)

proc_data.complete()
