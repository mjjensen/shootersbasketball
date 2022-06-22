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

Copyright (C) 2018-21 Murray Jensen - All Rights Reserved.
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
            'check_participants = sbci.check_participants:main',
            'check_team_entries = sbci.check_team_entries:main',
            'check_trybooking = sbci.check_trybooking:main',
            'email_info = sbci.email_info:main',
            'print_games = sbci.print_games:main',
            'print_participants = sbci.print_participants:main',
            'print_clinic_participants = sbci.print_clinic_participants:main',
            'print_teams_db = sbci.print_teams_db:main',
            'process_csv_clinic_tb = sbci.process_csv_clinic_tb:main',
            'process_csv_clinic = sbci.process_csv_clinic:main',
            'process_csv_devteams_tb = sbci.process_csv_devteams_tb:main',
            'process_csv_training_forms = sbci.process_csv_training_forms:main',
            'process_csv_xacts_tb = sbci.process_csv_xacts_tb:main',
            'process_csv_xero_upload = sbci.process_csv_xero_upload:main',
            'process_xls_clinic = sbci.process_xls_clinic:main',
            'process_xlsx_fixtures = sbci.process_xlsx_fixtures:main',
            'wwc_report = sbci.wwc_report:main',
        ],
    },
)
