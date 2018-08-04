'''
Created on 4 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from collections import OrderedDict, namedtuple
import csv
from datetime import date, datetime
from time import strptime

from sbcilib.financedb import SbciTransactionType


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
    ('Booking ID',                      'id'),
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
    ('Transaction', 'type'),
    ('Booking ID', 'id'),
    ('Description', 'desc'),
    ('Customer', 'cust'),
    ('Debit', 'debit'),
    ('Credit', 'credit'),
))


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
                data['date'] = datetime(st[:6])
            data['type'] = SbciTransactionType.by_csv_value(data['type'])
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
