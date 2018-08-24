'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from sbcilib.utils import SbciCSVColumn, SbciCSVInfo, latin1_str, date_str, \
    phone_str, email_str, postcode_str, boolean_str, posint_str


stg_members_csvinfo = SbciCSVInfo(
    SbciCSVColumn(
        'fiba_id',
        latin1_str,
        'FIBA ID Number',
    ),
    SbciCSVColumn(
        'member_id',
        latin1_str,
        'Member ID',
    ),
    SbciCSVColumn(
        'member_no',
        latin1_str,
        'Member No.',
    ),
    SbciCSVColumn(
        'first_name',
        latin1_str,
        'First Name',
    ),
    SbciCSVColumn(
        'preferred_name',
        latin1_str,
        'Preferred Name',
    ),
    SbciCSVColumn(
        'family_name',
        latin1_str,
        'Family Name',
    ),
    SbciCSVColumn(
        'date_of_birth',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date of Birth',
    ),
    SbciCSVColumn(
        'gender',
        latin1_str,
        'Gender',
    ),
    SbciCSVColumn(
        'parent1_firstname',
        latin1_str,
        'Parent/Guardian 1 Firstname',
    ),
    SbciCSVColumn(
        'parent1_surname',
        latin1_str,
        'Parent/Guardian 1 Surname',
    ),
    SbciCSVColumn(
        'parent1_gender',
        latin1_str,
        'Parent/Guardian 1 Gender',
    ),
    SbciCSVColumn(
        'parent1_mobile',
        phone_str,
        'Parent/Guardian 1 Mobile',
    ),
    SbciCSVColumn(
        'parent1_email',
        email_str,
        'Parent/Guardian 1 Email',
    ),
    SbciCSVColumn(
        'parent2_firstname',
        latin1_str,
        'Parent/Guardian 2 Firstname',
    ),
    SbciCSVColumn(
        'parent2_surname',
        latin1_str,
        'Parent/Guardian 2 Surname',
    ),
    SbciCSVColumn(
        'parent2_gender',
        latin1_str,
        'Parent/Guardian 2 Gender',
    ),
    SbciCSVColumn(
        'parent2_mobile',
        phone_str,
        'Parent/Guardian 2 Mobile',
    ),
    SbciCSVColumn(
        'parent2_email',
        email_str,
        'Parent/Guardian 2 Email',
    ),
    SbciCSVColumn(
        'address1',
        latin1_str,
        'Address 1',
    ),
    SbciCSVColumn(
        'address2',
        latin1_str,
        'Address 2',
    ),
    SbciCSVColumn(
        'suburb',
        latin1_str,
        'Suburb',
    ),
    SbciCSVColumn(
        'postal_code',
        postcode_str,
        'Postal Code',
    ),
    SbciCSVColumn(
        'phone_home',
        phone_str,
        'Telephone Number (Home)',
    ),
    SbciCSVColumn(
        'phone_work',
        phone_str,
        'Telephone Number (Work)',
    ),
    SbciCSVColumn(
        'mobile',
        phone_str,
        'Telephone Number (Mobile)',
    ),
    SbciCSVColumn(
        'email',
        email_str,
        'Email',
    ),
    SbciCSVColumn(
        'medical_notes',
        latin1_str,
        'Medical Notes',
    ),
    SbciCSVColumn(
        'wwc_check_number',
        latin1_str,
        'WWC Number', 'WWC Check Number',
    ),
    SbciCSVColumn(
        'wwc_check_expiry',
        lambda v: date_str(v, '%d/%m/%Y'),
        'WWC Expiry', 'WWC Check Expiry',
    ),
    SbciCSVColumn(
        'vjbl_level',
        latin1_str,
        'VJBL Level',
    ),
    SbciCSVColumn(
        'custom_text_field_25',
        latin1_str,
        'Custom Text Field 25',
        ignored=True
    ),
    SbciCSVColumn(
        'willingness_to_volunteer',
        latin1_str,
        'Willingness to Volunteer',
        ignored=True
    ),
    SbciCSVColumn(
        'notes',
        latin1_str,
        'Notes',
    ),
    SbciCSVColumn(
        'first_registered',
        lambda v: date_str(v, '%d/%m/%Y'),
        'First Registered',
    ),
    SbciCSVColumn(
        'last_registered',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Last Registered',
    ),
    SbciCSVColumn(
        'registered_until',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Registered Until',
    ),
    SbciCSVColumn(
        'last_updated',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Last Updated'
    ),
    SbciCSVColumn(
        'season',
        latin1_str,
        'Season',
    ),
    SbciCSVColumn(
        'season_player',
        boolean_str,
        'Season Player ?',
    ),
    SbciCSVColumn(
        'season_player_financial',
        boolean_str,
        'Season Player Financial ?',
    ),
    SbciCSVColumn(
        'date_player_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Player created in Season',
    ),
    SbciCSVColumn(
        'season_coach',
        boolean_str,
        'Season Coach',
    ),
    SbciCSVColumn(
        'date_coach_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Coach created in Season',
    ),
    SbciCSVColumn(
        'season_misc',
        boolean_str,
        'Season Misc',
    ),
    SbciCSVColumn(
        'date_misc_created_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Misc created in Season',
    ),
    SbciCSVColumn(
        'regoform_last_used_in_season',
        latin1_str,
        'RegoForm last used in Season',
    ),
    SbciCSVColumn(
        'date_regoform_last_used_in_season',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date RegoForm last used in Season',
    ),
    SbciCSVColumn(
        'club_default_number',
        posint_str,
        'Club Default Number',
    ),
    SbciCSVColumn(
        'school_name',
        latin1_str,
        'School Name',
    ),
    SbciCSVColumn(
        'school_suburb',
        latin1_str,
        'School Suburb',
    ),
    SbciCSVColumn(
        'bsb',
        latin1_str,
        'BSB',
    ),
    SbciCSVColumn(
        'account_number',
        latin1_str,
        'Account Number',
    ),
    SbciCSVColumn(
        'account_name',
        latin1_str,
        'Account Name',
    ),
    SbciCSVColumn(
        'competition_season',
        latin1_str,
        'Competition Season',
    ),
    SbciCSVColumn(
        'competition_name',
        latin1_str,
        'Competition Name',
    ),
    SbciCSVColumn(
        'team_name',
        latin1_str,
        'Team Name',
    ),
)


__all__ = ['stg_members_csvinfo']
