'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from collections import namedtuple
from datetime import datetime, date
import json
import re

from enum import unique, IntEnum


SbciColumnDesc = namedtuple('SbciColumnDesc', ['name', 'func', 'head'])


@unique
class SbciEnum(IntEnum):
    '''TODO'''

    @classmethod
    def __real_new__(cls, value, alt_value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.alt_value = alt_value
        return obj

    def __new__(cls, value, alt_value):
        return cls.__real_new__(value, alt_value)

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

    @classmethod
    def by_alt_value(cls, alt_value):
        if alt_value is None:
            return None
        for e in cls:
            if e.alt_value == alt_value:
                return e
        else:
            raise ValueError('{} not a valid SbciEnum!'.format(alt_value))


def end_of_season():
    '''TODO'''
    today = date.today()
    end_of_summer = date(today.year, 3, 31)  # near enough is good enough
    if today <= end_of_summer:
        return end_of_summer
    end_of_winter = date(today.year, 9, 30)  # near enough is good enough
    if today <= end_of_winter:
        return end_of_winter
    return date(today.year + 1, 3, 31)


def _prepare_str(s, allow_none):
    '''TODO'''
    if s is None:
        if allow_none:
            return None
        raise ValueError('string is None!')
    stmp = s.strip()
    if s == '':
        if allow_none:
            return None
        raise ValueError('string is empty!')
    return stmp


def date_str(s, fmt='%Y-%m-%d', allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt).date()


def time_str(s, fmt='%I:%M:%S %p', allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt).time()


def datetime_str(s, fmt='%Y-%m-%d %H:%M:%S.%f', allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt)


def latin1_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    return unicode(stmp, encoding='latin-1')


def currency_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    return float(stmp.replace(',', ''))


name2postcode = {
    'Melbourne':                 3000,
    'Moonee Ponds':              3039,
    'Brunswick East':            3057,
    'Sumner':                    3057,
    'Coburg':                    3058,
    'Fitzroy':                   3065,
    'Clifton Hill':              3068,
    'Northcote':                 3070,
    'Thornbury':                 3071,
    'Preston':                   3072,
    'Reservoir':                 3073,
    'Fairfield':                 3078,
    'Alphington':                3078,
    'Ivanhoe':                   3079,
    'Ivanhoe East':              3079,
    'Heidelberg Heights':        3081,
    'Bellfield':                 3081,
    'Eaglemont':                 3084,
    'Macleod':                   3085,
    'Macleod West':              3085,
    'Yallambie':                 3085,
    'Watsonia':                  3087,
    'Kew':                       3101,
    'East Kew':                  3102,
    'Balwyn North':              3104,
    'Bulleen':                   3105,
    'Doncaster':                 3108,
    'Camberwell':                3124,
    'Camberwell East':           3126,
    'Canterbury':                3126,
    'Box Hill South':            3128,
    'Patterson Lakes':           3197,
    'Carrum':                    3197,
    'Albert Park':               3206,
    'South Morang':              3752,
    'Como, WA':                  6152,
    'Little Lonsdale St, Vic':   8011,
}


postcode2name = {postcode: name for name, postcode in name2postcode.viewitems()}


def postcode_str(s, allow_none=True):
    '''TODO'''
    stmp = posint_str(s, allow_none)
    if stmp is None:
        return None
    postcode = int(stmp)
    if postcode not in postcode2name:
        raise RuntimeError('not a known postcode! (%r)' % s)
    return postcode


_phone_fixups = {}
try:
    with open('../misc/phone_fixups.json') as fd:
        _phone_fixups.extend(json.load(fd))
except BaseException:
    pass
_phone_pattern = re.compile(r'^\+?(61|0)?')


def phone_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    for r in ' \t\r\n-()[].':
        stmp = stmp.replace(r, '')
    if stmp.startswith('+61'):
        stmp = '0' + stmp[3:]
    if stmp.startswith(('3', '4')):
        stmp = '0' + stmp
    if stmp in _phone_fixups:
        return _phone_fixups[stmp]
    if _phone_pattern.match(stmp) is None:
        raise RuntimeError('not a valid phone number! (%r)' % s)
    return stmp


_email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def email_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    if _email_pattern.match(stmp) is None:
        raise RuntimeError('not a valid email address! (%r)' % s)
    return stmp


def posint_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    if not stmp.isdigit():
        raise RuntimeError('not a valid positive integer! (%r)' % s)
    return stmp


def boolean_str(s, allow_none=True):
    '''TODO'''
    stmp = _prepare_str(s, allow_none)
    if stmp is None:
        return None
    if stmp.lower() in ('t', 'true', 'y', 'yes', 'on'):
        return True
    if stmp.lower() in ('f', 'false', 'n', 'no', 'off'):
        return False
    if not stmp.isdigit():
        raise RuntimeError('not a valid boolean string! (%r)' % s)
    return (int(stmp) != 0)
