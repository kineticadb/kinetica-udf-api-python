# Install the GPUdb python API to the system module path.

from distutils.core import setup

setup(
    name = 'kinetica_proc',
    version = '7.2.0.0',
    description = 'Python libraries to create procs in Kinetica.',
    author = 'Kinetica DB, Inc.',
    author_email = 'support@kinetica.com',
    url = 'https://www.kinetica.com',
    py_modules = ['kinetica_proc', 'examples/UDF_simple/proc_example']
)
