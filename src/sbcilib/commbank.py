'''
Created on 8 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from collections import deque, namedtuple
import csv

from sbcilib.utils import date_str, currency_str, latin1_str


_cbtrx_cols = (
    ('date',
        lambda v: date_str(v, '%d/%m/%Y')),
    ('amount',
        lambda v: currency_str(v)),
    ('description',
        lambda v: latin1_str(v)),
    ('balance',
        lambda v: currency_str(v)),
)


class CBTrxRecord(namedtuple('CBTrxRecord', (n for n, f in _cbtrx_cols))):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(CBTrxRecord, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def CBTrxReadCSV(csvfile, verbose=0, reverse=False):
    '''TODO'''

    if verbose > 0:
        print('Reading Commbank Transaction CSV file: {} ... '
              .format(csvfile), end='')

    records = deque()

    with open(csvfile) as fd:

        reader = csv.reader(fd)

        for row in reader:

            if verbose > 2:
                print('row={}'.format(row))

            record = CBTrxRecord(*(f(v) for (n, f), v in zip(_cbtrx_cols, row)))

            if verbose > 1:
                print('{}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} records read.'.format(len(records)))

    return records


__all__ = ['CBTrxRecord', 'CBTrxReadCSV']
