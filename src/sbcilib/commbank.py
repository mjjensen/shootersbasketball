'''
Created on 8 Aug. 2018

@author: jen117
'''
from __future__ import print_function

from sbcilib.utils import date_str, currency_str, latin1_str, SbciCSVInfo,\
    SbciCSVColumn


cb_trx_csvinfo = SbciCSVInfo(
    SbciCSVColumn('date', lambda v: date_str(v, '%d/%m/%Y'), 'date'),
    SbciCSVColumn('amount', currency_str, 'amount'),
    SbciCSVColumn('description', latin1_str, 'description'),
    SbciCSVColumn('balance', currency_str, 'balance'),
    fieldnames=('date', 'amount', 'description', 'balance'),
)


__all__ = ['cb_trx_csvinfo']
