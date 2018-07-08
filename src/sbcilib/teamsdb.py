'''
Created on 7 Jul. 2018

@author: jen117
'''
from collections import Mapping
import json
from logging import getLogger
import os
import re
import urllib2

from sqlalchemy.engine import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import Session


_logger = getLogger(__name__)
_config = {
    'db_file':     'teams.sqlite3',  # leave out if no file backing db
    'db_url':      'sqlite:///teams.sqlite3',
    'wwc_url_fmt': 'https://online.justice.vic.gov.au/wwccu/checkstatus.doj'
                   '?viewSequence=1&cardnumber={}&lastname={}'
                   '&pageAction=Submit&Submit=submit',
    'wwc_num_re':  '^(\\d{7}(\\d|[Aa]))(-\\d{1,2})?$',
    'wwc_skip_re': '^(|Under\\s*18|VIT\\s*\\d{6}|N/A|[Pp]ending)$',
    'wwc_res_re':  '^('
                   '(Working.*expires on (\\d{2}) ([A-Z][a-z]{2}) (\\d{4})\.)'
                   '|'
                   '(Working.*no longer current.*)'
                   '|'
                   '(This family.*do not match.*)'
                   ')$',
    'wwc_res_inds': [2, 6, 7],
    'wwc_exp_inds': [5, 4, 3],
}


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

    def person_check_wwc(self, person, verbose=0):
        '''TODO'''

        id = person.id  # @ReservedAssignment
        if id in self._wwc_checked:
            return self._wwc_checked[id]
        name = person.name.encode('utf8')
        wwcn = person.wwc_number

        if id == 0:
            self._wwc_checked[id] = (
                True,
                'Skipping placeholder person "{}"'.format(name),
                None
            )
            return self._wwc_checked[id]

        m = re.match(_config['wwc_num_re'], wwcn)
        if not m:
            if not re.match(_config['wwc_skip_re'], wwcn):
                self._wwc_checked[id] = (
                    False,
                    'Bad wwc card number for {}: {}'.format(name, wwcn),
                    None
                )
                return self._wwc_checked[id]
            else:
                self._wwc_checked[id] = (
                    True,
                    'Skip wwc card number for {}: {}'.format(name, wwcn),
                    None
                )
                return self._wwc_checked[id]

        cardnumber = m.group(1).upper()
        lastname = '%20'.join(name.split()[1:])

        wwc_url = _config['wwc_url_fmt'].format(cardnumber, lastname)
        contents = urllib2.urlopen(wwc_url).read()

        for line in contents.splitlines():

            m = re.match(_config['wwc_res_re'], line)
            if not m:
                continue

            success, expired, notvalid = m.group(*_config['wwc_res_inds'])

            if success:
                if verbose > 1:
                    print('success response = {}'.format(success))
                self._wwc_checked[id] = (
                    True,
                    'WWC number for ({},{}) is valid ({}, {}, {})'
                    .format(cardnumber, lastname,
                            name, person.mobile, person.email),
                    '-'.join(m.group(*_config['wwc_exp_inds']))
                )
                return self._wwc_checked[id]

            if expired:
                if verbose > 1:
                    print('expired response = {}'.format(expired))
                self._wwc_checked[id] = (
                    False,
                    'WWC number for ({},{}) has EXPIRED! ({}, {}, {})'
                    .format(cardnumber, lastname,
                            name, person.mobile, person.email),
                    None
                )
                return self._wwc_checked[id]

            if notvalid:
                if verbose > 1:
                    print('notvalid response = {}'.format(notvalid))
                self._wwc_checked[id] = (
                    False,
                    'WWC number for ({},{}) is NOT VALID! ({}, {}, {})'
                    .format(cardnumber, lastname,
                            name, person.mobile, person.email),
                    None
                )
                return self._wwc_checked[id]

        if verbose > 1:
            print('bad response = {}'.format(contents))
        self._wwc_checked[id] = (
            False,
            'Bad http response from url "{}"'.format(wwc_url),
            None
        )
        return self._wwc_checked[id]

    def competition_shortname(self, competition):
        '''TODO'''
        if competition.gender is 'F':
            gender = 'G'
        else:
            gender = 'B'
        return str(competition.age_group) + gender + str(competition.section)

    def competition_longname(self, competition):
        '''TODO'''
        if competition.gender is 'F':
            gender = 'Girls'
        else:
            gender = 'Boys'
        return 'Under ' + str(competition.age_group) + ' ' + gender + \
               ' Section ' + str(competition.section)
