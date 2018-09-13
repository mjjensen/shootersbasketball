#!/usr/bin/env python2.7
# encoding: utf-8
'''
cbtrximport -- import Commbank Transactions CSV report file(s)

import Commbank Transactions CSV report file(s)
--
@version:    0.1
@created:    2016-04-29
@author:     Murray Jensen
@copyright:  2016 Murray Jensen. All rights reserved.
@license:    Apache License 2.0
@contact:    mjj@jensen-williams.id.au
$Date$
$Author$
$Revision$
'''
from __future__ import print_function

import os
import sys
import traceback

from sbcilib.commbank import cb_trx_csvinfo
from sbcilib.financedb import SbciFinanceDB, transactions_format
from sbcilib.utils import SbciMain, read_csv, deduplicate


class Main(SbciMain):

    def define_args(self):
        super(Main, self).define_args()

        self.parser.add_argument(
            '--dryrun', '-n',
            action='store_true',
            help='do not change the database [default: %(default)s]')

        self.parser.add_argument('csvlist', nargs='+')

    def main(self):
        if self.args.verbose > 0:
            print('CSV file list = {}'.format(self.args.csvlist))
            if self.args.dryrun:
                print('Dry run! Will not modify database.')

        try:
            csvrecords = []
            for csvfile in self.args.csvlist:
                csvrecords.extend(
                    read_csv(csvfile, cb_trx_csvinfo, self.args.verbose)
                )
        except BaseException as e:
            print('Caught exception {} reading CSV files'
                  .format(e), file=sys.stderr)
            return os.EX_SOFTWARE

        csvrecords = deduplicate(csvrecords)

        try:
            db = SbciFinanceDB(self.args.verbose)
        except BaseException as e:
            print('Caught exception {} opening database'
                  .format(e), file=sys.stderr)
            return os.EX_SOFTWARE

        try:
            duplicates = 0

            for csvrecord in sorted(csvrecords, key=lambda r: r.date):

                if self.args.verbose > 3:
                    print('CSV Record: {}'.format(csvrecord))

                maybe_dups = db.transactions_query.filter(
                    db.Transactions.amount == csvrecord.amount,
                    db.Transactions.description == csvrecord.description,
                    db.Transactions.balance == csvrecord.balance,
                ).all()

                found_dup = False
                prev_dup = None

                for maybe_dup in maybe_dups:

                    if self.args.verbose > 3:
                        print('Compare with: {} ...'.format(maybe_dup))

                    if maybe_dup.date.date() == csvrecord.date:

                        if found_dup:
                            raise RuntimeError(
                                'matched more than one! {} and {}'.format(
                                    transactions_format(prev_dup),
                                    transactions_format(maybe_dup)
                                )
                            )

                        if maybe_dup.date != csvrecord.date:
                            if self.args.dryrun:
                                if self.args.verbose > 1:
                                    print('(dryrun) Need to update date: '
                                          '{} => {}'.format(maybe_dup.date,
                                                            csvrecord.date))
                            else:
                                if self.args.verbose > 1:
                                    print('Updated date: {} => {}'.format(
                                        maybe_dup.date, csvrecord.date))

                                maybe_dup.date = csvrecord.date

                        found_dup = True
                        prev_dup = maybe_dup

                if found_dup:
                    if self.args.verbose > 2:
                        print('DUPLICATE!! {}'.format(csvrecord))
                    duplicates += 1
                else:
                    if self.args.dryrun:
                        if self.args.verbose > 0:
                            print('(dryrun) NEW RECORD: {}'.format(csvrecord))
                    else:
                        if self.args.verbose > 0:
                            print('NEW RECORD: {}'.format(csvrecord), end='')
                        dbrec = db.Transactions(
                            date=csvrecord.date,
                            amount=csvrecord.amount,
                            description=csvrecord.description.encode('utf-8'),
                            balance=csvrecord.balance
                        )
                        db.dbsession.add(dbrec)
                        if self.args.verbose > 0:
                            print(' => ID {}'.format(dbrec.id))

            db.dbsession.commit()
            return os.EX_OK

        except BaseException as e:
            print('Caught exception {} while updating database.'
                  .format(e), file=sys.stderr)
            traceback.print_exc(file=sys.stdout)
            db.dbsession.rollback()
            return os.EX_SOFTWARE


def main():
    '''function suitable for running via setuptools entry point'''
    return Main.setuptools_entry()


if __name__ == '__main__':
    sys.exit(main())
