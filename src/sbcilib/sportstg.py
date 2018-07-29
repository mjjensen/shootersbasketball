'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from collections import OrderedDict, namedtuple
import csv
from datetime import date
from time import strptime


_members_columnmap = OrderedDict((
    ('FIBA ID Number',                    'fiba_id'),
    ('Member ID',                         'member_id'),
    ('Member No.',                        'member_no'),
    ('First Name',                        'first_name'),
    ('Preferred Name',                    'preferred_name'),
    ('Family Name',                       'family_name'),
    ('Date of Birth',                     'date_of_birth'),
    ('Gender',                            'gender'),
    ('Parent/Guardian 1 Firstname',       'parent1_firstname'),
    ('Parent/Guardian 1 Surname',         'parent1_surname'),
    ('Parent/Guardian 1 Gender',          'parent1_gender'),
    ('Parent/Guardian 1 Mobile',          'parent1_mobile'),
    ('Parent/Guardian 1 Email',           'parent1_email'),
    ('Parent/Guardian 2 Firstname',       'parent2_firstname'),
    ('Parent/Guardian 2 Surname',         'parent2_surname'),
    ('Parent/Guardian 2 Gender',          'parent2_gender'),
    ('Parent/Guardian 2 Mobile',          'parent2_mobile'),
    ('Parent/Guardian 2 Email',           'parent2_email'),
    ('Address 1',                         'address1'),
    ('Address 2',                         'address2'),
    ('Suburb',                            'suburb'),
    ('Postal Code',                       'postal_code'),
    ('Telephone Number (Home)',           'phone_home'),
    ('Telephone Number (Work)',           'phone_work'),
    ('Telephone Number (Mobile)',         'mobile'),
    ('Email',                             'email'),
    ('Medical Notes',                     'medical_notes'),
    ('WWC Check Number',                  'wwc_check_number'),
    ('WWC Check Expiry',                  'wwc_check_expiry'),
    ('VJBL Level',                        'vjbl_level'),
    ('Custom Text Field 25',              'custom_text_field25'),
    ('Willingness to Volunteer ',         'willingness_to_volunteer'),
    ('Notes',                             'notes'),
    ('First Registered',                  'first_registered'),
    ('Last Registered',                   'last_registered'),
    ('Registered Until',                  'registered_until'),
    ('Last Updated',                      'last_updated'),
    ('Season',                            'season'),
    ('Season Player ?',                   'season_player'),
    ('Season Player Financial ?',         'season_player_financial'),
    ('Date Player created in Season',     'date_player_created_in_season'),
    ('Season Coach',                      'season_coach'),
    ('Date Coach created in Season',      'date_coach_created_in_season'),
    ('Season Misc',                       'season_misc'),
    ('Date Misc created in Season',       'date_misc_created_in_season'),
    ('RegoForm last used in Season',      'regoform_last_used_in_season'),
    ('Date RegoForm last used in Season', 'date_regoform_last_used_in_season'),
    ('Club Default Number',               'club_default_number'),
    ('School Name',                       'school_name'),
    ('School Suburb',                     'school_suburb'),
    ('BSB',                               'bsb'),
    ('Account Number',                    'account_number'),
    ('Account Name',                      'account_name'),
))


_members_date_columns = (
    'date_of_birth',
    'wwc_check_expiry',
    'first_registered',
    'last_registered',
    'registered_until',
    'last_updated',
    'date_player_created_in_season',
    'date_coach_created_in_season',
    'date_misc_created_in_season',
    'date_regoform_last_used_in_season',
)


MembersRecord = namedtuple('STGMembersRecord', _members_columnmap.viewvalues())


def MembersReadCSV(csvfile, verbose=0):
    '''TODO'''

    if verbose > 0:
        print('Reading Members CSV file: {} ... '.format(csvfile), end='')

    records = []
    first_column_name = next(iter(_members_columnmap))

    with open(csvfile) as fd:

        reader = csv.DictReader(fd)

        for d in reader:

            # SportsTG puts crap at the end ...
            if d[first_column_name] == ' rows ':
                break

            data = {
                _members_columnmap[k]: unicode(d[k], encoding='utf-8')
                if type(d[k]) is str else d[k]
                for k in _members_columnmap
            }

            for k in _members_date_columns:
                if data[k] == '':
                    data[k] = None
                elif data[k] is not None:
                    data[k] = date(*strptime(data[k], '%d/%m/%Y')[:3])

            record = MembersRecord(**data)

            if verbose > 1:
                print('{}'.format(record))

            records.append(record)

    if verbose > 0:
        print('{} CSV records read.'.format(len(records)))

    return records
