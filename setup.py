# Install the GPUdb python API to the system module path.

from distutils.core import setup

setup(
    name='kinetica_proc',
    version='6.0.0',
    description='Python libraries to create procs in Kinetica.',
    author='Kinetica',
    author_email='support@kinetica.com',
    url='http://kinetica.com',
    py_modules = ['kinetica_proc', 'proc_example'],
)
