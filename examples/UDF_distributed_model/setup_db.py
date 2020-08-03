from util import test_environment as te


"""Setup train and test table with example loan data for UDF."""

te.create_schema()
te.prepare_loan_data()
te.create_ensemble_model_table()
