'''
Created on 4 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from collections import deque, namedtuple
import csv

from sbcilib.utils import SbciEnum, latin1_str, postcode_str, currency_str,\
    date_str, phone_str, email_str, posint_str, time_str, boolean_str,\
    SbciCSVColumn, datetime_str


_tbreg_cols = (
    SbciCSVColumn(
        'first_name',
        lambda v: latin1_str(v),
        'Booking First Name'
    ),
    SbciCSVColumn(
        'last_name',
        lambda v: latin1_str(v),
        'Booking Last Name'
    ),
    SbciCSVColumn(
        'address_1',
        lambda v: latin1_str(v),
        'Booking Address 1'
    ),
    SbciCSVColumn(
        'address_2',
        lambda v: latin1_str(v),
        'Booking Address 2'
    ),
    SbciCSVColumn(
        'suburb',
        lambda v: latin1_str(v),
        'Booking Suburb'
    ),
    SbciCSVColumn(
        'state',
        lambda v: latin1_str(v),
        'Booking State'
    ),
    SbciCSVColumn(
        'post_code',
        lambda v: postcode_str(v),
        'Booking Post Code'
    ),
    SbciCSVColumn(
        'country',
        lambda v: latin1_str(v),
        'Booking Country'
    ),
    SbciCSVColumn(
        'telephone',
        lambda v: phone_str(v),
        'Booking Telephone'
    ),
    SbciCSVColumn(
        'email',
        lambda v: email_str(v),
        'Booking Email'
    ),
    SbciCSVColumn(
        'booking_id',
        lambda v: latin1_str(v),
        'Booking ID'
    ),
    SbciCSVColumn(
        'number_of_tickets',
        lambda v: posint_str(v),
        'Number of Tickets'
    ),
    SbciCSVColumn(
        'payment_received',
        lambda v: currency_str(v),
        'Payment Received'
    ),
    SbciCSVColumn(
        'discount_amount',
        lambda v: currency_str(v),
        'Discount Amount'
    ),
    SbciCSVColumn(
        'processing_fees',
        lambda v: currency_str(v),
        'Processing Fees'
    ),
    SbciCSVColumn(
        'box_office_fees',
        lambda v: currency_str(v),
        'Box Office Fees'
    ),
    SbciCSVColumn(
        'box_office_quicksale',
        lambda v: boolean_str(v),
        'Box Office Quicksale'
    ),
    SbciCSVColumn(
        'date_booked',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Booked (GMT+10:00)'
    ),
    SbciCSVColumn(
        'time_booked',
        lambda v: time_str(v),
        'Time Booked'
    ),
    SbciCSVColumn(
        'permission_to_contact',
        lambda v: latin1_str(v),
        'Permission to Contact'
    ),
    SbciCSVColumn(
        'ticket_type',
        lambda v: latin1_str(v),
        'Ticket Type'
    ),
    SbciCSVColumn(
        'ticket_price',
        lambda v: currency_str(v),
        'Ticket Price (AUD)'
    ),
    SbciCSVColumn(
        'discount_code',
        lambda v: latin1_str(v),
        'Promotion[Discount] Code'
    ),
    SbciCSVColumn(
        'section',
        lambda v: latin1_str(v),
        'Section'
    ),
    SbciCSVColumn(
        'ticket_number',
        lambda v: latin1_str(v),
        'Ticket Number'
    ),
    SbciCSVColumn(
        'seat_row',
        lambda v: latin1_str(v),
        'Seat Row'
    ),
    SbciCSVColumn(
        'seat_number',
        lambda v: latin1_str(v),
        'Seat Number'
    ),
    SbciCSVColumn(
        'refunded_misc',
        lambda v: latin1_str(v),
        'Refunded Misc'
    ),
    SbciCSVColumn(
        'refunded_amount',
        lambda v: currency_str(v),
        'Ticket Refunded Amount'
    ),
    SbciCSVColumn(
        'status',
        lambda v: latin1_str(v),
        'Ticket Status'
    ),
    SbciCSVColumn(
        'void',
        lambda v: latin1_str(v),
        'Void'
    ),
    SbciCSVColumn(
        'player_first_name',
        lambda v: latin1_str(v),
        'Ticket Data: Player First Name'
    ),
    SbciCSVColumn(
        'player_family_name',
        lambda v: latin1_str(v),
        'Ticket Data: Player Family Name'
    ),
)


class TBRegCSVRecord(namedtuple('TBRegCSVRecord',
                                (c.name for c in _tbreg_cols))):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(TBRegCSVRecord, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def TBRegCSVRead(csvfile, verbose=0, reverse=False):
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

            record = TBRegCSVRecord(*(c.func(v)
                                      for c, v in zip(_tbreg_cols, row)))

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
    SbciCSVColumn(
        'date',
        lambda v: datetime_str(v, '%d%b%y %I:%M %p'),
        'Date'
    ),
    SbciCSVColumn(
        'type',
        lambda v: latin1_str(v),
        'Transaction'
    ),
    SbciCSVColumn(
        'booking_id',
        lambda v: latin1_str(v),
        'Booking ID'
    ),
    SbciCSVColumn(
        'description',
        lambda v: latin1_str(v),
        'Description'
    ),
    SbciCSVColumn(
        'customer',
        lambda v: latin1_str(v),
        'Customer'
    ),
    SbciCSVColumn(
        'debit',
        lambda v: currency_str(v),
        'Debit'
    ),
    SbciCSVColumn(
        'credit',
        lambda v: currency_str(v),
        'Credit'
    ),
)
_tbtrx_del = (9, 7, 6, 5, 2)


class TBTrxCSVType(SbciEnum):
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


class TBTrxCSVRecord(namedtuple('TBTrxCSVRecord',
                                (c.name for c in _tbtrx_cols))):
    __slots__ = ()

    def __getitem__(self, index):
        try:
            return super(TBTrxCSVRecord, self).__getitem__(index)
        except TypeError:
            return getattr(self, index)


def TBTrxCSVRead(csvfile, verbose=0, reverse=False):
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
        for c in _tbtrx_del:
            del headings[c]

        for c, h in zip(_tbtrx_cols, headings):
            if h != c.head:
                raise RuntimeError('column heading mismatch! ("%s" != "%s")'
                                   % (h, c.head))

        for row in reader:

            for c in _tbtrx_del:
                del row[c]

            if row[0].startswith('Total'):
                break

            if verbose > 2:
                print('row={}'.format(row))

            record = TBTrxCSVRecord(*(c.func(v)
                                      for c, v in zip(_tbtrx_cols, row)))

            if verbose > 1:
                print('{}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} tbtrx records read.'.format(len(records)))

    return records


__all__ = ['TBRegCSVRecord', 'TBRegCSVRead',
           'TBTrxCSVType', 'TBTrxCSVRecord', 'TBTrxCSVRead']
