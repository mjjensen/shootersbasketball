'''
setuptools module for installation and distribution.

@author: jen117
'''
import os
from setuptools import setup, find_packages

_dotdot = os.path.abspath('..')

setup(
    name='sbci',

    version='0.1',

    description='A Python library and tools for Shooters Basketball Club Inc.',
    long_description='''
A Python library and tools for Shooters Basketball Club Inc.

Copyright (C) 2018 Murray Jensen - All Rights Reserved.
''',

    author='Murray Jensen',
    author_email='mjj@jensen-williams.id.au',

    license='Apache',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
    ],

    keywords='shooters basketball club library',

    package_dir={'': _dotdot},
    packages=find_packages(_dotdot, exclude=[]),

    entry_points={
        'console_scripts': [
            'checkstg = teams.checkstg:main',
            'readtest = teams.readtest:main',
            'wwcreport = teams.wwcreport:main',
            'cbtrximport = finance.cbtrximport:main',
            'tbtrximport = finance.tbtrximport:main',
        ],
    },
)
