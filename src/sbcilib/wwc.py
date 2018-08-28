'''
Created on 28 Aug. 2018

@author: jen117
'''
from datetime import date
import re
from time import strptime
import urllib2

from enum import IntEnum

from sbcilib.utils import is_under18


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


class WWCCheckResult(object):

    def __init__(self, status, message, expiry, *args, **kwds):
        super(WWCCheckResult, self).__init__(*args, **kwds)

        self.status = status
        self.message = message
        self.expiry = expiry


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
