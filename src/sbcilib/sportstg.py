'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from collections import deque
from collections import namedtuple
import csv

from sbcilib.utils import SbciColumnDesc, latin1_str, date_str, phone_str, \
    email_str, postcode_str, boolean_str, posint_str


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
        lambda v: date_str(v, '%d/%m/%Y'),
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
        lambda v: phone_str(v),
        'Parent/Guardian 1 Mobile'
    ),
    SbciColumnDesc(
        'parent1_email',
        lambda v: email_str(v),
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
        lambda v: phone_str(v),
        'Parent/Guardian 2 Mobile'
    ),
    SbciColumnDesc(
        'parent2_email',
        lambda v: email_str(v),
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
        lambda v: postcode_str(v),
        'Postal Code'
    ),
    SbciColumnDesc(
        'phone_home',
        lambda v: phone_str(v),
        'Telephone Number (Home)'
    ),
    SbciColumnDesc(
        'phone_work',
        lambda v: phone_str(v),
        'Telephone Number (Work)'
    ),
    SbciColumnDesc(
        'mobile',
        lambda v: phone_str(v),
        'Telephone Number (Mobile)'
    ),
    SbciColumnDesc(
        'email',
        lambda v: email_str(v),
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
        lambda v: date_str(v, '%d/%m/%Y'),
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
        lambda v: date_str(v, '%d/%m/%Y'),
        'First Registered'
    ),
    SbciColumnDesc(
        'last_registered',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Last Registered'
    ),
    SbciColumnDesc(
        'registered_until',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Registered Until'
    ),
    SbciColumnDesc(
        'last_updated',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Last Updated'
    ),
    SbciColumnDesc(
        'season',
        lambda v: latin1_str(v),
        'Season'
    ),
    SbciColumnDesc(
        'season_player',
        lambda v: boolean_str(v),
        'Season Player ?'
    ),
    SbciColumnDesc(
        'season_player_financial',
        lambda v: boolean_str(v),
        'Season Player Financial ?'
    ),
    SbciColumnDesc(
        'date_player_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Player created in Season'
    ),
    SbciColumnDesc(
        'season_coach',
        lambda v: boolean_str(v),
        'Season Coach'
    ),
    SbciColumnDesc(
        'date_coach_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Coach created in Season'
    ),
    SbciColumnDesc(
        'season_misc',
        lambda v: boolean_str(v),
        'Season Misc'
    ),
    SbciColumnDesc(
        'date_misc_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Misc created in Season'
    ),
    SbciColumnDesc(
        'regoform_last_used_in_season',
        lambda v: latin1_str(v),
        'RegoForm last used in Season'
    ),
    SbciColumnDesc(
        'date_regoform_last_used_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date RegoForm last used in Season'
    ),
    SbciColumnDesc(
        'club_default_number',
        lambda v: posint_str(v),
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
_stgmem_del = (54, )


class STGMembersCSVRecord(namedtuple('STGMembersCSVRecord',
                                     (c.name for c in _stgmem_cols))):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(STGMembersCSVRecord, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def STGMembersCSVRead(csvfile, verbose=0, reverse=False):
    '''TODO'''

    if verbose > 0:
        print('Reading SportsTG Members CSV file: {} ... '
              .format(csvfile), end='')

    records = deque()

    with open(csvfile) as fd:

        reader = csv.reader(fd)

        headings = next(reader)
        for c in _stgmem_del:
            del headings[c]

        for c, h in zip(_stgmem_cols, headings):
            if h != c.head:
                raise RuntimeError('column heading mismatch! ("%s" != "%s")'
                                   % (h, c.head))

        for row in reader:

            for c in _stgmem_del:
                del row[c]

            if row[0].endswith(' rows '):
                break

            if verbose > 2:
                print('row={}'.format(row))

            record = STGMembersCSVRecord(*(c.func(v)
                                           for c, v in zip(_stgmem_cols, row)))

            if verbose > 1:
                print('{}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} records read.'.format(len(records)))

    return records


__all__ = ['STGMembersCSVRecord', 'STGMembersCSVRead']
