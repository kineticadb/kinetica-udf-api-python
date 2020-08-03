import gpudb
import os
from util import test_environment as te
import argparse


def main(db_handle):
    proc_name = 'distributed_train'
    file_paths = ["dt_train.py", "../../kinetica_proc.py", "../../util/test_environment.py"]
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
    # Set up args
    parser = argparse.ArgumentParser(description='Register and execute the Python Distributed Model Training UDF example.')
    parser.add_argument('--host', default='127.0.0.1', help='Kinetica host to run example against')
    parser.add_argument('--username', default='', help='Username of user to run example with')
    parser.add_argument('--password', default='', help='Password of user')

    args = parser.parse_args()
    main(gpudb.GPUdb(host=['http://' + args.host + ':9191'], username=args.username, password=args.password))
