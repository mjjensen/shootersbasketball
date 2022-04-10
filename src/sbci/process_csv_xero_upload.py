from argparse import ArgumentParser
from csv import DictReader, DictWriter
from datetime import datetime
from json import dumps
import os
import re
import sys

from pupdb.core import PupDB

from sbci import xerodir, latest_report, load_config, to_date


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
    parser.add_argument('--dryrun', '-n', action='store_true',
                        help='dont make any actual changes - just run through')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    reportdir = args.reportdir
    if not os.path.isdir(reportdir):
        reportdir = os.path.join(xerodir, args.reportdir)
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
        xactfile, _ = latest_report(
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

    config = load_config(prefix=xerodir)

    db = PupDB(pupdbfile)

    with open(xactfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        orecs = []

        total_netamount = total_phqfee = total_subtotal = 0.0

        order_numbers = {}
        order_item_ids = {}

        for inrec in reader:
            org = inrec['Organisation']
            role = inrec['Role']
            org_to = inrec['Organisation Registering To']
            pstatus = inrec['Payout Status']

            if (
                org != 'Shooters Basketball Club' or
                role != 'Player' or
                org_to != 'Shooters Basketball Club' or
                pstatus != 'DISBURSED'
            ):
                print(
                    'skip (bad rec): org={}, role={}, org_to={}, '
                    'pstatus={}'.format(
                        org, role, org_to, pstatus
                    ), file=sys.stderr
                )
                continue

            rtype = inrec['Type of Registration']
            rname = inrec['Registration']
            ptype = inrec['Product Type']

            for rdesc in config['types']:
                if (
                    rdesc['rtype'] == rtype and
                    rdesc['rname'] == rname and
                    rdesc['ptype'] == ptype
                ):
                    break
            else:
                print(
                    'skip (bad type): rtype={}, rname={}, ptype={}'.format(
                        rtype, rname, ptype
                    ), file=sys.stderr
                )
                continue

            sname = inrec['Season Name']
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

            if rdesc['rid'] == 'clinic':
                sku = inrec['Merchandise SKU']
                if sku not in rdesc['skus']:
                    print(
                        'skip (bad sku): {} not in {}'.format(
                            sku, rdesc['skus']
                        ), file=sys.stderr
                    )
                    continue
                # Term N, YYYY
                m = re.match(r'^Term ([1-4]), (\d{4})$', sname)
                if m is None:
                    raise RuntimeError(
                        'clinic record has bad season name ({})'.format(sname)
                    )
                tracking1 = rdesc['tracking1'].format(*m.groups())
                tracking2 = rdesc['tracking2']
            elif rdesc['rid'] == 'registration':
                feename = inrec['Fee Name']
                for fdesc in rdesc['fees']:
                    if fdesc['name'] == feename:
                        famount = int(float(fdesc['amount']) * 100)
                        break
                else:
                    print(
                        'skip (bad fee): rtype={}, rname={}, ptype={}'.format(
                            rtype, rname, ptype
                        ), file=sys.stderr
                    )
                    continue
                if quantity != 1:
                    raise RuntimeError('registration with quantity != 1!')
                if famount != oprice:
                    raise RuntimeError(
                        'amount mismatch ({:.2f}!={:.2f})'.format(
                            float(famount) / 100, float(oprice) / 100
                        )
                    )
                # (Winter|Summer) YYYY
                m = re.match(r'^(Winter|Summer) (\d{4})$', sname)
                if m is None:
                    raise RuntimeError(
                        'rego record has bad season name ({})'.format(sname)
                    )
                wors, year = m.groups()
                if wors == 'Summer':
                    year = '{}/{:02d}'.format(year, int(year) - 2000 + 1)
                tracking1 = rdesc['tracking1'].format(year, wors)
                tracking2 = rdesc['tracking2']
            else:
                raise RuntimeError('bad rego id {}!'.format(rdesc['rid']))

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
                'Date': xdate.strftime('%d/%m/%Y'),
                'Amount': '{:.2f}'.format(float(netamount) / 100),
                'Payee': name,
                'Description': '{} - {} - Price {:.2f}, Quantity {:d}'.format(
                    product, sname, float(oprice) / 100, quantity
                ),
                'Reference': pid,
                'Cheque Number': onum,
                'Account code': config['account'],
                'Tax Rate (Display Name)': config['taxrate'],
                'Tracking1': tracking1,
                'Tracking2': tracking2,
                'Transaction Type': 'credit',
                'Analysis code': oid,
                'PlayHQ Fee': '{:.2f}'.format(float(phqfee) / 100),
                'Payout Date': pdate.strftime('%d/%m/%Y'),
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
        print('No records were collected.', file=sys.stderr)
        return 0

    if total_subtotal - total_phqfee != total_netamount:
        raise RuntimeError(
            'total({:.2f})-fees({:.2f})!=net({:.2f})'.format(
                float(total_subtotal) / 100,
                float(total_phqfee) / 100,
                float(total_netamount) / 100
            )
        )

    if args.verbose:
        print('{} records were collected.'.format(len(orecs)), file=sys.stderr)
        print('total subtotal = ${:.2f}'.format(float(total_subtotal) / 100),
              file=sys.stderr)
        print('total phqfee = ${:.2f}'.format(float(total_phqfee) / 100),
              file=sys.stderr)
        print('total netamount = ${:.2f}'.format(float(total_netamount) / 100),
              file=sys.stderr)

    if args.dryrun:
        return 0

    if os.path.exists(xerofile):
        raise RuntimeError('will not overwrite file {}'.format(xerofile))

    with open(xerofile, 'w', newline='') as outfile:
        writer = DictWriter(outfile, fieldnames=orecs[0].keys())
        writer.writeheader()
        for outrec in orecs:
            writer.writerow(outrec)

    for outrec in orecs:
        db.set(outrec['Reference'], dumps(outrec))

    return 0


if __name__ == "__main__":
    sys.exit(main())
