'''
setuptools module for installation and distribution.

@author: jen117
'''
import os
from setuptools import setup, find_packages

_cwd = os.path.abspath('.')

setup(
    name='sbci',

    version='0.1',

    description='Python lib and utils for Shooters Basketball Club Inc.',
    long_description='''
Python library and utilities for Shooters Basketball Club Inc.

Copyright (C) 2018 Murray Jensen - All Rights Reserved.
''',

    author='Murray Jensen',
    author_email='mjj@jensen-williams.id.au',

    license='Apache License 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
    ],

    keywords='shooters basketball library utilities',

    package_dir={'': _cwd},
    packages=find_packages(_cwd, exclude=[]),

    entry_points={
        'console_scripts': [
            'finance_cbtrximport = finance.cbtrximport:main',
            'finance_tbtrximport = finance.tbtrximport:main',
            'teams_checkstg = teams.checkstg:main',
            'teams_readtest = teams.readtest:main',
            'teams_wwcreport = teams.wwcreport:main',
            'uniforms_process = uniforms.process:main',
        ],
    },
)
