'''
Created on 7 Jul. 2018

@author: jen117
'''
from collections import Mapping, namedtuple
from datetime import date
from enum import IntEnum
import json
from logging import getLogger
import os
import re
from sqlalchemy.ext.automap import automap_base
import urllib2

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from sbcilib.utils import SbciEnum


_logger = getLogger(__name__)
_config = {
    'db_file':     'teams.sqlite3',  # leave out if no file backing db
    'db_url':      'sqlite:///teams.sqlite3',
    'wwc_url_fmt': 'https://online.justice.vic.gov.au/wwccu/checkstatus.doj'
                   '?viewSequence=1&cardnumber={}&lastname={}'
                   '&pageAction=Submit&Submit=submit',
}


WWCCheckStatus = IntEnum('WWCCheckStatus', ' '.join([
    'UNKNOWN', 'EMPTY', 'UNDER18', 'TEACHER', 'BADNUMBER',
    'FAILED', 'SUCCESS', 'EXPIRED', 'INVALID', 'BADRESPONSE'
]))


WWCCheckResult = namedtuple('WWCCheckResult', ['status', 'message', 'expiry'])


class PersonRole(SbciEnum):
    '''TODO'''

    COACH = 1, 'Coach'
    ASSISTANT_COACH = 2, 'Assistant Coach'
    TEAM_MANAGER = 3, 'Team Manager'


class SbciTeamsDB(object):
    '''TODO'''

    def __init__(self, verbose=False, *args, **kwds):
        super(SbciTeamsDB, self).__init__(*args, **kwds)

        try:
            with open('config.json', 'r') as fd:
                contents = json.load(fd)
                if isinstance(contents, Mapping):
                    _config.update(contents)
                elif verbose:
                    _logger.error('contents of "config.json" are unsuitable!')
        except (IOError, ValueError) as e:
            if verbose > 1:
                _logger.warning('exception reading "config.json": %s', str(e))

        self.Base = automap_base()

        if 'db_file' in _config:
            db_file = _config['db_file']
            if not os.access(db_file, os.R_OK | os.W_OK):
                raise RuntimeError('cannot access DB file ({}) for R/W!'
                                   .format(db_file))

        self.engine = create_engine(_config['db_url'])

        self.Base.prepare(self.engine, reflect=True)

        self.Competitions = self.Base.classes.competitions
        self.People = self.Base.classes.people
        self.Venues = self.Base.classes.venues
        self.Teams = self.Base.classes.teams
        self.Sessions = self.Base.classes.sessions

        self.dbsession = Session(self.engine)

        self.competitions_query = self.dbsession.query(self.Competitions)
        self.people_query = self.dbsession.query(self.People)
        self.venues_query = self.dbsession.query(self.Venues)
        self.teams_query = self.dbsession.query(self.Teams)
        self.sessions_query = self.dbsession.query(self.Sessions)

        self._wwc_checked = {}

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

    def person_check_wwc(self, person, verbose=0):
        '''TODO'''

        id = person.id  # @ReservedAssignment
        if id in self._wwc_checked:
            return self._wwc_checked[id]
        name = person.name.encode('utf8')
        wwcn = person.wwc_number

        if id == 0:
            self._wwc_checked[id] = WWCCheckResult(
                WWCCheckStatus.UNKNOWN,
                'Skipping - Placeholder ID',
                None
            )
            return self._wwc_checked[id]

        if wwcn == '':
            self._wwc_checked[id] = WWCCheckResult(
                WWCCheckStatus.EMPTY,
                'Skipping - Empty WWC Number',
                None
            )
            return self._wwc_checked[id]

        m = SbciTeamsDB._wwc_number_pattern.match(wwcn)

        if m is None:
            if wwcn == 'Under 18':
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.UNDER18,
                    'Skipping - Under 18 (DoB: {})'.format(person.dob),
                    None
                )
            elif wwcn.startswith('VIT'):
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.TEACHER,
                    'Skipping - Victorian Teacher ({})'.format(wwcn),
                    None
                )
            else:
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.BADNUMBER,
                    'Skipping - Bad WWC Number ({})'.format(wwcn),
                    None
                )
            return self._wwc_checked[id]

        cardnumber = m.group(1).upper()
        lastname = '%20'.join(name.split()[1:])

        try:
            wwc_url = _config['wwc_url_fmt'].format(cardnumber, lastname)
            contents = urllib2.urlopen(wwc_url).read()
        except BaseException:
            self._wwc_checked[id] = WWCCheckResult(
                WWCCheckStatus.TEACHER,
                'Web Transaction Failed!',
                None
            )
            return self._wwc_checked[id]

        for line in contents.splitlines():

            m = SbciTeamsDB._wwc_result_pattern.match(line)
            if not m:
                continue

            success, expired, notvalid = m.group(2, 6, 7)

            if success is not None:
                if verbose > 1:
                    print('success response = {}'.format(success))
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.SUCCESS,
                    'WWC Check Succeeded',
                    '-'.join(m.group(5, 4, 3))
                )
                return self._wwc_checked[id]

            if expired:
                if verbose > 1:
                    print('expired response = {}'.format(expired))
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.EXPIRED,
                    'WWC Number ({}) has Expired'.format(wwcn),
                    None
                )
                return self._wwc_checked[id]

            if notvalid:
                if verbose > 1:
                    print('notvalid response = {}'.format(notvalid))
                self._wwc_checked[id] = WWCCheckResult(
                    WWCCheckStatus.EXPIRED,
                    'WWC Number ({}) with Lastname ({}) NOT VALID'
                    .format(wwcn, lastname),
                    None
                )
                return self._wwc_checked[id]

        if verbose > 1:
            print('bad response = {}'.format(contents))
        self._wwc_checked[id] = WWCCheckResult(
            WWCCheckStatus.BADRESPONSE,
            'WWC Check Service returned BAD response',
            None
        )
        return self._wwc_checked[id]

    def competition_shortname(self, competition):
        '''TODO'''
        if competition.gender == 'F':
            gender = 'G'
        else:
            gender = 'B'
        return str(competition.age_group) + gender + str(competition.section)

    def competition_longname(self, competition):
        '''TODO'''
        if competition.gender == 'F':
            gender = 'Girls'
        else:
            gender = 'Boys'
        return 'Under ' + str(competition.age_group) + ' ' + gender + \
               ' Section ' + str(competition.section)

    def end_of_season(self):
        '''TODO'''
        today = date.today()
        end_of_summer = date(today.year, 3, 31)  # near enough is good enough
        if today <= end_of_summer:
            return end_of_summer
        end_of_winter = date(today.year, 9, 30)  # near enough is good enough
        if today <= end_of_winter:
            return end_of_winter
        return date(today.year + 1, 3, 31)
