from util import test_environment as te


"""Setup the table example_loan_data for UDF."""

te.create_schema()
te.prepare_loan_data()
