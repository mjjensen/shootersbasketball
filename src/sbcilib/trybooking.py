'''
Created on 4 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from sbcilib.utils import SbciEnum, latin1_str, postcode_str, currency_str,\
    date_str, phone_str, email_str, posint_str, time_str, boolean_str,\
    SbciCSVColumn, datetime_str, SbciCSVInfo, prepare_str


def _tb_initiate(fd):
    magic = fd.read(3)
    if magic not in ('\ufeff', '\xef\xbb\xbf'):
        fd.seek(0)


tb_rego_csvinfo = SbciCSVInfo(
    SbciCSVColumn(
        'first_name',
        latin1_str,
        'Booking First Name'
    ),
    SbciCSVColumn(
        'last_name',
        latin1_str,
        'Booking Last Name'
    ),
    SbciCSVColumn(
        'address_1',
        latin1_str,
        'Booking Address 1'
    ),
    SbciCSVColumn(
        'address_2',
        latin1_str,
        'Booking Address 2'
    ),
    SbciCSVColumn(
        'suburb',
        latin1_str,
        'Booking Suburb'
    ),
    SbciCSVColumn(
        'state',
        latin1_str,
        'Booking State'
    ),
    SbciCSVColumn(
        'post_code',
        postcode_str,
        'Booking Post Code'
    ),
    SbciCSVColumn(
        'country',
        latin1_str,
        'Booking Country'
    ),
    SbciCSVColumn(
        'telephone',
        phone_str,
        'Booking Telephone'
    ),
    SbciCSVColumn(
        'email',
        email_str,
        'Booking Email'
    ),
    SbciCSVColumn(
        'booking_id',
        latin1_str,
        'Booking ID'
    ),
    SbciCSVColumn(
        'number_of_tickets',
        posint_str,
        'Number of Tickets'
    ),
    SbciCSVColumn(
        'payment_received',
        currency_str,
        'Payment Received'
    ),
    SbciCSVColumn(
        'discount_amount',
        currency_str,
        'Discount Amount'
    ),
    SbciCSVColumn(
        'processing_fees',
        currency_str,
        'Processing Fees'
    ),
    SbciCSVColumn(
        'box_office_fees',
        currency_str,
        'Box Office Fees'
    ),
    SbciCSVColumn(
        'box_office_quicksale',
        boolean_str,
        'Box Office Quicksale'
    ),
    SbciCSVColumn(
        'date_booked',
        lambda v: date_str(v, '%d/%m/%Y'),
        'Date Booked (GMT+10:00)'
    ),
    SbciCSVColumn(
        'time_booked',
        time_str,
        'Time Booked'
    ),
    SbciCSVColumn(
        'permission_to_contact',
        latin1_str,
        'Permission to Contact'
    ),
    SbciCSVColumn(
        'ticket_type',
        latin1_str,
        'Ticket Type'
    ),
    SbciCSVColumn(
        'ticket_price',
        currency_str,
        'Ticket Price (AUD)'
    ),
    SbciCSVColumn(
        'discount_code',
        latin1_str,
        'Promotion[Discount] Code'
    ),
    SbciCSVColumn(
        'section',
        latin1_str,
        'Section'
    ),
    SbciCSVColumn(
        'ticket_number',
        latin1_str,
        'Ticket Number'
    ),
    SbciCSVColumn(
        'seat_row',
        latin1_str,
        'Seat Row'
    ),
    SbciCSVColumn(
        'seat_number',
        latin1_str,
        'Seat Number'
    ),
    SbciCSVColumn(
        'refunded_misc',
        latin1_str,
        'Refunded Misc'
    ),
    SbciCSVColumn(
        'refunded_amount',
        currency_str,
        'Ticket Refunded Amount'
    ),
    SbciCSVColumn(
        'status',
        latin1_str,
        'Ticket Status'
    ),
    SbciCSVColumn(
        'void',
        latin1_str,
        'Void'
    ),
    SbciCSVColumn(
        'player_first_name',
        latin1_str,
        'Ticket Data: Player First Name'
    ),
    SbciCSVColumn(
        'player_family_name',
        latin1_str,
        'Ticket Data: Player Family Name'
    ),
    initiate=_tb_initiate,
)


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


def _tb_trxtype_str(s, allow_none=True):
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return TBTrxCSVType.by_csv_value(s)


def _tb_trx_initiate(fd):
    _tb_initiate(fd)

    # skip header crap at start of file
    pos = fd.tell()
    while not fd.readline().startswith('Date'):
        pos = fd.tell()
    fd.seek(pos)


def _tb_trx_terminate(d):
    return d['Date'].startswith('Total')


tb_trx_csvinfo = SbciCSVInfo(
    SbciCSVColumn(
        'date',
        lambda v: datetime_str(v, '%d%b%y %I:%M %p'),
        'Date'
    ),
    SbciCSVColumn(
        'type',
        _tb_trxtype_str,
        'Transaction'
    ),
    SbciCSVColumn(
        'booking_id',
        latin1_str,
        'Booking ID'
    ),
    SbciCSVColumn(
        'description',
        latin1_str,
        'Description'
    ),
    SbciCSVColumn(
        'customer',
        latin1_str,
        'Customer'
    ),
    SbciCSVColumn(
        'debit',
        currency_str,
        'Debit'
    ),
    SbciCSVColumn(
        'credit',
        currency_str,
        'Credit'
    ),
    initiate=_tb_trx_initiate,
    terminate=_tb_trx_terminate,
)


__all__ = ['tb_rego_csvinfo', 'TBTrxCSVType', 'tb_trx_csvinfo']
