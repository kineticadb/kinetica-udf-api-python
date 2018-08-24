import gpudb
import os
from util import test_environment as te

HOST_IP = "127.0.0.1"


def main(db_handle):
    proc_name = 'H2o_rf_train_test'
    file_paths = ["h2o_rf_train_test.py", "../../kinetica_proc.py"]  # put the main python script in the first place
    # Read proc code in as bytes and add to a file data array
    files = {}
    for script_path in file_paths:
        script_name = os.path.basename(script_path)
        with open(script_path, 'rb') as f:
            files[script_name] = f.read()
    # Remove proc if it exists from a prior registration
    if db_handle.has_proc(proc_name)['proc_exists']:
        db_handle.delete_proc(proc_name)
    print("Registering proc...")
    response = db_handle.create_proc(proc_name, 'distributed', files, 'python', [file_paths[0]], {})
    print(response)
    print("Executing proc...")
    response = db_handle.execute_proc(proc_name, {}, {}, [te.LOAN_TRAIN_DATA_TABLE_NAME], {}, [], {})
    print(response)


if __name__ == "__main__":
    main(gpudb.GPUdb(encoding='BINARY', host=HOST_IP, port='9191'))
