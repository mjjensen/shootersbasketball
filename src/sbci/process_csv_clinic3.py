from argparse import ArgumentParser
from collections import OrderedDict
from csv import DictReader, DictWriter
from datetime import datetime, timedelta
from io import TextIOWrapper
from math import isclose
import os
from pathlib import Path
from pupdb.core import PupDB
import sys

from dateutil.parser import parse as dateutil_parse
from six import ensure_str

from sbci import make_address, make_phone, clinicdir, clinicterm, xerodir, \
    load_config, to_bool, to_date, to_datetime, to_time, latest_report
from json import dumps


def main():

    parser = ArgumentParser()
    parser.add_argument('--reportdir', default='reports', metavar='D',
                        help='directory containing report files')
    parser.add_argument('--xactfile', default=None, metavar='F',
                        help='csv file containing financial transaction report')
    parser.add_argument('--xerofile', default=None, metavar='F',
                        help='output csv file for xero pre-coded transactions')
    parser.add_argument('--pupdbfile', default=None, metavar='F',
                        help='json file for pupdb key-value store')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    reportdir = args.reportdir
    if not os.path.isdir(reportdir):
        reportdir = os.path.join(clinicdir, args.reportdir)
    if not os.path.isdir(reportdir):
        raise RuntimeError('cannot locate reports directory!')
    if args.verbose:
        print(
            '[reports found in directory {} (realpath={})]'.format(
                reportdir, os.path.realpath(reportdir)
            ), file=sys.stderr
        )

    xactfile = args.xactfile
    if xactfile is None:
        xactfile, dt = latest_report(
            'transactions', reportdir, r'^transactions_(\d{8})\.csv$',
            lambda m: datetime.strptime(m.group(1), '%Y%m%d'), args.verbose
        )
        if xactfile is None:
            raise RuntimeError('cannot locate transaction file!')
    if args.verbose:
        print(
            '[transaction report file = {} (realpath={})]'.format(
                xactfile, os.path.realpath(xactfile)
            ), file=sys.stderr
        )

    xerofile = args.xerofile
    if xerofile is None:
        xerofile = os.path.join(
            xerodir, datetime.now().strftime('xero-upload-%Y%m%d.csv')
        )
    if args.verbose:
        print(
            '[Xero output csv file = {} (realpath={})]'.format(
                xerofile, os.path.realpath(xerofile)
            ), file=sys.stderr
        )

    pupdbfile = args.pupdbfile
    if pupdbfile is None:
        pupdbfile = os.path.join(xerodir, 'uploaded.json')
    if args.verbose:
        print(
            '[pupdb json file = {} (realpath={})]'.format(
                pupdbfile, os.path.realpath(pupdbfile)
            ), file=sys.stderr
        )

    config = load_config(prefix=clinicdir)

    db = PupDB(pupdbfile)

    with open(xactfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        orecs = []

        total_netamount = total_phqfee = total_subtotal = 0.0

        order_numbers = {}
        order_item_ids = {}

        for inrec in reader:
            role = inrec['Role']
            rtype = inrec['Type of Registration']
            label = inrec['Season Name']
            sku = inrec['Merchandise SKU']
            pstatus = inrec['Payout Status']

            if (
                role != 'Player' or
                rtype != 'Local Program' or
                label != config['label'] or
                sku not in ('SINGLE', 'FULLTERM') or
                pstatus != 'DISBURSED'
            ):
                print(
                    'skip (wrong type): role={}, rtype={}, label={}, '
                    'sku={}, pstatus={}'.format(
                        role, rtype, label, sku, pstatus
                    ), file=sys.stderr
                )
                continue

            xdate = to_date(inrec['Date'], '%d/%m/%Y')
            name = inrec['Name']
            onum = inrec['Order Number']
            oid = inrec['Order Item ID']
            oprice = int(float(inrec['Order Item Price'][1:]) * 100)
            product = inrec['Product Name']
            quantity = int(inrec['Quantity'])
            subtotal = int(float(inrec['Subtotal'][1:]) * 100)
            phqfee = int(float(inrec['PlayHQ Fee'][1:]) * 100)
            netamount = int(float(inrec['Net Amount'][1:]) * 100)
            pdate = to_date(inrec['Payout Date'], '%Y-%m-%d')
            pid = inrec['Payout ID']

            if oprice * quantity != subtotal:
                raise RuntimeError(
                    'oprice({:.2f})*quantity({})!=subtotal({:.2f})'.format(
                        float(oprice) / 100,
                        quantity,
                        float(subtotal) / 100,
                    )
                )
            if subtotal != netamount + phqfee:
                raise RuntimeError(
                    'subtotal({:.2f})!=netamount({:.2f})+phqfee({:.2f})'.format(
                        float(subtotal) / 100,
                        float(netamount) / 100,
                        float(phqfee) / 100,
                    )
                )

            if db.get(pid) is not None:
                print(
                    'skip (already uploaded): name={}, pdate={}, pid={}'.format(
                        name, pdate, pid
                    ), file=sys.stderr
                )
                continue

            total_netamount += netamount
            total_phqfee += phqfee
            total_subtotal += subtotal

            orec = {
                'Date': pdate.strftime('%d/%m/%Y'),
                'Amount': '{:.2f}'.format(float(netamount) / 100),
                'Payee': name,
                'Description': '{} - {}, Price {:.2f}, Quantity {:d}'.format(
                    product, label, float(oprice) / 100, quantity
                ),
                'Reference': onum,
                'Cheque Number': pid,
                'Account code': config['account'],
                'Tax Rate (Display Name)': config['taxrate'],
                'Tracking1': config['tracking1'],
                'Tracking2': config['tracking2'],
                'Transaction Type': None,
                'Analysis code': None,
                'PlayHQ Fee': '{:.2f}'.format(float(phqfee) / 100),
                'Payout ID': pid,
            }

            orecs.append(orec)

            if onum not in order_numbers:
                order_numbers[onum] = []
            elif args.verbose:
                print('duplicate order number {}'.format(onum), file=sys.stderr)
            order_numbers[onum].append(orec)

            if oid not in order_item_ids:
                order_item_ids[oid] = []
            elif args.verbose:
                print('duplicate order item id {}'.format(oid), file=sys.stderr)
            order_item_ids[oid].append(orec)

    if len(orecs) == 0:
        raise RuntimeError('No records were collected.')

    if args.verbose:
        print('total subtotal = ${:.2f}'.format(float(total_subtotal) / 100),
              file=sys.stderr)
        print('total phqfee = ${:.2f}'.format(float(total_phqfee) / 100),
              file=sys.stderr)
        print('total netamount = ${:.2f}'.format(float(total_netamount) / 100),
              file=sys.stderr)

    if total_subtotal - total_phqfee != total_netamount:
        raise RuntimeError(
            'total({:.2f})-fees({:.2f})!=net({:.2f})'.format(
                float(total_subtotal) / 100,
                float(total_phqfee) / 100,
                float(total_netamount) / 100
            )
        )

    if os.path.exists(xerofile):
        raise RuntimeError('will not overwrite file {}'.format(xerofile))

    with open(xerofile, 'w', newline='') as outfile:
        writer = DictWriter(outfile, fieldnames=orecs[0].keys())
        writer.writeheader()
        for outrec in orecs:
            writer.writerow(outrec)

    for outrec in orecs:
        db.set(outrec['Payout ID'], dumps(outrec))

    return 0


if __name__ == "__main__":
    sys.exit(main())
