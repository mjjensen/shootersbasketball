from collections import OrderedDict
from csv import DictReader
from datetime import datetime, date
from enum import unique, IntEnum
from glob import glob
from json import loads
import os
import re
from sqlite3 import connect, Row
from ssl import create_default_context, PROTOCOL_TLS
import sys
from threading import Lock
from time import strftime
import time
from urllib.parse import urlencode
from urllib.request import urlopen

from dateutil.relativedelta import relativedelta
from requests import Session
from requests.adapters import HTTPAdapter
from six import string_types, binary_type, text_type, ensure_text
from urllib3 import PoolManager
from urllib3.util.ssl_ import create_urllib3_context


provider = os.getenv('PROVIDER', 'PlayHQ')
association = os.getenv('ASSOCIATION', 'EDJBA')
season = os.getenv('SEASON', '2023-winter')
clinicterm = os.getenv('CLINICTERM', '2023-Term2')
develterm = os.getenv('DEVELTERM', '2023-Term2-Friday')

shootersdir = os.getenv(
    'SHOOTERSDIR',
    os.path.join(os.getenv('HOME', '.'), 'basketball', 'shooters')
)
seasondir = os.getenv(
    'SEASONDIR',
    os.path.join(shootersdir, provider, association, season)
)
xerodir = os.getenv(
    'XERODIR',
    os.path.join(shootersdir, provider, 'Xero')
)
trybookingdir = os.getenv(
    'TRYBOOKINGDIR',
    os.path.join(shootersdir, 'Trybooking')
)
clinicdir = os.getenv(
    'CLINICDIR',
    os.path.join(shootersdir, provider, 'Clinic', clinicterm)
)
develdir = os.getenv(
    'DEVELDIR',
    os.path.join(shootersdir, provider, 'Devel', develterm)
)


class Team(object):

    def __str__(self):
        vals = []
        for attr in vars(self):
            val = getattr(self, attr)
            if isinstance(val, string_types):
                val = val.encode('utf-8')
            else:
                val = '{}'.format(val)
            vals.append('{}={}'.format(attr, val))
        return 'Team: ' + ', '.join(vals)


# map sql elements to Team object attributes
# first in tuple is sql element, second is team object attr
sql_attr_map = [
    ('gender',            'gender'),
    ('age_group',         'age_group'),
    ('team_number',       'number'),
    ('grade',             'grade'),
    ('team_name',         'name'),
    ('tm.id',             'tm_id'),
    ('tm.dob',            'tm_dob'),
    ('tm.name',           'tm_name'),
    ('tm.email',          'tm_email'),
    ('tm.mobile',         'tm_mobile'),
    ('tm.wwc_name',       'tm_wwcname'),
    ('tm.wwc_number',     'tm_wwcnum'),
    ('tm.wwc_expiry',     'tm_wwcexp'),
    ('co.id',             'co_id'),
    ('co.dob',            'co_dob'),
    ('co.name',           'co_name'),
    ('co.email',          'co_email'),
    ('co.mobile',         'co_mobile'),
    ('co.wwc_name',       'co_wwcname'),
    ('co.wwc_number',     'co_wwcnum'),
    ('co.wwc_expiry',     'co_wwcexp'),
    ('co.postal_address', 'co_address'),
    ('ac.id',             'ac_id'),
    ('ac.dob',            'ac_dob'),
    ('ac.name',           'ac_name'),
    ('ac.email',          'ac_email'),
    ('ac.mobile',         'ac_mobile'),
    ('ac.wwc_name',       'ac_wwcname'),
    ('ac.wwc_number',     'ac_wwcnum'),
    ('ac.wwc_expiry',     'ac_wwcexp'),
    ('ac.postal_address', 'ac_address'),
    ('compats',           'compats'),
    ('playhq_regurl',     'regurl'),
    ('responded',         'responded'),
]


sql_query = '''
    SELECT {} FROM teams
    LEFT JOIN people AS tm ON teams.team_manager_id = tm.id
    LEFT JOIN people AS co ON teams.coach_id = co.id
    LEFT JOIN people AS ac ON teams.asst_coach_id = ac.id
    WHERE teams.active = 'true'
    ORDER BY
'''.format(', '.join(map(lambda elem: elem[0], sql_attr_map)))


def verbose_info(dest=sys.stderr):
    print(
        'season={}\nprovider={}\nshootersdir={}\nseasondir={}'.format(
            season, provider, shootersdir, seasondir
        ),
        file=dest
    )


def fetch_teams(teamsfile='teams.sqlite3', order_by=None, verbose=None):
    '''TODO - document this'''

    if order_by is None:
        order_by = 'gender, age_group, team_number, team_name'

    if verbose is None:
        verbose = True

    if not os.path.exists(teamsfile):
        teamsfile = os.path.join(seasondir, teamsfile)
        if not os.path.exists(teamsfile):
            raise RuntimeError('cannot locate teams sqlite database')

    if verbose:
        print(
            'fetch_teams: using DB file: {} (realpath={})'.format(
                teamsfile, os.path.realpath(teamsfile)
            ),
            file=sys.stderr
        )

    conn = connect(teamsfile)
    conn.row_factory = Row

    try:
        cursor = conn.cursor()

        rows = cursor.execute(sql_query + ' ' + order_by)

        teams = OrderedDict()

        for row in rows:
            t = Team()

            for index, (_, attr) in enumerate(sql_attr_map):
                setattr(t, attr, row[index])

            t.sgender = 'B' if t.gender == 'Boys' else 'G'
            t.sname = t.name[9:]

            t.edjba_id = 'Fairfield-Shooters U{:02d} {} {:02d}'.format(
                t.age_group, t.gender, t.number
            )
            t.edjba_code = '{}{:02d}FS{:02d}'.format(
                t.sgender, t.age_group, t.number
            )

            t.players = []
            t.coaches = []
            t.managers = []

            teams[t.sname] = t

        return teams
    finally:
        conn.close()


def find_team(teams, func=any, **kwds):
    if not kwds:
        raise RuntimeError('find_team: no conditions specified')
    for t in teams.values():
        r = []
        for k, v in kwds.items():
            r.append(getattr(t, k) == v)
        if func(r):
            return t
    return None


def load_config(filename='config.json', prefix=seasondir, verbose=False):
    config = {}
    if not os.path.exists(filename):
        filename = os.path.join(prefix, filename)
    if os.path.exists(filename):
        if verbose:
            print(
                'load_config: using file: {} (realpath={})'.format(
                    filename, os.path.realpath(filename)
                ),
                file=sys.stderr
            )
        with open(filename, 'rb') as cfd:
            config.update(loads(cfd.read().decode()))
    else:
        if verbose:
            print('load_config: no config file found!', file=sys.stderr)
    return config


def get_reports(rtype, rdir='reports', nre=None):

    if nre is None:
        nre = r'^' + rtype + r'_(\d{8})(\d+)\.csv$'
    p = re.compile(nre)

    if not os.path.isdir(rdir):
        rdir = os.path.join(seasondir, rdir)
        if not os.path.isdir(rdir):
            raise RuntimeError('cannot find report dir ({})'.format(rdir))

    matches = []

    # os.walk() returns generator that walks the directory tree; next() on
    # the generator will return the first level (i.e. rdir contents) as a
    # triple (root, dirnames, filenames)
    for name in next(os.walk(rdir))[2]:

        m = p.match(name)
        if m is None:
            continue

        matches.append((name, m))

    return matches


def latest_report(rtype, rdir='reports', nre=None, n2dt=None):
    '''find the latest report file of a certain type'''

    if n2dt is None:
        def n2dt(m):
            return datetime.strptime(
                '{:08d}{:06d}'.format(*map(int, m.groups())), '%Y%m%d%H%M%S'
            )

    latest = None, None

    for name, m in get_reports(rtype, rdir, nre):

        dt = n2dt(m)

        _, ldt = latest
        if not ldt or dt > ldt:
            latest = os.path.join(rdir, name), dt

    return latest


def maybe_strip(s):
    if s is None:
        return None
    else:
        return s.strip()


def trykeys(d, *args, default=None):
    for k in args:
        try:
            return d[k]
        except KeyError:
            pass
    return default


class Participant(object):

    def __init__(self, p, *args, **kwds):
        super(Participant, self).__init__(*args, **kwds)
        self.p = p

    def first_name(self):
        return maybe_strip(trykeys(self.p, 'first name', 'First Name'))

    def last_name(self):
        return maybe_strip(trykeys(self.p, 'last name', 'Last Name'))

    def date_of_birth(self):
        return maybe_strip(trykeys(self.p, 'date of birth', 'Date of Birth'))

    def address(self):
        return maybe_strip(trykeys(self.p, 'address', 'Participant Address'))

    def suburb(self):
        return maybe_strip(trykeys(self.p,
                                   'suburb/town',
                                   'Participant Suburb/Town'))

    def state(self):
        return maybe_strip(trykeys(self.p,
                                   'state/province/region',
                                   'Participant State/Province/Region'))

    def postcode(self):
        return maybe_strip(trykeys(self.p, 'postcode', 'Participant Postcode'))

    def email(self):
        return maybe_strip(trykeys(self.p, 'email', 'Account Holder Email'))

    def parent1_email(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian1 email',
                                   'Parent/Guardian1 Email'))

    def parent2_email(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian2 email',
                                   'Parent/Guardian2 Email'))

    def mobile(self):
        return maybe_strip(trykeys(self.p,
                                   'mobile number',
                                   'Account Holder Mobile'))

    def parent1_mobile(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian1 mobile number',
                                   'Parent/Guardian1 Mobile Number'))

    def parent2_mobile(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian2 mobile number',
                                   'Parent/Guardian2 Mobile Number'))

    def profile_id(self):
        return maybe_strip(trykeys(self.p, 'profile id', 'Profile ID'))

    def opted_in(self):
        return maybe_strip(trykeys(self.p,
                                   'opted-in to marketing',
                                   'Opted In To Marketing'))

    def role(self):
        return maybe_strip(trykeys(self.p, 'role', 'Role'))

    def status(self):
        return maybe_strip(trykeys(self.p, 'status', 'Status'))

    def season(self):
        return maybe_strip(trykeys(self.p, 'season', 'Season'))

    def team_name(self):
        return maybe_strip(trykeys(self.p, 'team name', 'Team'))

    def atsi(self):
        return maybe_strip(trykeys(self.p,
                                   'atsi',
                                   'Aboriginal/Torres Strait Islander'))

    def parent_born_overseas(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian born overseas',
                                   'Parent/Guardian Born Overseas?'))

    def parent1_country_of_birth(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian 1 country of birth',
                                   'Parent/Guardian1 Country Of Birth'))

    def parent2_country_of_birth(self):
        return maybe_strip(trykeys(self.p,
                                   'parent/guardian 2 country of birth',
                                   'Parent/Guardian2 Country Of Birth'))

    def disability(self):
        return maybe_strip(trykeys(self.p, 'disability?', 'Disability'))

    def disability_type(self):
        return maybe_strip(trykeys(self.p,
                                   'disability type',
                                   'Disability Type'))

    def disability_other(self):
        return maybe_strip(trykeys(self.p,
                                   'disability-other',
                                   'Disability Other'))

    def disability_assistance(self):
        return maybe_strip(trykeys(self.p,
                                   'disability assistance',
                                   'Disability Assistance'))

    def full_name(self):
        return self.last_name() + ', ' + self.first_name()

    def __str__(self):
        return self.full_name()


def is_dup(curlist, new):
    nfn = new.first_name().lower()
    nln = new.last_name().lower()
    for old in curlist:
        ofn = old.first_name().lower()
        oln = old.last_name().lower()
        if ofn == nfn and oln == nln:
            return True
    return False


def first_not_empty(*values):
    return next((v for v in values if v is not None and v.strip()), None)


def fetch_program_participants(report_file=None, verbose=False, drop_dups=True):

    if report_file is None:
        report_file, _ = latest_report('program_participant')
        if report_file is None:
            raise RuntimeError('no program participant report found!')
        if verbose:
            print(
                '[program participant report selected: '
                '{} (realpath={})]'.format(
                    report_file, os.path.realpath(report_file)
                )
            )

    with open(report_file, 'r', newline='') as csvfile:

        roles = {
            'Player': [],
            'Coach': [],
            'Volunteer': [],
        }

        reader = DictReader(csvfile)

        for record in reader:

            p = Participant(record)
            p.program = True

            if p.status() != 'Active':
                if verbose:
                    print('status not Active for {}!'.format(p))
                continue

            role = p.role()
            role_list = roles[role]

            if is_dup(role_list, p) and drop_dups:
                if verbose:
                    print('dup? {}: {}'.format(role, p))
            else:
                role_list.append(p)

    return roles


def fetch_participants(teams, report_file=None, verbose=False, drop_dups=True,
                       player_moves={}):

    if report_file is None:
        report_file1, dt1 = latest_report('participant')
        report_file2, dt2 = latest_report('participants')
        if report_file1 is None and report_file2 is None:
            raise RuntimeError('no participant report found!')
        if report_file1 is None:
            report_file = report_file2
        elif report_file2 is None:
            report_file = report_file1
        else:
            if dt1 > dt2:
                report_file = report_file1
            else:
                report_file = report_file2
        if verbose:
            print(
                '[participant report selected: {} (realpath={})]'.format(
                    report_file, os.path.realpath(report_file)
                )
            )

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for record in reader:

            p = Participant(record)
            p.program = False

            if p.status() != 'Active':
                if verbose:
                    print('status not Active for {}!'.format(p))
                continue

            team_name = p.team_name()
            move_into = player_moves.get(p.full_name(), None)
            if move_into:
                print(
                    'moving {} from {} into {}'.format(
                        p.full_name(), team_name, move_into
                    )
                )
                team_name = move_into
            if not team_name:
                if verbose:
                    print('no team name for {}!'.format(p))
                continue

            t = find_team(teams, edjba_id=team_name)
            if t is None:
                if verbose:
                    print('team name not found for {}!'.format(team_name))
                continue

            role = p.role()
            if role == 'Player':
                if is_dup(t.players, p) and drop_dups:
                    if verbose:
                        print('dup? player in {}: {}'.format(t.sname, p))
                else:
                    t.players.append(p)
            elif role == 'Coach':
                if is_dup(t.coaches, p) and drop_dups:
                    if verbose:
                        print('dup? coach in {}: {}'.format(t.sname, p))
                else:
                    t.coaches.append(p)
            elif role == 'Team Manager':
                if is_dup(t.managers, p) and drop_dups:
                    if verbose:
                        print('dup t/m? in {}: {}'.format(t.sname, p))
                else:
                    t.managers.append(p)
            else:
                raise RuntimeError('Unknown role: {}'.format(role))


def find_in_tb(tb, want_name):

    for name, elist in tb['by-name'].items():

        if name.lower() == want_name.lower():
            entry = elist.pop()
            if len(elist) == 0:
                del tb['by-name'][name]
            tnum = entry['Ticket Number']
            oent = tb['by-tnum'].pop(tnum)[0]
            if oent is not entry:
                raise RuntimeError(
                    'ticket number msimatch! ({}!={})'.format(entry, oent)
                )
            return entry

    return None


def fetch_trybooking(tbmap=None, report_file=None, verbose=False):

    if report_file is None:
        report_file, _ = latest_report(
            'trybooking',
            nre=r'^trybooking_(\d{8}).csv$',
            n2dt=lambda m: datetime.strptime(m.group(1), '%d%m%Y'),
        )
        if report_file is None:
            raise RuntimeError('no trybooking report found!')
        if verbose:
            print(
                '[trybooking report selected: {} (realpath={})]'.format(
                    report_file, os.path.realpath(report_file)
                )
            )

    tb = {}

    with open(report_file, 'r', newline='') as csvfile:

        _ = csvfile.read(1)

        reader = DictReader(csvfile)

        for entry in reader:
            # {
            #  'Booking First Name': 'david',
            #  'Booking Last Name': 'mcnab',
            #  'Booking Address 1': '63 Perry St',
            #  'Booking Address 2': '',
            #  'Booking Suburb': 'Fairfield',
            #  'Booking State': 'Vic',
            #  'Booking Post Code': '3078',
            #  'Booking Country': 'Australia',
            #  'Booking Telephone': ' 0402064630',
            #  'Booking Email': 'david.mcnab@finity.com.au',
            #  'Booking ID': 'e24e3bc7-867c-4cd5-aa00-e8a11a96b94d',
            #  'Number of Tickets': '1',
            #  'Net Booking': '200.00',
            #  'Discount Amount': '0.00',
            #  'Gift Certificates Redeemed': '0.00',
            #  'Processing Fees': '0.00',
            #  'Ticket Fees': '0.00',
            #  'Quicksale Fees': '0.00',
            #  'Quicksale': 'No',
            #  'Date Booked (UTC+11)': '18Feb21',
            #  'Time Booked': '9:15:56 PM',
            #  'Permission to Contact': 'No',
            #  'Donation': '0.00',
            #  'Booking Data: Season': '2020/21 Summer',
            #  'Ticket Type': 'Full Season',
            #  'Ticket Price (AUD)': '200.00',
            #  'Promotion[Discount] Code': '',
            #  'Section': 'Section 1',
            #  'Ticket Number': '2287297-62601549',
            #  'Seat Row': '',
            #  'Seat Number': '0',
            #  'Refunded Misc': '0.0000',
            #  'Ticket Refunded Amount': '0.0000',
            #  'Ticket Status': 'Unrefunded',
            #  'Void': 'No',
            #  'Ticket Data: Player First Name': 'jack',
            #  'Ticket Data: Player Family Name': 'mcnab',
            #  '': ''
            # }
            name = entry['Ticket Data: Player Family Name'] + ',' + \
                entry['Ticket Data: Player First Name']
            if tbmap and name in tbmap:
                mapped_name = tbmap[name]
                if not mapped_name:
                    continue
                if verbose:
                    print(
                        '[mapping name from "{}" to "{}"'.format(
                            name, mapped_name
                        )
                    )
                name = mapped_name
            txid = entry['Booking ID']
            tnum = entry['Ticket Number']

            if to_bool(entry['Void']):
                if verbose:
                    print(
                        '[ignore void ticket: {} - {}, {}]'.format(
                            name, tnum, txid
                        )
                    )
                continue

            tb.setdefault('by-name', {}).setdefault(name, []).append(entry)
            tb.setdefault('by-txid', {}).setdefault(txid, []).append(entry)
            tb.setdefault('by-tnum', {}).setdefault(tnum, []).append(entry)

    return tb


def to_fullname(fn, ln):
    '''make a standard full name from a first name and last name'''
    if fn is None:
        fn = 'None'
    if ln is None:
        ln = 'None'
    return ln + ',' + fn


def to_datetime(s, fmt='%d/%m/%Y'):
    '''convert a string to a datetime object'''
    if s is None:
        return None
    else:
        return datetime.strptime(s.strip(), fmt)


def to_date(s, fmt='%d/%m/%Y'):
    '''convert a string to a date object'''
    dt = to_datetime(s, fmt)
    if dt is None:
        return None
    else:
        return dt.date()


def to_time(s, fmt='%H:%M:%S'):
    '''convert a string to a time object'''
    dt = to_datetime(s, fmt)
    if dt is None:
        return None
    else:
        return dt.time()


_binary_types = (binary_type, bytearray)
_text_types = (text_type, )
_string_types = string_types + _text_types + _binary_types
_numeric_pattern = re.compile(
    r'^[+-]?(inf(inity)?|(\d+(\.\d*)?|(\d*\.)?\d+)(e[+-]?\d+)?)$'
)


def to_bool(value):
    '''convert an object to a boolean'''
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, _string_types):
        if isinstance(value, _binary_types):
            try:
                value = value.decode()
            except UnicodeDecodeError:
                value = ''.join(chr(c) if c < 128 else '\\x%02x' % c
                                for c in value)
        stmp = value.strip().lower()
        if stmp in ('true', 't', 'yes', 'y', 'on'):
            return True
        if stmp in ('false', 'f', 'no', 'n', 'off',
                    '', 'none', 'nil', 'nul', 'null', 'nan'):
            return False
        if stmp.isdigit():
            return (int(stmp) != 0)
        if _numeric_pattern.match(stmp):
            return (float(stmp) != 0.0)
        raise ValueError('cannot convert "{}" to bool!'.format(value))
    if value:
        return True
    else:
        return False


def find_age_group(age_groups, dob):
    '''return age group that a date-of-birth is in'''
    result = None
    for ag, (ss, es) in age_groups.items():
        sd = to_date(ss)
        ed = to_date(es)
        if sd <= dob and (ed is None or dob <= ed):
            if result is not None:
                raise RuntimeError(
                    'dob ({}) in two age groups! ({}, {})'.format(
                        dob, result, ag
                    )
                )
            result = ag
    return result


_POPATTR_NO_DEFAULT = object()  # so that None could be used as a default value


def popattr(obj, name, default=_POPATTR_NO_DEFAULT):
    '''"pop" attribute from obj - see: https://stackoverflow.com/a/19550942'''
    try:
        return obj.__dict__.pop(name)
    except KeyError:
        if default is not _POPATTR_NO_DEFAULT:
            return default
        raise AttributeError('no attribute "%s"'.format(name))
        # or getattr(obj, name) to generate a real AttributeError


postcode2name = {
    3000: 'Melbourne',
    3039: 'Moonee Ponds',
    3057: 'Brunswick East',
    3057: 'Sumner',
    3058: 'Coburg',
    3065: 'Fitzroy',
    3068: 'Clifton Hill',
    3070: 'Northcote',
    3071: 'Thornbury',
    3072: 'Preston',
    3073: 'Reservoir',
    3078: 'Fairfield',
    3078: 'Alphington',
    3079: 'Ivanhoe',
    3079: 'Ivanhoe East',
    3081: 'Heidelberg Heights',
    3081: 'Bellfield',
    3084: 'Eaglemont',
    3085: 'Macleod',
    3085: 'Macleod West',
    3085: 'Yallambie',
    3087: 'Watsonia',
    3101: 'Kew',
    3102: 'East Kew',
    3104: 'Balwyn North',
    3105: 'Bulleen',
    3108: 'Doncaster',
    3126: 'Camberwell East',
    3126: 'Canterbury',
    3128: 'Box Hill South',
    3181: 'Prahran',
    3181: 'Windsor',
    3197: 'Patterson Lakes',
    3197: 'Carrum',
    3206: 'Albert Park',
    3752: 'South Morang',
    8011: 'Little Lonsdale St, Vic',
    3006: 'Southbank',
    3029: 'Hoppers Crossing',
    2203: 'Dulwich Hill',
}
name2postcode = {name: postcode for postcode, name in postcode2name.items()}


def make_address(addr1, addr2, suburb, postcode):
    a1 = addr1.strip().lower()
    a2 = addr2.strip().lower()
    a3 = suburb.strip().lower() + ', ' + str(postcode)
    return '\n'.join(a for a in [a1, a2, a3] if a)


def make_phone(inphone):
    s = inphone.strip()
    if s == '':
        return ''
    if s.startswith('+'):
        s = s[1:]
    if s.startswith('61'):
        s = '0' + s[2:]
    if not s.startswith('0'):
        s = '0' + s
    return s


def end_of_season():
    today = date.today()
    end_of_summer = date(today.year, 3, 31)  # near enough is good enough
    if today <= end_of_summer:
        return end_of_summer
    end_of_winter = date(today.year, 9, 30)  # near enough is good enough
    if today <= end_of_winter:
        return end_of_winter
    return date(today.year + 1, 3, 31)


def is_under18(date_of_birth):
    diff = relativedelta(end_of_season(), date_of_birth)
    return (diff.years < 18)


_wwc_url = 'https://online.justice.vic.gov.au/wwccu/checkstatus.doj'

_wwc_post_data = {
    'viewSequence': 1,
    'language': 'en',
    'cardnumber': None,
    'lastname': None,
    'pageAction': 'Submit',
    'Submit': 'submit',
}

_wwc_post_headers = {
    'Cache-Control': 'no-cache, no-store, max-age=0',
    'Expires': '0',
}

_wwc_number_pattern = re.compile(r'^(\d{7}(\d|A))(-\d{1,2})?$', re.I)

_wwc_result_pattern = re.compile(
    r'^('
    '(Working.*expires on (\d{2}) ([A-Z][a-z]{2}) (\d{4})\.)'
    '|'
    '(Working.*no longer current(.*has a new card that is current)?.*)'
    '|'
    '(This family.*do not match.*)'
    ')$'
)

_wwc_check_cache = {}
_wwc_check_session = None
_wwc_check_lock = Lock()


WWCCheckStatus = IntEnum(
    'WWCCheckStatus',
    ' '.join(
        [
            'NONE', 'UNKNOWN', 'EMPTY', 'UNDER18', 'TEACHER', 'BADNUMBER',
            'FAILED', 'SUCCESS', 'CHANGED', 'EXPIRED', 'INVALID', 'BADRESPONSE'
        ]
    )
)


class WWCCheckPerson(object):
    '''details of a person requiring a Working With Children check'''

    def __init__(self, ident, name, number, dob, checkname=None, *args, **kwds):
        super(WWCCheckPerson, self).__init__(*args, **kwds)

        self.ident = ident
        self.name = name
        self.number = number
        self.dob = dob
        self.checkname = checkname

    def __str__(self):
        return '[wwc check person: {},{},{},{},{}]'.format(
            self.ident, self.name, self.number, self.dob, self.checkname
        )


class WWCCheckResult(object):
    '''the result of a Working With Children check'''

    def __init__(self, status, message, expiry, *args, **kwds):
        super(WWCCheckResult, self).__init__(*args, **kwds)

        self.status = status
        self.message = message
        self.expiry = expiry

    def __str__(self):
        return '[wwc check result: {},{},{}]'.format(
            self.status, self.message, self.expiry
        )


class _TLSAdapter(HTTPAdapter):
    '''see: https://stackoverflow.com/a/61643770/2130789'''
    '''also: https://stackoverflow.com/a/76217135'''

    def init_poolmanager(self, connections, maxsize, block=False):
        '''Create and initialize the urllib3 PoolManager.'''
        ctx = create_urllib3_context(ciphers='ALL:@SECLEVEL=0')
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
        )


def wwc_check(person, verbose=False, nocache=False):

    if person is None or person.ident is None or person.name is None:
        return WWCCheckResult(
            WWCCheckStatus.NONE,
            'Skipping - invalid person {}'.format(person),
            None
        )

    ident = person.ident
    if not nocache and ident in _wwc_check_cache:
        return _wwc_check_cache[ident]
    if person.checkname is not None:
        name = ensure_text(person.checkname)
        if verbose:
            print(
                '[Using {} for name instead of {}]'.format(
                    person.checkname, person.name
                )
            )
    else:
        name = ensure_text(person.name)
    wwcn = person.number

    if ident == 0:
        _wwc_check_cache[ident] = WWCCheckResult(
            WWCCheckStatus.UNKNOWN,
            'Skipping - Placeholder ID',
            None
        )
        return _wwc_check_cache[ident]

    if person.dob is not None and is_under18(person.dob):
        _wwc_check_cache[ident] = WWCCheckResult(
            WWCCheckStatus.UNDER18,
            'Skipping - Under 18 (DoB: {})'.format(person.dob),
            None
        )
        return _wwc_check_cache[ident]

    if wwcn is None or wwcn == '':
        _wwc_check_cache[ident] = WWCCheckResult(
            WWCCheckStatus.EMPTY,
            'Skipping - Empty WWC Number',
            None
        )
        return _wwc_check_cache[ident]

    m = _wwc_number_pattern.match(wwcn)

    if m is None:
        if wwcn.startswith('VIT'):
            _wwc_check_cache[ident] = WWCCheckResult(
                WWCCheckStatus.TEACHER,
                'Skipping - Victorian Teacher ({})'.format(wwcn),
                None
            )
        else:
            _wwc_check_cache[ident] = WWCCheckResult(
                WWCCheckStatus.BADNUMBER,
                'Skipping - Bad WWC Number ({})'.format(wwcn),
                None
            )
        return _wwc_check_cache[ident]

    cardnumber = m.group(1).upper()
    lastname = '%20'.join(name.split()[1:])
    postdata = dict(_wwc_post_data)
    postdata['cardnumber'] = cardnumber
    postdata['lastname'] = lastname

    with _wwc_check_lock:
        # based on: https://stackoverflow.com/a/61643770/2130789
        global _wwc_check_session
        if _wwc_check_session is None:
            _wwc_check_session = Session()
            _wwc_check_session.mount(_wwc_url, _TLSAdapter())
        try:
            res = _wwc_check_session.post(
                _wwc_url, postdata, headers=_wwc_post_headers
            )
        except Exception as e:
            _wwc_check_cache[ident] = WWCCheckResult(
                WWCCheckStatus.FAILED,
                'Exception during Web Transaction: {}'.format(e),
                None
            )
            return _wwc_check_cache[ident]

    if res.status_code != 200:
        _wwc_check_cache[ident] = WWCCheckResult(
            WWCCheckStatus.FAILED,
            'Web Transaction Failed with status {}!'.format(res.status_code),
            None
        )
        return _wwc_check_cache[ident]
    contents = res.text

    for line in contents.splitlines():

        m = _wwc_result_pattern.match(line)
        if not m:
            continue

        success, notcurrent, changed, notvalid = m.group(2, 6, 7, 8)

        if notcurrent:
            if verbose:
                print('notcurrent response = {}'.format(notcurrent))
            if changed:
                _wwc_check_cache[ident] = WWCCheckResult(
                    WWCCheckStatus.CHANGED,
                    'WWC Number ({}) has Changed'.format(wwcn),
                    None
                )
            else:
                _wwc_check_cache[ident] = WWCCheckResult(
                    WWCCheckStatus.EXPIRED,
                    'WWC Number ({}) has Expired'.format(wwcn),
                    None
                )
            return _wwc_check_cache[ident]

        if notvalid:
            if verbose:
                print('notvalid response = {}'.format(notvalid))
            _wwc_check_cache[ident] = WWCCheckResult(
                WWCCheckStatus.EXPIRED,
                'WWC Number ({}) with Lastname ({}) NOT VALID'
                .format(wwcn, lastname),
                None
            )
            return _wwc_check_cache[ident]

        if success is not None:
            if verbose:
                print('success response = {}'.format(success))
            _wwc_check_cache[ident] = WWCCheckResult(
                WWCCheckStatus.SUCCESS,
                'WWC Check Succeeded',
                date(*time.strptime('-'.join(m.group(5, 4, 3)), '%Y-%b-%d')[:3])
            )
            return _wwc_check_cache[ident]

    if verbose:
        print('bad response = {}'.format(contents))
    _wwc_check_cache[ident] = WWCCheckResult(
        WWCCheckStatus.BADRESPONSE,
        'WWC Check Service returned BAD response',
        None
    )
    return _wwc_check_cache[ident]
