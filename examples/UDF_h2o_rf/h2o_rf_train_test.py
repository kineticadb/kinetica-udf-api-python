from kinetica_proc import ProcData
import h2o
from h2o.estimators.random_forest import H2ORandomForestEstimator

"""
    This is a demonstration of how to use H2O for model learning and inference in a distributed Kinetica UDF. 
    The demo is based on this H2O tutorial:
    https://github.com/h2oai/h2o-tutorials/blob/master/h2o-open-tour-2016/chicago/intro-to-h2o.ipynb

    This demonstration assumes the situation where the data is large and learning a single model on all data is not
    feasible (e.g. due to memory constraints). A possible approach to address this challenge is to learn multiple 
    models, each on a fraction of the data, and then to combine their inference output (e.g. by averaging).
    In this demonstration we assume to be on one such fraction of the data. We walk through the process of
        * accessing the data directly from a Kinetica table via the UDF API's proc_data handle
        * using H2O to derive a GLM model from it
        * store the model into a Kinetica table (via KiFS)
        * load the model from the Kinetica table (via KiFS)
        * apply the loaded model for inference
    For the last two steps of this approach you can imagine to be in an ensemble learning situation, where you have
    multiple models loaded (100s), and want to output a combined (average/majority/weighted/...) prediction result.

    Note that when using proc_data to access data from Kinetica tables, we are in a distributed environment. Each
    instance of the UDF accesses the data of its respective TOM. This can make sense when you have large data and
    like to learn multiple models - each on a fraction of the data. However, in this situation it is important to 
    keep two things in mind:
    1) The data needs to be distributed across TOMs such that its distribution is (nearly) the same on each TOM. This 
        could for example be achieved by introducing a column with random numbers and using that as the shard key.
    2) At the inference step all models are applied to a record and the prediction result need to be combined. 
        This could be done efficiently through another distributed UDF (that loads the models from a replicated table).
"""

"""Initialize demo dependencies"""
h2o.init(nthreads=-1)

"""Get H2O data frame via Kinetica UDF API"""
print('Receiving h2o df...')
proc_data = ProcData()
h20_df = proc_data.to_h2odf()
print('h2o df shape: {}'.format(h20_df.shape))

"""Prepare data set"""
print('Partitioning data')
splits = h20_df.split_frame(ratios=[0.7, 0.15], seed=1)
train = splits[0]
valid = splits[1]
test = splits[2]
print('Identify response and predictor variables')
y = 'bad_loan'
x = list(h20_df.columns)
x.remove(y)  # remove the response
x.remove('int_rate')  # remove the interest rate column because it's correlated with the outcome
x.remove('record_id')
print('Predictor columns: {}'.format(x))

"""Use H2O API to learn a random forrest model"""
print('Train a random forrest')
rf_fit1 = H2ORandomForestEstimator(model_id='rf_fit', seed=1)
rf_fit1.train(x=x, y=y, training_frame=train)

"""Store the model into a Kinetica table to have it available for inference, e.g. in an ensemble"""
print('Storing model to table (via KiFS)')
kifs_path = proc_data.request_info['kifs_mount_point']
print('KiFS mount point: {}'.format(kifs_path))
model1_path = h2o.save_model(rf_fit1, kifs_path+'/RF_model', force=True)
print('Saved model file to: {}'.format(model1_path))

"""Demonstrate how to load the H2O model from a Kinetica table"""
print('Load model from KiFS to H2O.')
model1 = h2o.load_model(model1_path)

"""Use loaded model for inference on test data set"""
print('Apply loaded model to test set')
performance = model1.model_performance(test)
print('Performance of model 1: {}'.format(performance))

"""Shutdown demo"""
proc_data.complete()
h2o.cluster().shutdown()
