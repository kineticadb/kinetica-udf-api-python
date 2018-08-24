from kinetica_proc import ProcData
from h2o.estimators.glm import H2OGeneralizedLinearEstimator
import h2o


"""
    This is a demonstration of how to use H2O for model learning and inference in a distributed Kinetica UDF.
    This UDF is registered and executed from register_execute_train_test.py
    The demo is based on this H2O tutorial:
    https://github.com/h2oai/h2o-tutorials/blob/master/h2o-open-tour-2016/chicago/intro-to-h2o.ipynb
    
    This demonstration assumes the situation where the data is large and learning a single model on all data is not
    feasible (e.g. due to memory constraints). A possible approach to address this challenge is to learn multiple 
    models, each on a fraction of the data, and then to combine their inference output (e.g. by averaging).
    In this demonstration we assume to be on one such fraction of the data. We walk through the process of
        * accessing the data directly from a Kinetica table via the UDF API's proc_data handle
        * using H2O to derive a GLM model from it
        * store the model into a Kinetica table via KiFS
    The model is then accessible from another distributed UDF that could do the inference step with it.
    
    Note that when using proc_data to access data from Kinetica tables, we are in a distributed environment. Each
    instance of the UDF accesses the data of its respective TOM. This can make sense when you have large data and
    like to learn multiple models - each on a fraction of the data. However, in this situation it is important to 
    keep two things in mind:
    1) The data needs to be distributed across TOMs such that its distribution is (nearly) the same on each TOM. When
        you use KiFS this should automatically be the case since the data is distributed randomly.
    2) At the inference step all models are applied to a record and the prediction results need to be combined. 
        This could be done efficiently through another distributed UDF.
"""


"""Initialize demo dependencies"""
h2o.init(nthreads=-1)


"""Get H2O data frame via Kinetica UDF API"""
print('Receiving h2o df...')
proc_data = ProcData()
h20_df = proc_data.to_h2odf()

print('h2o df shape: {}'.format(h20_df.shape))


"""Use H2O API to learn a GLM model"""
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
print('Train a default GLM')
glm_fit1 = H2OGeneralizedLinearEstimator(family='binomial', model_id='glm_fit1')
glm_fit1.train(x=x, y=y, training_frame=train)


"""Store the model into a Kinetica table to have it available for inference, e.g. in an ensemble"""
print('Serializing model object, save to KiFS')
tmp_model1_path = h2o.save_model(glm_fit1, '/opt/gpudb/kifs/mount/GLM_model', force=True)

h2o.cluster().shutdown()
proc_data.complete()
