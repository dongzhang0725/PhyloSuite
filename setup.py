#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pipenv install twine --dev

import io
import os
import platform
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'PhyloSuite'
DESCRIPTION = 'A desktop platform for streamlined molecular sequence data management and state of the art evolutionary phylogenetics studies.'
URL = 'https://github.com/dongzhang0725/PhyloSuite'
EMAIL = 'dongzhang0725@gmail.com'
AUTHOR = 'Dong Zhang'
REQUIRES_PYTHON = '>=3.6.0, <=3.7.0'
VERSION = '2.0.dev2'

platform_ = platform.system().lower()

# 如何配置：https://stackoverflow.com/questions/16055403/setuptools-platform-specific-dependencies
# What packages are required for this module to be executed?
REQUIRED = [
    'pyparsing==3.0.7',
    'Pillow==8.4.0',
    'numpy==1.19.5',
    'netCDF4==1.5.6',
    'biopython==1.76',
    'python-dateutil',
    'suds-py3',
    'PyQt5==5.10.1',
    'psutil',
    'pywin32; platform_system=="Windows"',
    'plotly==5.10.0',
    'pandas==1.1.5',
    'kaleido==0.2.1; platform_system=="Darwin"',
    'kaleido==0.2.1; platform_system=="Linux"',
    'kaleido==0.1.*; platform_system=="Windows"', # other version will cause error,like 0.2.1
    'statsmodels==0.10.2; platform_system=="Darwin"',
    'statsmodels==0.12.2; platform_system=="Linux"',
    'statsmodels==0.12.2; platform_system=="Windows"',
    'matplotlib==3.3.4; platform_system=="Windows"',
    'matplotlib==3.2.2; platform_system=="Darwin"',
    'matplotlib==3.2.2; platform_system=="Linux"',
    "dna-features-viewer==3.1.3",
    "dataclasses==0.8",
    "seaborn==0.11.2",
    "arviz==0.11.4",
    "DendroPy==4.4.0"
]
# , 'reportlab==3.5.57'

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(sys.argv[0]))
here = os.path.abspath(os.path.dirname(__file__)) if not os.path.exists(here + os.sep + "MANIFEST.in") else here
# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine…')
        os.system('twine upload dist/*')

        self.status('Pushing git tags…')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["todo"]),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    platforms='Linux; MacOS X; Windows',
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='GNU Affero General Public License v3 or later (AGPLv3+)',
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: Implementation :: CPython',
        # 'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: User Interfaces'
    ],
    entry_points={
              'console_scripts': [
                  'PhyloSuite = PhyloSuite.PhyloSuite:start',
              ],
    }
    # $ setup.py publish support.
    # cmdclass={
    #     'upload': UploadCommand,
    # },
)