from kinetica_proc import ProcData
import pandas as pd

"""
    This UDF outputs the content of a Pandas data frame into a Kinetica table. Its purpose is to demonstrate the
    proc_data.from_df(...) mechanism.
"""

proc_data = ProcData()

"""Output rank & tom information"""
rank_number = proc_data.request_info['rank_number']
tom_number = proc_data.request_info['tom_number']
print('\nUDF pandas proc output test r{}_t{}: instantiated.'.format(rank_number, tom_number))

"""write dataframe to table"""
data = {'id': pd.Series([1, 12, 123]), 'value_long': pd.Series([2, 23, 24]), 'value_float': pd.Series([0.2, 2.3, 2.34])}
df = pd.DataFrame(data)
output_table = proc_data.output_data[0]
output_table.size = df.shape[0]
proc_data.from_df(df, output_table)


proc_data.complete()
