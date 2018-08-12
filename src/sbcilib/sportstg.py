'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from collections import OrderedDict, namedtuple
import csv
from datetime import date
from time import strptime

from sbcilib.utils import SbciColumnDesc, latin1_str


_stgmem_cols = (
    SbciColumnDesc(
        'fiba_id',
        lambda v: latin1_str(v),
        'FIBA ID Number'
    ),
    SbciColumnDesc(
        'member_id',
        lambda v: latin1_str(v),
        'Member ID'
    ),
    SbciColumnDesc(
        'member_no',
        lambda v: latin1_str(v),
        'Member No.'
    ),
    SbciColumnDesc(
        'first_name',
        lambda v: latin1_str(v),
        'First Name'
    ),
    SbciColumnDesc(
        'preferred_name',
        lambda v: latin1_str(v),
        'Preferred Name'
    ),
    SbciColumnDesc(
        'family_name',
        lambda v: latin1_str(v),
        'Family Name'
    ),
    SbciColumnDesc(
        'date_of_birth',
        lambda v: latin1_str(v),
        'Date of Birth'
    ),
    SbciColumnDesc(
        'gender',
        lambda v: latin1_str(v),
        'Gender'
    ),
    SbciColumnDesc(
        'parent1_firstname',
        lambda v: latin1_str(v),
        'Parent/Guardian 1 Firstname'
    ),
    SbciColumnDesc(
        'parent1_surname',
        lambda v: latin1_str(v),
        'Parent/Guardian 1 Surname'
    ),
    SbciColumnDesc(
        'parent1_gender',
        lambda v: latin1_str(v),
        'Parent/Guardian 1 Gender'
    ),
    SbciColumnDesc(
        'parent1_mobile',
        lambda v: latin1_str(v),
        'Parent/Guardian 1 Mobile'
    ),
    SbciColumnDesc(
        'parent1_email',
        lambda v: latin1_str(v),
        'Parent/Guardian 1 Email'
    ),
    SbciColumnDesc(
        'parent2_firstname',
        lambda v: latin1_str(v),
        'Parent/Guardian 2 Firstname'
    ),
    SbciColumnDesc(
        'parent2_surname',
        lambda v: latin1_str(v),
        'Parent/Guardian 2 Surname'
    ),
    SbciColumnDesc(
        'parent2_gender',
        lambda v: latin1_str(v),
        'Parent/Guardian 2 Gender'
    ),
    SbciColumnDesc(
        'parent2_mobile',
        lambda v: latin1_str(v),
        'Parent/Guardian 2 Mobile'
    ),
    SbciColumnDesc(
        'parent2_email',
        lambda v: latin1_str(v),
        'Parent/Guardian 2 Email'
    ),
    SbciColumnDesc(
        'address1',
        lambda v: latin1_str(v),
        'Address 1'
    ),
    SbciColumnDesc(
        'address2',
        lambda v: latin1_str(v),
        'Address 2'
    ),
    SbciColumnDesc(
        'suburb',
        lambda v: latin1_str(v),
        'Suburb'
    ),
    SbciColumnDesc(
        'postal_code',
        lambda v: latin1_str(v),
        'Postal Code'
    ),
    SbciColumnDesc(
        'phone_home',
        lambda v: latin1_str(v),
        'Telephone Number (Home)'
    ),
    SbciColumnDesc(
        'phone_work',
        lambda v: latin1_str(v),
        'Telephone Number (Work)'
    ),
    SbciColumnDesc(
        'mobile',
        lambda v: latin1_str(v),
        'Telephone Number (Mobile)'
    ),
    SbciColumnDesc(
        'email',
        lambda v: latin1_str(v),
        'Email'
    ),
    SbciColumnDesc(
        'medical_notes',
        lambda v: latin1_str(v),
        'Medical Notes'
    ),
    SbciColumnDesc(
        'wwc_check_number',
        lambda v: latin1_str(v),
        'WWC Check Number'
    ),
    SbciColumnDesc(
        'wwc_check_expiry',
        lambda v: latin1_str(v),
        'WWC Check Expiry'
    ),
    SbciColumnDesc(
        'vjbl_level',
        lambda v: latin1_str(v),
        'VJBL Level'
    ),
    SbciColumnDesc(
        'notes',
        lambda v: latin1_str(v),
        'Notes'
    ),
    SbciColumnDesc(
        'first_registered',
        lambda v: latin1_str(v),
        'First Registered'
    ),
    SbciColumnDesc(
        'last_registered',
        lambda v: latin1_str(v),
        'Last Registered'
    ),
    SbciColumnDesc(
        'registered_until',
        lambda v: latin1_str(v),
        'Registered Until'
    ),
    SbciColumnDesc(
        'last_updated',
        lambda v: latin1_str(v),
        'Last Updated'
    ),
    SbciColumnDesc(
        'season',
        lambda v: latin1_str(v),
        'Season'
    ),
    SbciColumnDesc(
        'season_player',
        lambda v: latin1_str(v),
        'Season Player ?'
    ),
    SbciColumnDesc(
        'season_player_financial',
        lambda v: latin1_str(v),
        'Season Player Financial ?'
    ),
    SbciColumnDesc(
        'date_player_created_in_season',
        lambda v: latin1_str(v),
        'Date Player created in Season'
    ),
    SbciColumnDesc(
        'season_coach',
        lambda v: latin1_str(v),
        'Season Coach'
    ),
    SbciColumnDesc(
        'date_coach_created_in_season',
        lambda v: latin1_str(v),
        'Date Coach created in Season'
    ),
    SbciColumnDesc(
        'season_misc',
        lambda v: latin1_str(v),
        'Season Misc'
    ),
    SbciColumnDesc(
        'date_misc_created_in_season',
        lambda v: latin1_str(v),
        'Date Misc created in Season'
    ),
    SbciColumnDesc(
        'regoform_last_used_in_season',
        lambda v: latin1_str(v),
        'RegoForm last used in Season'
    ),
    SbciColumnDesc(
        'date_regoform_last_used_in_season',
        lambda v: latin1_str(v),
        'Date RegoForm last used in Season'
    ),
    SbciColumnDesc(
        'club_default_number',
        lambda v: latin1_str(v),
        'Club Default Number'
    ),
    SbciColumnDesc(
        'school_name',
        lambda v: latin1_str(v),
        'School Name'
    ),
    SbciColumnDesc(
        'school_suburb',
        lambda v: latin1_str(v),
        'School Suburb'
    ),
    SbciColumnDesc(
        'bsb',
        lambda v: latin1_str(v),
        'BSB'
    ),
    SbciColumnDesc(
        'account_number',
        lambda v: latin1_str(v),
        'Account Number'
    ),
    SbciColumnDesc(
        'account_name',
        lambda v: latin1_str(v),
        'Account Name'
    ),
    SbciColumnDesc(
        'competition_season',
        lambda v: latin1_str(v),
        'Competition Season'
    ),
    SbciColumnDesc(
        'competition_name',
        lambda v: latin1_str(v),
        'Competition Name'
    ),
    SbciColumnDesc(
        'team_name',
        lambda v: latin1_str(v),
        'Team Name'
    ),
)


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


_players_colmap = OrderedDict((
    ('FIBA ID Number',     'fiba_id_number'),
    ('Member ID',          'member_id'),
    ('Member No.',         'member_number'),
    ('First Name',         'first_name'),
    ('Family Name',        'family_name'),
    ('Gender',             'gender'),
    ('Competition Season', 'competition_season'),
    ('Competition Name',   'competition_name'),
    ('Team Name',          'team_name'),
    ('Season',             'season'),
))


_players_date_columns = (
)


MembersRecord = namedtuple('MembersRecord', _members_colmap.values())


PlayersRecord = namedtuple('PlayersRecord', _players_colmap.values())


def MembersReadCSV(csvfile, verbose=0):
    '''TODO'''

    if verbose > 0:
        print('Reading Members CSV file: {} ... '.format(csvfile), end='')

    records = []
    first_column_name = next(iter(_members_colmap))

    with open(csvfile) as fd:

        reader = csv.DictReader(fd)

        for d in reader:

            # SportsTG puts crap at the end ...
            if d[first_column_name] == ' rows ':
                break

            data = {
                _members_colmap[k]: unicode(d[k], encoding='utf-8')
                if type(d[k]) is str else d[k]
                for k in _members_colmap
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
        print('{} member records read.'.format(len(records)))

    return records


def PlayersReadCSV(csvfile, verbose=0):
    '''TODO'''

    if verbose > 0:
        print('Reading Players CSV file: {} ... '.format(csvfile), end='')

    records = []
    first_column_name = next(iter(_players_colmap))

    with open(csvfile) as fd:

        reader = csv.DictReader(fd)

        for d in reader:

            # SportsTG puts crap at the end ...
            if d[first_column_name] == ' rows ':
                break

            data = {
                _players_colmap[k]: unicode(d[k], encoding='utf-8')
                if type(d[k]) is str else d[k]
                for k in _players_colmap
            }

            for k in _players_date_columns:
                if data[k] == '':
                    data[k] = None
                elif data[k] is not None:
                    data[k] = date(*strptime(data[k], '%d/%m/%Y')[:3])

            record = PlayersRecord(**data)

            if verbose > 1:
                print('{}'.format(record))

            records.append(record)

    if verbose > 0:
        print('{} player records read.'.format(len(records)))

    return records


__all__ = ['MembersRecord', 'MembersReadCSV', 'PlayersRecord', 'PlayersReadCSV']
