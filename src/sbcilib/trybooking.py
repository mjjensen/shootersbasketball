'''
Created on 4 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from collections import deque, namedtuple
import csv
from datetime import datetime
from time import strptime

from sbcilib.utils import SbciEnum, latin1_str, postcode_str, currency_str,\
    date_str, phone_str, email_str, posint_str, time_str, boolean_str,\
    SbciColumnDesc, datetime_str


_tbreg_cols = (
    SbciColumnDesc(
        'first_name',
        lambda v: latin1_str(v),
        'Booking First Name'
    ),
    SbciColumnDesc(
        'last_name',
        lambda v: latin1_str(v),
        'Booking Last Name'
    ),
    SbciColumnDesc(
        'address_1',
        lambda v: latin1_str(v),
        'Booking Address 1'
    ),
    SbciColumnDesc(
        'address_2',
        lambda v: latin1_str(v),
        'Booking Address 2'
    ),
    SbciColumnDesc(
        'suburb',
        lambda v: latin1_str(v),
        'Booking Suburb'
    ),
    SbciColumnDesc(
        'state',
        lambda v: latin1_str(v),
        'Booking State'
    ),
    SbciColumnDesc(
        'post_code',
        lambda v: postcode_str(v),
        'Booking Post Code'
    ),
    SbciColumnDesc(
        'country',
        lambda v: latin1_str(v),
        'Booking Country'
    ),
    SbciColumnDesc(
        'telephone',
        lambda v: phone_str(v),
        'Booking Telephone'
    ),
    SbciColumnDesc(
        'email',
        lambda v: email_str(v),
        'Booking Email'
    ),
    SbciColumnDesc(
        'booking_id',
        lambda v: latin1_str(v),
        'Booking ID'
    ),
    SbciColumnDesc(
        'number_of_tickets',
        lambda v: posint_str(v),
        'Number of Tickets'
    ),
    SbciColumnDesc(
        'payment_received',
        lambda v: currency_str(v),
        'Payment Received'
    ),
    SbciColumnDesc(
        'discount_amount',
        lambda v: currency_str(v),
        'Discount Amount'
    ),
    SbciColumnDesc(
        'processing_fees',
        lambda v: currency_str(v),
        'Processing Fees'
    ),
    SbciColumnDesc(
        'box_office_fees',
        lambda v: currency_str(v),
        'Box Office Fees'
    ),
    SbciColumnDesc(
        'box_office_quicksale',
        lambda v: boolean_str(v),
        'Box Office Quicksale'
    ),
    SbciColumnDesc(
        'date_booked',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Booked (GMT+10:00)'
    ),
    SbciColumnDesc(
        'time_booked',
        lambda v: time_str(v),
        'Time Booked'
    ),
    SbciColumnDesc(
        'permission_to_contact',
        lambda v: latin1_str(v),
        'Permission to Contact'
    ),
    SbciColumnDesc(
        'ticket_type',
        lambda v: latin1_str(v),
        'Ticket Type'
    ),
    SbciColumnDesc(
        'ticket_price',
        lambda v: currency_str(v),
        'Ticket Price (AUD)'
    ),
    SbciColumnDesc(
        'discount_code',
        lambda v: latin1_str(v),
        'Promotion[Discount] Code'
    ),
    SbciColumnDesc(
        'section',
        lambda v: latin1_str(v),
        'Section'
    ),
    SbciColumnDesc(
        'ticket_number',
        lambda v: latin1_str(v),
        'Ticket Number'
    ),
    SbciColumnDesc(
        'seat_row',
        lambda v: latin1_str(v),
        'Seat Row'
    ),
    SbciColumnDesc(
        'seat_number',
        lambda v: latin1_str(v),
        'Seat Number'
    ),
    SbciColumnDesc(
        'refunded_misc',
        lambda v: latin1_str(v),
        'Refunded Misc'
    ),
    SbciColumnDesc(
        'refunded_amount',
        lambda v: currency_str(v),
        'Ticket Refunded Amount'
    ),
    SbciColumnDesc(
        'status',
        lambda v: latin1_str(v),
        'Ticket Status'
    ),
    SbciColumnDesc(
        'void',
        lambda v: latin1_str(v),
        'Void'
    ),
    SbciColumnDesc(
        'player_first_name',
        lambda v: latin1_str(v),
        'Ticket Data: Player First Name'
    ),
    SbciColumnDesc(
        'player_family_name',
        lambda v: latin1_str(v),
        'Ticket Data: Player Family Name'
    ),
)


class TBRegRecord(namedtuple('TBRegRecord', (c.name for c in _tbreg_cols))):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(TBRegRecord, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def TBRegReadCSV(csvfile, verbose=0, reverse=False):
    '''TODO'''

    if verbose > 0:
        print('Reading Trybooking Registration CSV file: {} ... '
              .format(csvfile), end='')

    records = deque()

    with open(csvfile) as fd:

        magic = fd.read(3)
        if magic not in ('\ufeff', '\xef\xbb\xbf'):
            if verbose > 2:
                print('no weird bytes at start of file! (%r)' % magic)
            fd.seek(0)
        elif verbose > 2:
            print(r'skip weird bytes at start of file! (\ufeff)')

        reader = csv.reader(fd)

        headings = next(reader)

        for c, h in zip(_tbreg_cols, headings):
            if h != c.head:
                raise RuntimeError('column heading mismatch! ("%s" != "%s")'
                                   % (h, c.head))

        for row in reader:

            if verbose > 2:
                print('row={}'.format(row))

            record = TBRegRecord(*(c.func(v) for c, v in zip(_tbreg_cols, row)))

            if verbose > 1:
                print('{}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} records read.'.format(len(records)))

    return records


_tbtrx_cols = (
    SbciColumnDesc(
        'date',
        lambda v: datetime_str(v, '%d%b%Y %I:%M %p'),
        'Date'
    ),
    SbciColumnDesc(
        'trxtype',
        lambda v: latin1_str(v),
        'Transaction'
    ),
    SbciColumnDesc(
        'booking_id',
        lambda v: latin1_str(v),
        'Booking ID'
    ),
    SbciColumnDesc(
        'description',
        lambda v: latin1_str(v),
        'Description'
    ),
    SbciColumnDesc(
        'customer',
        lambda v: latin1_str(v),
        'Customer'
    ),
    SbciColumnDesc(
        'debit',
        lambda v: currency_str(v),
        'Debit'
    ),
    SbciColumnDesc(
        'credit',
        lambda v: currency_str(v),
        'Credit'
    ),
)


class TBTrxType(SbciEnum):
    '''TODO'''

    BOOKING = 1, True, 'Booking'
    TRANSFER = 2, False, 'Fund Transfer'
    CHARGE = 3, False, 'Gateway Charge'
    RCHARGE = 4, True, 'Refunded PG Charge'
    RBOOKING = 5, False, 'Refunded Tickets'
    BANKVERIFY = 6, False, 'Bank Verification'

    def __new__(cls, value, is_credit, csv_value):
        obj = cls.__real_new__(value, csv_value)
        obj.is_credit = is_credit
        obj.csv_value = csv_value
        return obj

    @classmethod
    def by_csv_value(cls, csv_value):
        return cls.by_alt_value(csv_value)


TBTrxRecord = namedtuple('TBTrxRecord', c.name for c in _tbtrx_cols)


def TBTrxReadCSV(csvfile, verbose=0, reverse=False):
    '''TODO'''

    if verbose > 0:
        print('Reading Trybooking Transaction CSV file: {} ... '
              .format(csvfile), end='')

    records = deque()
    first_column_name = next(iter(_tbtrx_cols)).head

    with open(csvfile) as fd:

        # skip header crap at start of file
        pos = fd.tell()
        skipped_lines = 0
        while not fd.readline().startswith(first_column_name):
            pos = fd.tell()
            skipped_lines += 1
        fd.seek(pos)

        reader = csv.reader(fd)

        headings = next(reader)

        for c, h in zip(_tbtrx_cols, headings):
            if h != c.head:
                raise RuntimeError('column heading mismatch! ("%s" != "%s")'
                                   % (h, c.head))

        for row in reader:

            if verbose > 2:
                print('row={}'.format(row))

            record = TBTrxRecord(*(c.func(v) for c, v in zip(_tbtrx_cols, row)))

            if verbose > 1:
                print('{}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} tbtrx records read.'.format(len(records)))

    return records


__all__ = ['TBRegRecord', 'TBRegReadCSV', 'TBTrxRecord', 'TBTrxReadCSV']
