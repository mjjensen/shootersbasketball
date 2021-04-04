from collections import OrderedDict
from csv import DictReader
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from enum import unique, IntEnum
from glob import glob
from json import loads
import os
import re
from six import string_types
from sqlite3 import connect, Row
from time import strftime


#season = os.getenv('SEASON', '2021-summer')
season = os.getenv('SEASON', '2021-winter')
provider = os.getenv('PROVIDER', 'PlayHQ')
shootersdir = os.getenv(
    'SHOOTERSDIR',
    os.path.join(os.getenv('HOME', '.'), 'basketball', 'shooters')
)
seasondir = os.getenv(
    'SEASONDIR',
    os.path.join(shootersdir, provider, season)
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
    ('tm.name',           'tm_name'),
    ('tm.email',          'tm_email'),
    ('tm.mobile',         'tm_mobile'),
    ('tm.wwc_number',     'tm_wwcnum'),
    ('tm.wwc_expiry',     'tm_wwcexp'),
    ('co.name',           'co_name'),
    ('co.email',          'co_email'),
    ('co.mobile',         'co_mobile'),
    ('co.wwc_number',     'co_wwcnum'),
    ('co.wwc_expiry',     'co_wwcexp'),
    ('co.postal_address', 'co_address'),
    ('ac.name',           'ac_name'),
    ('ac.email',          'ac_email'),
    ('ac.mobile',         'ac_mobile'),
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
    ORDER BY gender, age_group, team_number, team_name
'''.format(', '.join(map(lambda elem: elem[0], sql_attr_map)))


def fetch_teams(teamsfile='teams.sqlite3'):
    if not os.path.exists(teamsfile):
        teamsfile = os.path.join(seasondir, teamsfile)
        if not os.path.exists(teamsfile):
            raise RuntimeError('cannot locate teams sqlite database')

    conn = connect(teamsfile)
    conn.row_factory = Row

    try:
        cursor = conn.cursor()

        rows = cursor.execute(sql_query)

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


def load_config(filename='config.json'):
    config = {}
    if not os.path.exists(filename):
        filename = os.path.join(seasondir, filename)
    if os.path.exists(filename):
        with open(filename, 'rb') as cfd:
            config.update(loads(cfd.read().decode()))
    return config


def latest_report(rtype, rdir='reports', nre=None, n2dt=None, verbose=False):
    '''find the latest report file of a certain type'''

    if nre is None:
        nre = r'^' + rtype + r'_(\d{8})(\d+)\.csv$'
    if n2dt is None:
        n2dt = lambda m: datetime.strptime(
            '{:08d}{:06d}'.format(*map(int, m.groups())), '%Y%m%d%H%M%S'
        )

    p = re.compile(nre)
    latest = None, None

    if not os.path.isdir(rdir):
        rdir = os.path.join(seasondir, rdir)
        if not os.path.isdir(rdir):
            raise RuntimeError('cannot find report dir ({})'.format(rdir))

    # os.walk() returns generator that walks the directory tree; next() on
    # the generator will return the first level (i.e. rdir contents) as a
    # triple (root, dirnames, filenames)
    for name in next(os.walk(rdir))[2]:

        m = p.match(name)
        if m is None:
            if verbose:
                print('re mismatch for file name: {}'.format(name))
            continue

        dt = n2dt(m)

        lpath, ldt = latest
        if not ldt or dt > ldt:
            latest = os.path.join(rdir, name), dt

    return latest


def is_dup(curlist, new):
    nfn = new['first name'].strip().lower()
    nln = new['last name'].strip().lower()
    for old in curlist:
        ofn = old['first name'].strip().lower()
        oln = old['last name'].strip().lower()
        if ofn == nfn and oln == nln:
            return True
    return False


def pn(participant):
    return participant['last name'] + ', ' + participant['first name']


def fetch_participants(teams, report_file=None, verbose=False, drop_dups=True):

    if report_file is None:
        report_file, _ = latest_report('participant')
        if report_file is None:
            raise RuntimeError('no participant report found!')
        if verbose:
            print('[participant report selected: {}]'.format(report_file))

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for participant in reader:

            if participant['status'] != 'Active':
                if verbose:
                    print('status not Active for {}!'.format(pn(participant)))
                continue

            team_name = participant['team name']
            if not team_name:
                if verbose:
                    print('no team name for {}!'.format(pn(participant)))
                continue

            t = find_team(teams, edjba_id=team_name)
            if t is None:
                if verbose:
                    print('team name not found for {}!'.format(team_name))
                continue

            role = participant['role']
            if role == 'Player':
                if is_dup(t.players, participant):
                    if verbose:
                        print(
                            'dup? player in {}: {}'.format(
                                t.sname, pn(participant)
                            )
                        )
                else:
                    t.players.append(participant)
            elif role == 'Coach':
                if is_dup(t.coaches, participant):
                    if verbose:
                        print(
                            'dup? coach in {}: {}'.format(
                                t.sname, pn(participant)
                            )
                        )
                else:
                    t.coaches.append(participant)
            elif role == 'Team Manager':
                if is_dup(t.managers, participant):
                    if verbose:
                        print(
                            'dup t/m? in {}: {}'.format(
                                t.sname, pn(participant)
                            )
                        )
                else:
                    t.managers.append(participant)
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


def fetch_trybooking(teams, tbmap=None, report_file=None, verbose=False):

    if report_file is None:
        report_file, _ = latest_report(
            'trybooking',
            nre=r'^trybooking_(\d{8}).csv$',
            n2dt=lambda m: datetime.strptime(m.group(1), '%d%m%Y'),
        )
        if report_file is None:
            raise RuntimeError('no trybooking report found!')
        if verbose:
            print('[trybooking report selected: {}]'.format(report_file))

    tb = {}

    with open(report_file, 'r', newline='') as csvfile:

        uchar = csvfile.read(1)

        reader = DictReader(csvfile)

        for entry in reader:

            # {'Booking First Name': 'david', 'Booking Last Name': 'mcnab', 'Booking Address 1': '63 Perry St', 'Booking Address 2': '', 'Booking Suburb': 'Fairfield', 'Booking State': 'Vic', 'Booking Post Code': '3078', 'Booking Country': 'Australia', 'Booking Telephone': ' 0402064630', 'Booking Email': 'david.mcnab@finity.com.au', 'Booking ID': 'e24e3bc7-867c-4cd5-aa00-e8a11a96b94d', 'Number of Tickets': '1', 'Net Booking': '200.00', 'Discount Amount': '0.00', 'Gift Certificates Redeemed': '0.00', 'Processing Fees': '0.00', 'Ticket Fees': '0.00', 'Quicksale Fees': '0.00', 'Quicksale': 'No', 'Date Booked (UTC+11)': '18Feb21', 'Time Booked': '9:15:56 PM', 'Permission to Contact': 'No', 'Donation': '0.00', 'Booking Data: Season': '2020/21 Summer', 'Ticket Type': 'Full Season', 'Ticket Price (AUD)': '200.00', 'Promotion[Discount] Code': '', 'Section': 'Section 1', 'Ticket Number': '2287297-62601549', 'Seat Row': '', 'Seat Number': '0', 'Refunded Misc': '0.0000', 'Ticket Refunded Amount': '0.0000', 'Ticket Status': 'Unrefunded', 'Void': 'No', 'Ticket Data: Player First Name': 'jack', 'Ticket Data: Player Family Name': 'mcnab', '': ''}
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


def to_date(s):
    '''convert a string to a date object'''
    if s is None:
        return None
    else:
        return datetime.strptime(s, '%d/%m/%Y').date()


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
name2postcode = { name: postcode for postcode, name in postcode2name.items() }


def make_address(addr1, addr2, suburb, postcode):
    a1 = addr1.strip().lower()
    a2 = addr2.strip().lower()
    a3 = suburb.strip().lower() + ', ' + str(postcode)
    return '\n'.join(a for a in [a1, a2, a3] if a)


def make_phone(inphone):
    s = inphone.strip()
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


_wwc_url_fmt = 'https://online.justice.vic.gov.au/wwccu/checkstatus.doj' \
               '?viewSequence=1&cardnumber={}&lastname={}' \
               '&pageAction=Submit&Submit=submit'

_wwc_number_pattern = re.compile(r'^(\d{7}(\d|A))(-\d{1,2})?$', re.I)

_wwc_result_pattern = re.compile(
    r'^('
    '(Working.*expires on (\d{2}) ([A-Z][a-z]{2}) (\d{4})\.)'
    '|'
    '(Working.*no longer current.*)'
    '|'
    '(This family.*do not match.*)'
    ')$'
)

_wwc_check_cache = {}


WWCCheckStatus = IntEnum(
    'WWCCheckStatus',
    ' '.join(
        [
            'NONE', 'UNKNOWN', 'EMPTY', 'UNDER18', 'TEACHER', 'BADNUMBER',
            'FAILED', 'SUCCESS', 'EXPIRED', 'INVALID', 'BADRESPONSE'
        ]
    )
)


class WWCCheckResult(object):

    def __init__(self, status, message, expiry, *args, **kwds):
        super(WWCCheckResult, self).__init__(*args, **kwds)

        self.status = status
        self.message = message
        self.expiry = expiry


def wwc_check(person, verbose=0):

    if person is None:
        return WWCCheckResult(
            WWCCheckStatus.NONE,
            'Skipping - Value is None',
            None
        )

    id = person.id  # @ReservedAssignment
    if id in _wwc_check_cache:
        return _wwc_check_cache[id]
    name = person.name.encode('utf-8')
    wwcn = person.wwc_number

    if id == 0:
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.UNKNOWN,
            'Skipping - Placeholder ID',
            None
        )
        return _wwc_check_cache[id]

    if is_under18(person.dob):
        if person.dob is None:
            dob_date = '<unknown>'
        else:
            dob_date = person.dob.date()
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.UNDER18,
            'Skipping - Under 18 (DoB: {})'.format(dob_date),
            None
        )
        return _wwc_check_cache[id]

    if wwcn is None or wwcn == '':
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.EMPTY,
            'Skipping - Empty WWC Number',
            None
        )
        return _wwc_check_cache[id]

    m = _wwc_number_pattern.match(wwcn)

    if m is None:
        if wwcn.startswith('VIT'):
            _wwc_check_cache[id] = WWCCheckResult(
                WWCCheckStatus.TEACHER,
                'Skipping - Victorian Teacher ({})'.format(wwcn),
                None
            )
        else:
            _wwc_check_cache[id] = WWCCheckResult(
                WWCCheckStatus.BADNUMBER,
                'Skipping - Bad WWC Number ({})'.format(wwcn),
                None
            )
        return _wwc_check_cache[id]

    cardnumber = m.group(1).upper()
    lastname = '%20'.join(name.split()[1:])

    try:
        wwc_url = _wwc_url_fmt.format(cardnumber, lastname)
        contents = urllib2.urlopen(wwc_url).read()
    except BaseException:
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.TEACHER,
            'Web Transaction Failed!',
            None
        )
        return _wwc_check_cache[id]

    for line in contents.splitlines():

        m = _wwc_result_pattern.match(line)
        if not m:
            continue

        success, expired, notvalid = m.group(2, 6, 7)

        if expired:
            if verbose > 1:
                print('expired response = {}'.format(expired))
            _wwc_check_cache[id] = WWCCheckResult(
                WWCCheckStatus.EXPIRED,
                'WWC Number ({}) has Expired'.format(wwcn),
                None
            )
            return _wwc_check_cache[id]

        if notvalid:
            if verbose > 1:
                print('notvalid response = {}'.format(notvalid))
            _wwc_check_cache[id] = WWCCheckResult(
                WWCCheckStatus.EXPIRED,
                'WWC Number ({}) with Lastname ({}) NOT VALID'
                .format(wwcn, lastname),
                None
            )
            return _wwc_check_cache[id]

        if success is not None:
            if verbose > 1:
                print('success response = {}'.format(success))
            _wwc_check_cache[id] = WWCCheckResult(
                WWCCheckStatus.SUCCESS,
                'WWC Check Succeeded',
                date(*strptime('-'.join(m.group(5, 4, 3)), '%Y-%b-%d')[:3])
            )
            return _wwc_check_cache[id]

    if verbose > 1:
        print('bad response = {}'.format(contents))
    _wwc_check_cache[id] = WWCCheckResult(
        WWCCheckStatus.BADRESPONSE,
        'WWC Check Service returned BAD response',
        None
    )
    return _wwc_check_cache[id]
