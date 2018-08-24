from kinetica_proc import ProcData
from sklearn import tree
import pickle
import test_environment as te
from sklearn.metrics import accuracy_score


"""
    This is a distributed UDF that trains and stores a decision tree model - one per TOM. Note that there will be 
    running one instance of a UDF per rank per tom. If you only have one rank, you may want to increase the
    property ranks_per_tom to something greater than 1 (e.g. 8), in gpudb.conf.
    Since each instance of this UDF only sees data local to their rank and tom, it is important that at ingest time
    this data was distributed randomly (uniform). This can be achieved by not using a shard key. Alternatively a 
    column could be introduced that contains a random number, as the shard key.
    The data used in this example is about loans with target feature 'bad_loan' that can have the values 0 and 1.
"""

proc_data = ProcData()

"""Output rank & tom information"""
rank_number = proc_data.request_info['rank_number']
tom_number = proc_data.request_info['tom_number']
print('\nUDF train r{}_t{}: instantiated.'.format(rank_number, tom_number))

"""Load and prepare training data"""
training_data = proc_data.to_df().dropna()  # only use non-NAN rows
num_input_data = training_data.shape[0]
X = training_data[['loan_amnt', 'int_rate', 'emp_length', 'annual_inc', 'dti', 'delinq_2yrs', 'revol_util', 'total_acc',
                   'longest_credit_length']]
y = training_data[['bad_loan']]

"""Train model"""
print('UDF train r{}_t{}: learning model on {} data points.'.format(rank_number, tom_number, num_input_data))
tree_classifier = tree.DecisionTreeClassifier(class_weight=None, criterion='entropy', max_depth=7, max_features=None,
                                              max_leaf_nodes=None, min_samples_leaf=5, min_samples_split=2,
                                              min_weight_fraction_leaf=0.0, presort=False, random_state=100,
                                              splitter='best')

"""Store model along with some meta information"""
if X.shape[0] > 10:
    model = tree_classifier.fit(X, y)
    # evaluate on train data
    acc = accuracy_score(y, model.predict(X))
    print('UDF train r{}_t{}: training accuracy: {}'.format(rank_number, tom_number, acc))
    # store model
    print('UDF train r{}_t{}: storing model.'.format(rank_number, tom_number))
    model_byte_array = pickle.dumps(model)
    te.store_ensemble_model(model_byte_array, 'sklearn_dt', rank_number, tom_number, num_input_data, acc)
    # TODO use KiFS for model storage
else:
    print('UDF train r{}_t{}: not enough training data: {} data points.\n'.format(rank_number, tom_number, X.shape[0]))

proc_data.complete()
