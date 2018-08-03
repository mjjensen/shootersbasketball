'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

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
        for e in cls:
            if e.alt_value == alt_value:
                return e
