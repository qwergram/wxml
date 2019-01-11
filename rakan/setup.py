from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='Rakan',
    ext_modules=cythonize('rakan.pyx', annotate=True),
)