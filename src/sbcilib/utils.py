'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

from datetime import date
from time import strptime

from enum import unique, IntEnum


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
            raise RuntimeError('{} not a valid SbciEnum!'.format(alt_value))


def date_str(s, fmt='%Y-%m-%d'):
    '''TODO'''
    if s is None:
        return None
    stmp = s.strip()
    if stmp == '':
        return None
    return date(*(strptime(stmp, fmt)[:3]))


def latin1_str(s):
    '''TODO'''
    return unicode(s.strip(), encoding='latin-1')


def currency_str(s):
    '''TODO'''
    return float(s.strip().replace(',', ''))


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
    'Camberwell East':           3126,
    'Canterbury':                3126,
    'Box Hill South':            3128,
    'Patterson Lakes':           3197,
    'Carrum':                    3197,
    'Albert Park':               3206,
    'South Morang':              3752,
    'Little Lonsdale St, Vic':   8011,
}


postcode2name = {postcode: name for name, postcode in name2postcode.viewitems()}


def postcode_str(s):
    '''TODO'''
    stmp = s.strip()
    if not stmp.isdigit():
        raise RuntimeError('not a valid postcode! (%s)' % s)
    postcode = int(stmp)
    if postcode not in postcode2name:
        raise RuntimeError('not a known postcode! (%s)' % s)
    return postcode
