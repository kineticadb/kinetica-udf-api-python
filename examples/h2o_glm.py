from kinetica_proc import ProcData
from util import test_environment as te
import h2o
from h2o.estimators.glm import H2OGeneralizedLinearEstimator
import shutil


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
        * store the model into a Kinetica table
        * load the model from the Kinetica table
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
te.ingest_loan_data()
te.init_udfsim([te.LOAN_DATA_TABLE_NAME])
h2o.init(nthreads=-1)


"""Get H2O data frame via Kinetica UDF API"""
print('Receiving h2o df...')
proc_data = ProcData()
h20_df = proc_data.to_h2odf()
proc_data.complete()
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
print('Predictor columns: {}'.format(x))


"""Use H2O API to learn a GLM model"""
print('Train a default GLM')
glm_fit1 = H2OGeneralizedLinearEstimator(family='binomial', model_id='glm_fit1')
glm_fit1.train(x=x, y=y, training_frame=train)


"""Store the model into a Kinetica table to have it available for inference, e.g. in an ensemble"""
print('Serializing model object')
# we use h2o.save_model for serialization because pickle does not work with h2o models
tmp_model1_path = h2o.save_model(glm_fit1, './tmp_model_directory', force=True)
print('Wrote tmp model file to: {}'.format(tmp_model1_path))
print("Load model data from file.")
file = open(tmp_model1_path, mode='rb')
# with open(tmp_model1_path, mode='rb') as file:
model1_from_file = file.read()
file.close()
print('Store model to table.')
te.create_model_table()
te.store_model(model_id=1, model_name='glm1', model_binary=model1_from_file)


"""Demonstrate how to load the H2O model from a Kinetica table"""
print('Load model from table')
model1_from_table = te.load_model(1)
print('Write loaded model to file (to be able to use h2o.load_model)')
model_file = open('./tmp_model_directory/model1_from_table', 'wb')
model_file.write(model1_from_table)
model_file.close()
print('Load model to H2O.')
model1 = h2o.load_model('./tmp_model_directory/model1_from_table')


"""Use loaded model for inference on test data set"""
print('Apply loaded model to test set')
print('Performance of model 1: {}'.format(model1.model_performance(test)))


"""Delete demo artifacts"""
print('Deleting demo artifacts')
shutil.rmtree('./tmp_model_directory')
te.delete_udfsim_artifacts()
te.delete_loan_data()
te.delete_model_table()
h2o.cluster().shutdown()
print('Artifacts deleted - demo finished.')
