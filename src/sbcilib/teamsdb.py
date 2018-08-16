'''
Created on 7 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from collections import namedtuple
from datetime import date
import os
import re
from sqlalchemy import event
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.automap import automap_base
from time import strptime
import urllib2

from dateutil.relativedelta import relativedelta
from enum import IntEnum
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from sbcilib.utils import SbciEnum, end_of_season


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    # Will force sqlite constraint foreign keys

    # print('_set_sqlite_pragma: enabling foreign keys, conn={}, rec={}'
    #       .format(dbapi_connection, connection_record), file=sys.stderr)
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


def _classname_for_table(_base, tablename, _table):
    # print('classname_for_table: base={}, tablename={}, table={}'
    #       .format(base.__name__, tablename, table), file=sys.stderr)
    return str(tablename)


def _name_for_scalar_relationship(_base, _local_cls, referred_cls, constraint):
    # print('name_for_scalar_relationship: '
    #       'base={}, local_cls={}, referred_cls={}, constraint={}'
    #       .format(base.__name__, local_cls.__name__,
    #               referred_cls.__name__, constraint), file=sys.stderr)
    # print('constraint.column_keys={}'.format(constraint.column_keys),
    #       file=sys.stderr)
    # return referred_cls.__name__.lower()
    id_col = constraint.column_keys[0]
    if not id_col.endswith('_id'):
        return referred_cls.__name__.lower()
    return id_col[:-3]


def _name_for_collection_relationship(
        _base, _local_cls, referred_cls, constraint):
    # print('name_for_collection_relationship: '
    #       'base={}, local_cls={}, referred_cls={}, constraint={}'
    #       .format(base.__name__, local_cls.__name__,
    #               referred_cls.__name__, constraint), file=sys.stderr)
    # print('constraint.column_keys={}'.format(constraint.column_keys),
    #       file=sys.stderr)
    # return referred_cls.__name__.lower() + "_collection"
    id_col = constraint.column_keys[0]
    if not id_col.endswith('_id'):
        return referred_cls.__name__.lower() + '_collection'
    return id_col[:-3] + '_collection'


class TeamRole(SbciEnum):
    '''TODO'''
    COACH = 1, 'Coach'
    ASSISTANT_COACH = 2, 'Assistant Coach'
    TEAM_MANAGER = 3, 'Team Manager'


class SbciTeamsDB(object):
    '''TODO'''

    TEAMSDB_FILE = \
        os.getenv('HOME') + \
        '/basketball/shooters/SportsTG/2018-winter/teams.sqlite3'

    def __init__(self, verbose=False, *args, **kwds):
        super(SbciTeamsDB, self).__init__(*args, **kwds)

        if not os.access(SbciTeamsDB.TEAMSDB_FILE, os.R_OK | os.W_OK):
            raise RuntimeError('cannot access DB file ({}) for R/W!'
                               .format(SbciTeamsDB.TEAMSDB_FILE))

        self.Base = automap_base()

        self.engine = create_engine('sqlite:///' + SbciTeamsDB.TEAMSDB_FILE)

        self.Base.prepare(
            self.engine, reflect=True,
            classname_for_table=_classname_for_table,
            name_for_scalar_relationship=_name_for_scalar_relationship,
            name_for_collection_relationship=_name_for_collection_relationship
        )

        self.Competitions = self.Base.classes.competitions
        self.People = self.Base.classes.people
        self.Venues = self.Base.classes.venues
        self.Teams = self.Base.classes.teams
        self.Sessions = self.Base.classes.sessions

        if verbose > 1:
            for cls in (self.Competitions, self.People, self.Venues,
                        self.Teams, self.Sessions):
                print('{} = {}'.format(cls.__name__, dir(cls)))

        self.dbsession = Session(self.engine)

        self.competitions_query = self.dbsession.query(self.Competitions)
        self.people_query = self.dbsession.query(self.People)
        self.venues_query = self.dbsession.query(self.Venues)
        self.teams_query = self.dbsession.query(self.Teams)
        self.sessions_query = self.dbsession.query(self.Sessions)


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


WWCCheckStatus = IntEnum('WWCCheckStatus', ' '.join([
    'NONE', 'UNKNOWN', 'EMPTY', 'UNDER18', 'TEACHER', 'BADNUMBER',
    'FAILED', 'SUCCESS', 'EXPIRED', 'INVALID', 'BADRESPONSE'
]))


class WWCCheckResult(namedtuple('WWCCheckResult',
                                ['status', 'message', 'expiry'])):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(WWCCheckResult, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def wwc_check(person, verbose=0):
    '''TODO'''

    if person is None:
        return WWCCheckResult(
            WWCCheckStatus.NONE,
            'Skipping - Value is None',
            None
        )

    id = person.id  # @ReservedAssignment
    if id in _wwc_check_cache:
        return _wwc_check_cache[id]
    name = person.name.encode('utf8')
    wwcn = person.wwc_number

    if id == 0:
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.UNKNOWN,
            'Skipping - Placeholder ID',
            None
        )
        return _wwc_check_cache[id]

    if is_under18(person):
        _wwc_check_cache[id] = WWCCheckResult(
            WWCCheckStatus.UNDER18,
            'Skipping - Under 18 (DoB: {})'.format(person.dob.date()),
            None
        )
        return _wwc_check_cache[id]

    if wwcn == '':
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


def is_under18(person):
    '''TODO'''
    diff = relativedelta(end_of_season(), person.dob)
    return (diff.years < 18)


def competition_shortname(competition):
    '''TODO'''
    if competition.gender == 'F':
        gender = 'G'
    else:
        gender = 'B'
    return str(competition.age_group) + gender + str(competition.section)


def competition_longname(competition):
    '''TODO'''
    if competition.gender == 'F':
        gender = 'Girls'
    else:
        gender = 'Boys'
    return 'Under ' + str(competition.age_group) + ' ' + gender + \
           ' Section ' + str(competition.section)
