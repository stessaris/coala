from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(
    # Application name:
    name="coala",

    # Version number (initial):
    version="2.460",

    # Application author details:
    author="Christian Schulz-Hanke",
    author_email="Christian.Schulz-Hanke@cs.uni-potsdam.de",

    # Packages
    packages=["coala","coala.parse","coala.bc","coala.bc_legacy","coala.bcLc","coala.b","coala.bcAgent","coala.bcAgent_legacy"],

    #
    scripts=["coala/coala","outputformatclingocoala"],

    # Include additional files into the package
    #include_package_data=True,

    # Details
    url="https://github.com/potassco/coala",

    #
    # license="LICENSE.txt",
    description="coala - Action Language Translation Tool.",

    # long_description=open("README.txt").read(),
    long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[
        "ply>=3.8",
    ],

    package_dir={'coala': 'coala'},
    package_data={
        'coala': [
            'README_BC.txt',
            'internal/*.lp',
            'testcases/*'
        ]
    }
)

# Build: python setup.py sdist
