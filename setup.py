# Install the GPUdb python API to the system module path.

from distutils.core import setup

setup(
    name='kinetica_proc',
    version='7.1.0.0',
    description='Python libraries to create procs in Kinetica.',
    author='Kinetica',
    author_email='support@kinetica.com',
    url='http://kinetica.com',
    py_modules=['kinetica_proc', 'examples/UDF_simple/proc_example']
)
