'''
Created on 4 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from collections import deque, OrderedDict, namedtuple
import csv
from datetime import date, datetime
from time import strptime

from sbcilib.utils import SbciEnum, latin1_str, postcode_str, currency_str,\
    date_str


_c = namedtuple('_c', ['name', 'func', 'head'])

_tbreg_cols = (
    _c(
        'first_name',
        lambda v: latin1_str(v),
        'Booking First Name'
    ),
    _c(
        'last_name',
        lambda v: latin1_str(v),
        'Booking Last Name'
    ),
    _c(
        'address_1',
        lambda v: latin1_str(v),
        'Booking Address 1'
    ),
    _c(
        'address_2',
        lambda v: latin1_str(v),
        'Booking Address 2'
    ),
    _c(
        'suburb',
        lambda v: latin1_str(v),
        'Booking Suburb'
    ),
    _c(
        'state',
        lambda v: latin1_str(v),
        'Booking State'
    ),
    _c(
        'post_code',
        lambda v: postcode_str(v),
        'Booking Post Code'
    ),
    _c(
        'country',
        lambda v: latin1_str(v),
        'Booking Country'
    ),
    _c(
        'telephone',
        lambda v: phone_str(v),
        'Booking Telephone'
    ),
    _c(
        'email',
        lambda v: email_str(v),
        'Booking Email'
    ),
    _c(
        'booking_id',
        lambda v: latin1_str(v),
        'Booking ID'
    ),
    _c(
        'number_of_tickets',
        lambda v: number_str(v),
        'Number of Tickets'
    ),
    _c(
        'payment_received',
        lambda v: currency_str(v),
        'Payment Received'
    ),
    _c(
        'discount_amount',
        lambda v: currency_str(v),
        'Discount Amount'
    ),
    _c(
        'processing_fees',
        lambda v: currency_str(v),
        'Processing Fees'
    ),
    _c(
        'box_office_fees',
        lambda v: currency_str(v),
        'Box Office Fees'
    ),
    _c(
        'box_office_quicksale',
        lambda v: latin1_str(v),
        'Box Office Quicksale'
    ),
    _c(
        'date_booked',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Booked (GMT+10:00)'
    ),
    _c(
        'time_booked',
        lambda v: time_str(v),
        'Time Booked'
    ),
    _c(
        'permission_to_contact',
        lambda v: latin1_str(v),
        'Permission to Contact'
    ),
    _c(
        'ticket_type',
        lambda v: latin1_str(v),
        'Ticket Type'
    ),
    _c(
        'ticket_price',
        lambda v: currency_str(v),
        'Ticket Price (AUD)'
    ),
    _c(
        'discount_code',
        lambda v: latin1_str(v),
        'Promotion[Discount] Code'
    ),
    _c(
        'section',
        lambda v: latin1_str(v),
        'Section'
    ),
    _c(
        'ticket_number',
        lambda v: latin1_str(v),
        'Ticket Number'
    ),
    _c(
        'seat_row',
        lambda v: latin1_str(v),
        'Seat Row'
    ),
    _c(
        'seat_number',
        lambda v: latin1_str(v),
        'Seat Number'
    ),
    _c(
        'refunded_misc',
        lambda v: latin1_str(v),
        'Refunded Misc'
    ),
    _c(
        'refunded_amount',
        lambda v: currency_str(v),
        'Ticket Refunded Amount'
    ),
    _c(
        'status',
        lambda v: latin1_str(v),
        'Ticket Status'
    ),
    _c(
        'void',
        lambda v: latin1_str(v),
        'Void'
    ),
    _c(
        'player_first_name',
        lambda v: latin1_str(v),
        'Ticket Data: Player First Name'
    ),
    _c(
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
        print('Reading Commbank Transaction CSV file: {} ... '
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

        headers = next(reader)

        for c, h in zip(_tbreg_cols, headers):
            if h != c.head:
                raise RuntimeError('column header mismatch! ("%s"!="%s")'
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


_tbrego_colmap = OrderedDict((
    ('Booking First Name',              'first_name'),
    ('Booking Last Name',               'last_name'),
    ('Booking Address 1',               'address_1'),
    ('Booking Address 2',               'address_2'),
    ('Booking Suburb',                  'suburb'),
    ('Booking State',                   'state'),
    ('Booking Post Code',               'post_code'),
    ('Booking Country',                 'country'),
    ('Booking Telephone',               'telephone'),
    ('Booking Email',                   'email'),
    ('Booking ID',                      'booking_id'),
    ('Number of Tickets',               'number_of_tickets'),
    ('Payment Received',                'payment_received'),
    ('Discount Amount',                 'discount_amount'),
    ('Processing Fees',                 'processing_fees'),
    ('Box Office Fees',                 'box_office_fees'),
    ('Box Office Quicksale',            'box_office_quicksale'),
    ('Date Booked (GMT+10:00)',         'date_booked'),
    ('Time Booked',                     'time_booked'),
    ('Permission to Contact',           'permission_to_contact'),
    ('Ticket Type',                     'ticket_type'),
    ('Ticket Price (AUD)',              'ticket_price'),
    ('Promotion[Discount] Code',        'discount_code'),
    ('Section',                         'section'),
    ('Ticket Number',                   'ticket_number'),
    ('Seat Row',                        'seat_row'),
    ('Seat Number',                     'seat_number'),
    ('Refunded Misc',                   'refunded_misc'),
    ('Ticket Refunded Amount',          'refunded_amount'),
    ('Ticket Status',                   'status'),
    ('Void',                            'void'),
    ('Ticket Data: Player First Name',  'player_first_name'),
    ('Ticket Data: Player Family Name', 'player_family_name'),
))

TBRegoRecord = namedtuple('TBRegoRecord', _tbrego_colmap.values())


def TBRegoReadCSV(csvfile, verbose=0):
    '''TODO'''

    if verbose > 0:
        print('Reading Trybooking Registration CSV file: {} ... '
              .format(csvfile), end='')

    records = []
    first_column_name = next(iter(_tbrego_colmap))

    with open(csvfile) as fd:

        if fd.read(2) != '\ufeff':
            fd.seek(0)

        reader = csv.DictReader(fd)

        for d in reader:

            # SportsTG puts crap at the end ...
            if d[first_column_name] == ' rows ':
                break

            data = {
                _tbrego_colmap[k]: unicode(d[k], encoding='latin-1')
                if type(d[k]) is str else d[k]
                for k in _tbrego_colmap
            }

            if data['date_booked'] == '':
                data['date_booked'] = None
            elif data['date_booked'] is not None:
                st = strptime(data['date_booked'], '%d/%m/%Y')
                data['date_booked'] = date(*st[:3])

            record = TBRegoRecord(**data)

            if verbose > 1:
                print('{}'.format(record))

            records.append(record)

    if verbose > 0:
        print('{} tbrego records read.'.format(len(records)))

    return records


_tbxact_colmap = OrderedDict((
    ('Date', 'date'),
    ('Transaction', 'xact'),
    ('Booking ID', 'booking_id'),
    ('Description', 'description'),
    ('Customer', 'customer'),
    ('Debit', 'debit'),
    ('Credit', 'credit'),
))


class TBXactType(SbciEnum):
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


TBXactRecord = namedtuple('TBXactRecord', _tbxact_colmap.values())


def TBXactReadCSV(csvfile, verbose=0):
    '''TODO'''

    if verbose > 0:
        print('Reading Trybooking Transaction CSV file: {} ... '
              .format(csvfile), end='')

    records = []
    first_column_name = next(iter(_tbxact_colmap))

    with open(csvfile) as fd:

        # skip header crap at start of file
        pos = fd.tell()
        skipped_lines = 0
        while not fd.readline().startswith(first_column_name):
            pos = fd.tell()
            skipped_lines += 1
        fd.seek(pos)

        reader = csv.DictReader(fd)

        for d in reader:

            # skip crap at end of file ...
            if d[first_column_name].startswith('Total'):
                break

            data = {
                _tbxact_colmap[k]: unicode(d[k], encoding='latin-1')
                if type(d[k]) is str else d[k]
                for k in _tbxact_colmap
            }

            # massage ...
            if data['date'] == '':
                data['date'] = None
            elif data['date'] is not None:
                # 26Apr2016 02:07 PM or 27Jul18 4:36 PM
                try:
                    st = strptime(data['date'], '%d%b%Y %I:%M %p')
                except ValueError:
                    st = strptime(data['date'], '%d%b%y %I:%M %p')
                data['date'] = datetime(*st[:6])
            data['xact'] = TBXactType.by_csv_value(data['xact'])
            data['debit'] = float(data['debit'].replace(',', ''))
            data['credit'] = float(data['credit'].replace(',', ''))

            record = TBXactRecord(**data)

            if verbose > 1:
                print('{}'.format(record))

            records.append(record)

    if verbose > 0:
        print('{} tbxact records read.'.format(len(records)))

    return records


__all__ = ['TBRegoRecord', 'TBRegoReadCSV', 'TBXactRecord', 'TBXactReadCSV']
