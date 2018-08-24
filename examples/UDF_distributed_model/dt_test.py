from kinetica_proc import ProcData
import pickle
import test_environment as te
from sklearn.metrics import accuracy_score
import numpy as np


"""
    This is a distributed UDF that combines predictions of multiple models in an ensemble.
    There will be one instance of this UDF running, per rank per tom. If you only have one rank, you may want to 
    increase the property ranks_per_tom to something greater than 1 (e.g. 8), in gpudb.conf.
    An instance of this UDF loads all models into memory and executes all models against the inference data that is 
    local to on their rank and tom. The prediction results of all models on one inference record are then combined.
"""


proc_data = ProcData()

"""Output rank & tom information"""
rank_number = proc_data.request_info['rank_number']
tom_number = proc_data.request_info['tom_number']
print('\nUDF test r{}_t{}: instantiated.'.format(rank_number, tom_number))

"""Load test data - NOTE: same data prep steps required as in dt_train.py!"""
test_data = proc_data.to_df().dropna()
num_test_data = test_data.shape[0]
X = test_data[['loan_amnt', 'int_rate', 'emp_length', 'annual_inc', 'dti', 'delinq_2yrs', 'revol_util', 'total_acc',
               'longest_credit_length']]
y_actual = test_data[['bad_loan']]
record_ids = test_data[['record_id']]

"""Get output table information"""
out_table = proc_data.output_data[0]
out_table.size = num_test_data
record_id_column, y_actual_column, y_predicted_column = out_table[0], out_table[1], out_table[2]

"""Execute all models against test data"""
print('UDF test r{}_t{}: execute all models on {} test data points.'.format(rank_number, tom_number, num_test_data))
if num_test_data > 0:
    models_from_db = te.load_ensemble_models('sklearn_dt')
    sum_predictions = np.full(num_test_data, 0.)
    accuracies = list()
    for current_model_dict in models_from_db:
        model = pickle.loads(current_model_dict['model'])
        y_test_predict = model.predict(X.values)
        test_accuracy = accuracy_score(y_actual, y_test_predict)
        accuracies.append(test_accuracy)
        sum_predictions += y_test_predict
    # compute combined predictions
    combined_predictions = np.around(sum_predictions / len(models_from_db))
    combined_accuracy = accuracy_score(y_actual, combined_predictions)
    print('Average accuracies of {} models: {}'.format(len(accuracies), (sum(accuracies) / float(len(accuracies)))))
    print('Ensemble accuracy: {}'.format(combined_accuracy))
    record_id_column[:] = record_ids.values
    y_actual_column[:] = y_actual.values
    y_predicted_column[:] = combined_predictions
    print('\n')
else:
    print('UDF test r{}_t{}: no test data on tom.\n'.format(rank_number, tom_number))

proc_data.complete()



