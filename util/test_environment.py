import gpudb
import subprocess
import os
import glob
import pandas as pd
import collections
import sys
from datetime import datetime


""" All constants and functions provided here are to be used in examples and unit test implementations for the UDF API.
    It involves two features: test data ingestion (and deletion) to a table in an actual Kinetica instance and 
    initialization of a udf-simulator (and cleansing its artifacts) to avoid having to deploy actual UDFs just for 
    the purpose of examples or unit tests. Note that the udf-simulator requires the test data to be ingested, 
    which means the ingestion has to happen first. 
"""

# Adjust these constants to reflect your Kinetica installation that you can use for running examples and unit tests.
HOST = 'http://localhost'
PORT = '9191'
USER = 'testuser'
PASSWORD = 'Testuser123!'
DB_HANDLE = gpudb.GPUdb(encoding='BINARY', host=HOST, port=PORT)

# This is the test data that examples and unit tests will use. All data and tables will be deleted after the
# examples or unit tests have run.
TEST_DATA_TABLE_NAME_1 = 'unittest_toy_data'
TEST_DATA_TYPE_1 = [
    ['id', gpudb.GPUdbRecordColumn._ColumnType.INT],
    ['value_long', gpudb.GPUdbRecordColumn._ColumnType.LONG],
    ['value_float', gpudb.GPUdbRecordColumn._ColumnType.FLOAT]
]
TEST_DATA_RECORDS_1 = [
    [1, 123, 1.2],
    [2, 1234, 1.3],
    [3, 12345, 1.4],
    [4, 123456, 1.5],
    [5, 1234567, 1.6]
]
TEST_DATA_TABLE_NAME_2 = 'unittest_toy_data2'
TEST_DATA_TYPE_2 = [
    ['id', gpudb.GPUdbRecordColumn._ColumnType.INT],
    ['value_float', gpudb.GPUdbRecordColumn._ColumnType.FLOAT]
]
TEST_DATA_RECORDS_2 = [
    [6, 2.2],
    [7, 2.3],
    [8, 2.4],
    [9, 2.5],
    [10, 2.6]
]
TEST_OUTPUT_TABLE_NAME = 'unittest_df_output'

LOAN_TRAIN_DATA_TABLE_NAME = "example_loan_train_data"
LOAN_TEST_DATA_TABLE_NAME = "example_loan_test_data"
LOAN_INFERENCE_TABLE_NAME = "example_loan_inference_result"
LOAN_DATA_TYPE = """
    {
        "type": "record",
        "name": "loan_type",
        "fields": [
            {"name":"loan_amnt","type":"float"},
            {"name":"int_rate","type":"float"},
            {"name":"emp_length","type":"float"},
            {"name":"annual_inc","type":"float"},
            {"name":"dti","type":"float"},
            {"name":"delinq_2yrs","type":"float"},
            {"name":"revol_util","type":"float"},
            {"name":"total_acc","type":"float"},
            {"name":"bad_loan","type":"float"},
            {"name":"longest_credit_length","type":"float"},
            {"name":"record_id","type":"float"}
        ]
    }"""
LOAN_INFERENCE_TYPE = """
{
        "type": "record",
        "name": "loan_type",
        "fields": [
            {"name":"record_id","type":"float"},
            {"name":"bad_loan_actual","type":"float"},
            {"name":"bad_loan_predicted","type":"float"}
        ]
    }"""
MODEL_TABLE_NAME = "example_model_table"
MODEL_TABLE_TYPE = [
    ["model_id", gpudb.GPUdbRecordColumn._ColumnType.INT],
    ["model_name", gpudb.GPUdbRecordColumn._ColumnType.STRING],
    ["model_binary", gpudb.GPUdbRecordColumn._ColumnType.BYTES]
]
MODEL_TYPE_PROPERTIES = {"id": ["char64"], "date_time_created": ["datetime"]}

ENSEMBLE_MODEL_TABLE_NAME = "ensemble_models"
ENSEMBLE_MODEL_TYPE = MODEL_TYPE = """
    {
        "type": "record",
        "name": "ensemble_mode_type",
        "fields": [
            {"name":"model","type":"bytes"},
            {"name":"name","type":"string"},
            {"name":"rank","type":"int"},
            {"name":"tom","type":"int"},
            {"name":"num_input_data","type":"int"},
            {"name":"date_time_created","type":"string"}
        ]
    }"""
ENSEMBLE_MODEL_TYPE_PROPERTIES = {"date_time_created": ["datetime"]}

# Constants to control the udf simulator and its artifacts.
UDFSIM_PATH = '../util/udfsim.py'
UDFSIM_CONTROL_FILE_ENVIRON = 'KINETICA_PCF'
UDFSIM_FILES = './kinetica-udf-sim-*'  # files generated by udfsim.py at runtime


def ingest_test_data(table_name, table_type, table_records):
    """Ingest some test data to a table in Kinetica, to have it available for the examples or unit tests."""
    if DB_HANDLE.has_table(table_name=table_name)['table_exists']:
        DB_HANDLE.clear_table(table_name)
    test_data_table = gpudb.GPUdbTable(table_type, table_name, db=DB_HANDLE)
    test_data_table.insert_records(table_records)


def create_test_output_table(table_name, table_type):
    if DB_HANDLE.has_table(table_name=table_name)['table_exists']:
        DB_HANDLE.clear_table(table_name)
    test_data_table = gpudb.GPUdbTable(table_type, table_name, db=DB_HANDLE)


def delete_test_data(table_name):
    """Remove test data table from database"""
    if DB_HANDLE.has_table(table_name=table_name)['table_exists']:
        DB_HANDLE.clear_table(table_name)


def prepare_loan_data():
    if DB_HANDLE.has_table(table_name=LOAN_TRAIN_DATA_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(LOAN_TRAIN_DATA_TABLE_NAME)
    if DB_HANDLE.has_table(table_name=LOAN_TEST_DATA_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(LOAN_TEST_DATA_TABLE_NAME)
    if DB_HANDLE.has_table(table_name=LOAN_INFERENCE_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(LOAN_INFERENCE_TABLE_NAME)
    response = DB_HANDLE.create_type(type_definition=LOAN_DATA_TYPE, label=LOAN_TRAIN_DATA_TABLE_NAME)
    type_id = response['type_id']
    response = DB_HANDLE.create_table(table_name=LOAN_TRAIN_DATA_TABLE_NAME, type_id=type_id)
    print("Create loan train data table response status: {}".format(response['status_info']['status']))
    response = DB_HANDLE.create_table(table_name=LOAN_TEST_DATA_TABLE_NAME, type_id=type_id)
    print("Create loan test data table response status: {}".format(response['status_info']['status']))
    response = DB_HANDLE.create_type(type_definition=LOAN_INFERENCE_TYPE, label=LOAN_INFERENCE_TABLE_NAME)
    type_id = response['type_id']
    response = DB_HANDLE.create_table(table_name=LOAN_INFERENCE_TABLE_NAME, type_id=type_id)
    print("Create loan inference table response status: {}".format(response['status_info']['status']))
    pythonpath = os.environ['PYTHONPATH'].split(os.pathsep)[0]
    records = pd.read_csv(pythonpath + '/util/loan_sample.csv.zip', sep=',', quotechar='"').values
    print('Inserting loan data, this may take a few minutes.')
    encoded_obj_list_train = []
    encoded_obj_list_test = []
    i = 0
    for record in records:
        i += 1
        datum = collections.OrderedDict()
        datum['loan_amnt'] = float(record[0])
        datum['int_rate'] = float(record[1])
        datum['emp_length'] = float(record[2])
        datum['annual_inc'] = float(record[3])
        datum['dti'] = float(record[4])
        datum['delinq_2yrs'] = float(record[5])
        datum['revol_util'] = float(record[6])
        datum['total_acc'] = float(record[7])
        datum['bad_loan'] = float(record[8])
        datum['longest_credit_length'] = float(record[9])
        datum['record_id'] = float(i)
        if i % 10 == 0:
            encoded_obj_list_test.append(DB_HANDLE.encode_datum(LOAN_DATA_TYPE, datum))
        else:
            encoded_obj_list_train.append(DB_HANDLE.encode_datum(LOAN_DATA_TYPE, datum))
        if i % 1000 == 0:
            response = DB_HANDLE.insert_records(table_name=LOAN_TRAIN_DATA_TABLE_NAME, data=encoded_obj_list_train,
                                                list_encoding='binary', options={})
            if response['status_info']['status'] == "ERROR":
                print("Insert train response: {}".format(response))
            response = DB_HANDLE.insert_records(table_name=LOAN_TEST_DATA_TABLE_NAME, data=encoded_obj_list_test,
                                                list_encoding='binary', options={})
            if response['status_info']['status'] == "ERROR":
                print("Insert test response: {}".format(response))
            encoded_obj_list_train = []
            encoded_obj_list_test = []
            sys.stdout.write('.')
            sys.stdout.flush()
    response = DB_HANDLE.insert_records(table_name=LOAN_TRAIN_DATA_TABLE_NAME, data=encoded_obj_list_train,
                                        list_encoding='binary')
    if response['status_info']['status'] == "ERROR":
        print("Insert response: {}".format(response))
    response = DB_HANDLE.insert_records(table_name=LOAN_TEST_DATA_TABLE_NAME, data=encoded_obj_list_train,
                                        list_encoding='binary')
    if response['status_info']['status'] == "ERROR":
        print("Insert response: {}".format(response))
    print('\nAll data inserted.')


def delete_loan_data():
    """Remove loan data table from database"""
    if DB_HANDLE.has_table(table_name=LOAN_TRAIN_DATA_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(LOAN_TRAIN_DATA_TABLE_NAME)
    if DB_HANDLE.has_table(table_name=LOAN_TEST_DATA_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(LOAN_TEST_DATA_TABLE_NAME)


def create_model_table():
    """Create table to be able to store serialized models."""
    if DB_HANDLE.has_table(table_name=MODEL_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(MODEL_TABLE_NAME)
    gpudb.GPUdbTable(MODEL_TABLE_TYPE, MODEL_TABLE_NAME, db=DB_HANDLE)


def create_ensemble_model_table():
    if DB_HANDLE.has_table(table_name=ENSEMBLE_MODEL_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(ENSEMBLE_MODEL_TABLE_NAME)
    response = DB_HANDLE.create_type(type_definition=ENSEMBLE_MODEL_TYPE, label=ENSEMBLE_MODEL_TABLE_NAME,
                                     properties=ENSEMBLE_MODEL_TYPE_PROPERTIES)
    response = DB_HANDLE.create_table(table_name=ENSEMBLE_MODEL_TABLE_NAME, type_id=response['type_id'])
    print("Create model_table response status: {}".format(response['status_info']['status']))


def delete_model_table():
    """Remove model table from database"""
    if DB_HANDLE.has_table(table_name=MODEL_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(MODEL_TABLE_NAME)


def delete_ensemble_model_table():
    """Remove model table from database"""
    if DB_HANDLE.has_table(table_name=ENSEMBLE_MODEL_TABLE_NAME)['table_exists']:
        DB_HANDLE.clear_table(ENSEMBLE_MODEL_TABLE_NAME)


def store_model(model_id, model_name, model_binary):
    """Store serialized model object into table"""
    encoded_object_list = []
    datum = collections.OrderedDict()
    datum[MODEL_TABLE_TYPE[0][0]] = int(model_id)
    datum[MODEL_TABLE_TYPE[1][0]] = str(model_name)
    datum[MODEL_TABLE_TYPE[2][0]] = model_binary
    table_type = gpudb.GPUdbRecordType(MODEL_TABLE_TYPE).schema_string
    encoded_object_list.append(DB_HANDLE.encode_datum(table_type, datum))
    response = DB_HANDLE.insert_records(table_name=MODEL_TABLE_NAME, data=encoded_object_list, list_encoding='binary')
    print(response)


def store_ensemble_model(model_binary, name, rank, tom, num_input_data, train_acc):
    """Store serialized model object into table"""
    encoded_object_list = []
    datum = collections.OrderedDict()
    datum['model'] = model_binary
    datum['name'] = str(name)
    datum['rank'] = int(rank)
    datum['tom'] = int(tom)
    datum['num_input_data'] = int(num_input_data)

    datum['date_time_created'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    encoded_object_list.append(DB_HANDLE.encode_datum(ENSEMBLE_MODEL_TYPE, datum))
    response = DB_HANDLE.insert_records(table_name=ENSEMBLE_MODEL_TABLE_NAME, data=encoded_object_list,
                                        list_encoding='binary')
    print(response)


def load_model(model_id):
    """Load serialized model object from table"""
    response = DB_HANDLE.get_records(table_name=MODEL_TABLE_NAME, offset=0, limit=1,
                                     options={"expression": "model_id="+str(model_id)})
    res_decoded = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
    model_binary = res_decoded[0]['model_binary']
    return model_binary


def load_ensemble_models(name, limit=100):
    """Load serialized ensemble model objects that share the same name from table."""
    response = DB_HANDLE.get_records(table_name=ENSEMBLE_MODEL_TABLE_NAME, offset=0, limit=limit,
                                     options={"expression": "(name='" + str(name) + "')"})
    res_decoded = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
    result_dict_list = []
    for current_result in res_decoded:
        current_dict = dict()
        current_dict['model'] = current_result['model']
        current_dict['num_input_data'] = current_result['num_input_data']
        current_dict['rank'] = current_result['rank']
        current_dict['tom'] = current_result['tom']
        current_dict['date_time_created'] = current_result['date_time_created']
        result_dict_list.append(current_dict)
    return result_dict_list


def init_udfsim(test_data_table_names, output_tables=None):
    """ Runs the udf-simulator (udfsim.py). The simulator creates a control file, which is pointed to via
        an environment variable. All of this is required for ProcData() to work, which is used in all examples or
        unit tests. The simulator is used since the real-world situation of deploying actual UDFs to Kinetica
        is neither practical nor reasonable just for the purpose of udf-api unit tests.
    """
    print('Initializing UDF simulator...')
    udfsim_parameters = ["python", UDFSIM_PATH, "execute", "-K", HOST + ":" + PORT, "-U", USER, "-P", PASSWORD]
    print('udfsim parameters: {}'.format(udfsim_parameters))
    for table_name in test_data_table_names:
        udfsim_parameters.append("-i")
        udfsim_parameters.append(table_name)
    if output_tables:
        for table_name in output_tables:
            udfsim_parameters.append("-o")
            udfsim_parameters.append(table_name)
    (out, err) = subprocess.Popen(udfsim_parameters, stdout=subprocess.PIPE).communicate()
    if err:
        print('udfsim execute error: {}\n'.format(err))
    environ = [s for s in out.decode().split('\n') if UDFSIM_CONTROL_FILE_ENVIRON in s][0].split('=')[-1]
    os.environ[UDFSIM_CONTROL_FILE_ENVIRON] = environ


def output_udfsim_result():
    """ If init_udfsim was triggered with output tables then this method can be used to trigger writing result data to
        these tables.
    """
    print('Writing output from UDF simulator to table...')
    udfsim_parameters = ["python", UDFSIM_PATH, "output", "-K", HOST + ":" + PORT, "-U", USER, "-P", PASSWORD]
    (out, err) = subprocess.Popen(udfsim_parameters, stdout=subprocess.PIPE).communicate()
    if err:
        print('udfsim output error: {}'.format(err))


def load_result_data(table_name, limit=1):
    """Load serialized model object from table"""
    response = DB_HANDLE.get_records(table_name=table_name, offset=0, limit=limit, options={})
    records = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
    return records


def delete_udfsim_artifacts():
    """Delete any artifacts generated by the udf-simulator."""
    for filename in glob.glob(UDFSIM_FILES):
        os.remove(filename)
