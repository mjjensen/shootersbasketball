'''
Created on 7 Jul. 2018

@author: jen117
'''
from __future__ import print_function

import os
from sqlalchemy.ext.automap import automap_base

from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

from sbcilib.config import FINANCEDB_FILE


class SbciFinanceDB(object):
    '''TODO'''

    def __init__(self, verbose=0, *args, **kwds):  # @UnusedVariable
        super(SbciFinanceDB, self).__init__(*args, **kwds)

        if not os.access(FINANCEDB_FILE, os.R_OK | os.W_OK):
            raise RuntimeError('cannot access Finance DB file ({}) for R/W!'
                               .format(FINANCEDB_FILE))

        self.Base = automap_base()

        self.engine = create_engine('sqlite:///' + FINANCEDB_FILE)

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


def trybooking_format(record):
    return '({},{},{},{},{},{},{},{})'.format(
        record.id, record.date,
        record.type, record.booking_id,
        record.description, record.customer,
        record.debit, record.credit
    )


def transactions_format(record):
    return '({},{},{},{},{})'.format(
        record.id, record.date, record.amount,
        record.description, record.balance
    )
