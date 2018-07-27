'''
Created on 7 Jul. 2018

@author: jen117
'''
from collections import Mapping
from enum import unique, IntEnum
import json
from logging import getLogger
import os
from sqlalchemy.ext.automap import automap_base

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session


_logger = getLogger(__name__)
_config = {
    'db_file':     'finance.sqlite3',  # leave out if no file backing db
    'db_url':      'sqlite:///finance.sqlite3',
}


@unique
class SbciTransactionType(IntEnum):
    '''TODO'''
    NOTSET = 0, None, None
    BOOKING = 1, True, 'Booking'
    TRANSFER = 2, False, 'Fund Transfer'
    CHARGE = 3, False, 'Gateway Charge'
    RCHARGE = 4, True, 'Refunded PG Charge'
    RBOOKING = 5, False, 'Refunded Tickets'

    def __new__(cls, value, is_credit, csvvalue):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.is_credit = is_credit
        obj.csvvalue = csvvalue
        return obj

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

    @classmethod
    def by_csvvalue(cls, csvvalue):
        for t in SbciTransactionType:
            if t.csvvalue == csvvalue:
                return t


class SbciFinanceDB(object):
    '''TODO'''

    def __init__(self, verbose=False, *args, **kwds):
        super(SbciFinanceDB, self).__init__(*args, **kwds)

        try:
            with open('config.json', 'r') as fd:
                contents = json.load(fd)
                if isinstance(contents, Mapping):
                    _config.update(contents)
                elif verbose:
                    _logger.error('contents of "config.json" are unsuitable!')
        except (IOError, ValueError) as e:
            if verbose > 1:
                _logger.warning('exception reading "config.json": %s', str(e))

        self.Base = automap_base()

        if 'db_file' in _config:
            db_file = _config['db_file']
            if not os.access(db_file, os.R_OK | os.W_OK):
                raise RuntimeError('cannot access DB file ({}) for R/W!'
                                   .format(db_file))

        self.engine = create_engine(_config['db_url'])

        self.Base.prepare(self.engine, reflect=True)

        self.Categories = self.Base.classes.categories
        self.Seasons = self.Base.classes.seasons
        self.Cheques = self.Base.classes.cheques
        self.Transactions = self.Base.classes.transactions
        self.Trybooking = self.Base.classes.trybooking

        self.dbsession = Session(self.engine)

        self.categories_query = self.dbsession.query(self.Categories)
        self.seasons_query = self.dbsession.query(self.Seasons)
        self.cheques_query = self.dbsession.query(self.Cheques)
        self.transactions_query = self.dbsession.query(self.Transactions)
        self.trybooking_query = self.dbsession.query(self.Trybooking)

    def trybooking_format(self, record):
        return '({},{},{},{},{},{})'.format(
            record.id, record.date,
            record.type, record.description,
            record.debit, record.credit
        )
