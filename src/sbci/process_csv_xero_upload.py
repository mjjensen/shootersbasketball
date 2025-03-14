from argparse import ArgumentParser
from csv import DictReader, DictWriter
from datetime import datetime
from decimal import Decimal
from json import dumps, loads
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
    parser.add_argument('--pending', '-p', action='store_true',
                        help='include xacts marked as DISBURSEMENT_PENDING')
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
        # xactfile, _ = latest_report(
        #     'transactions', reportdir,
        #     r'^transactions_(\d{8})\.csv$',
        #     lambda m: datetime.strptime(m.group(1), '%Y%m%d')
        # )
        xactfile, _ = latest_report('transactions')
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

    fieldnames = [
        'Date',
        'Amount',
        'Payee',
        'Description',
        'Reference',
        'Cheque Number',
        'Account code',
        'Tax Rate (Display Name)',
        'Tracking1',
        'Tracking2',
        'Transaction Type',
        'Analysis code',
    ]

    gov_voucher_desc = 'Get Active Kids Voucher Program'

    with open(xactfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        output_records = {}
        already_uploaded = {}

        order_numbers = {}
        order_item_ids = {}

        total_netamount = Decimal('0.00')
        total_phqfee = Decimal('0.00')
        total_subtotal = Decimal('0.00')
        total_pending = Decimal('0.00')
        total_gvapplied = Decimal('0.00')
        total_vapplied = Decimal('0.00')

        for inrec in reader:
            org = inrec['Organisation']
            role = inrec['Role']
            org_to = inrec['Organisation Registering To Name']
            pstatus = inrec['Payout Status']
            netamount = Decimal(inrec['Net Amount'][1:])

            if (
                org != 'Shooters Basketball Club' or
                role != 'Player' or
                org_to != 'Shooters Basketball Club' or
                (
                    pstatus != 'DISBURSED'
                and
                    (not args.pending or pstatus != 'DISBURSEMENT_PENDING')
                )
            ):
                if args.verbose:
                    print(
                        'skip (bad rec): org={}, role={}, org_to={}, '
                        'pstatus={}'.format(
                            org, role, org_to, pstatus
                        ), file=sys.stderr
                    )
                if pstatus == 'DISBURSEMENT_PENDING':
                    total_pending += netamount
                continue

            rtype = inrec.get('Type of Registration',
                              inrec['Type of Transaction'])
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
                raise RuntimeError(
                    'type not found: rtype={}, rname={}, ptype={}'.format(
                        rtype, rname, ptype
                    )
                )

            dfmt = '%d/%m/%Y'

            sname = inrec['Season Name']
            xdate = to_date(inrec['Date'], dfmt)
            name = inrec['First Name'] + ' ' + inrec['Last Name']
            onum = inrec['Order Number']
            oid = inrec['Order Item ID']
            oprice = Decimal(inrec['Order Item Price'][1:])
            gvname = inrec['Government Voucher Name']
            if gvname != '':
                if gvname != 'Get Active Kids':
                    raise RuntimeError('bad gov voucher: {}'.format(gvname))
                sgva = inrec['Government Voucher Amount']
                gvamount = Decimal(sgva[1:])
                if gvamount != Decimal('200.00'):
                    raise RuntimeError(
                        'GAK voucher not $200: {:.2f}'.format(gvamount)
                    )
                sgvaa = inrec['Government Voucher Amount Applied']
                gvapplied = Decimal(sgvaa[1:])
            else:
                gvamount = Decimal('0.00')
                gvapplied = Decimal('0.00')
            product = inrec['Product Name']
            quantity = int(inrec['Quantity'])
            subtotal = Decimal(inrec['Subtotal'][1:])
            phqfee = Decimal(inrec['PlayHQ Fee'][1:])
            pdate = to_date(inrec['Payout Date'], '%Y-%m-%d')
            pid = inrec['Payout ID']

            vname = inrec['Voucher Name']
            if vname:
                vcode = inrec['Voucher Code']
                vamount = Decimal(inrec['Voucher Amount'].lstrip('$'))
                vapplied = Decimal(inrec['Voucher Amount Applied'].lstrip('$'))
                if vamount != vapplied:
                    raise RuntimeError('complete voucher NOT applied!')

                for vdesc in rdesc['vouchers']:
                    if vdesc['code'] == vcode:
                        break
                else:
                    raise RuntimeError('unknown voucher code: {}'.format(vcode))

                if vname != vdesc['name']:
                    raise RuntimeError(
                        'voucher name mismatch: {}!={}'.format(
                            vname, vdesc['name']
                        )
                    )

                vdapplied = Decimal(vdesc['amount'])
                if vapplied != vdapplied:
                    raise RuntimeError(
                        'unexpected voucher amount applied: {}!={}'.format(
                            vapplied, vdapplied
                        )
                    )

                product += ' [{}]'.format(vname)
            else:
                vapplied = Decimal(0.00)

            if rdesc['rid'] == 'clinic':
                sku = inrec['Merchandise SKU']
                if sku not in rdesc['skus']:
                    raise RuntimeError(
                        'sku not found: {} not in {}'.format(
                            sku, rdesc['skus']
                        )
                    )
                # Term N, YYYY
                m = re.match(r'^Term ([1-4]),? (\d{4})$', sname)
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
                        famount = Decimal(fdesc['amount'])
                        break
                else:
                    raise RuntimeError(
                        'fee {} not found: rtype={}, rname={}, ptype={}'.format(
                            feename, rtype, rname, ptype
                        )
                    )
                if quantity != 1:
                    raise RuntimeError('registration with quantity != 1!')
                if famount != oprice:
                    raise RuntimeError(
                        'fee amount mismatch ({:.2f}!={:.2f})'.format(
                            famount, oprice
                        )
                    )
                m = re.match(r'^(Winter|Summer) (\d{4})(/(\d{2}))?$', sname)
                if m is None:
                    raise RuntimeError(
                        'rego record has bad season name ({})'.format(sname)
                    )
                wors, year, _, year2 = m.groups()
                if wors == 'Summer':
                    if int(year2) != int(year) - 2000 + 1:
                        raise RuntimeError(
                            'bad Summer season: {} - year={}, year2={}'.format(
                                sname, year, year2
                            )
                        )
                    year = '{}/{}'.format(year, year2)
                elif wors == 'Winter':
                    if year2 is not None:
                        raise RuntimeError(
                            'bad Winter season: {} - year={}, year2={}'.format(
                                sname, year, year2
                            )
                        )
                else:
                    raise RuntimeError('bad season name: {}'.format(sname))
                tracking1 = rdesc['tracking1'].format(year, wors)
                tracking2 = rdesc['tracking2']
            else:
                raise RuntimeError('bad rego id {}!'.format(rdesc['rid']))

            if (oprice - gvapplied - vapplied) * quantity != subtotal:
                raise RuntimeError(
                    'oprice({:.2f})*quantity({})!=subtotal({:.2f})'.format(
                        oprice, quantity, subtotal
                    )
                )
            if subtotal != netamount + phqfee:
                raise RuntimeError(
                    'subtotal({:.2f})!=netamount({:.2f})+phqfee({:.2f})'.format(
                        subtotal, netamount, phqfee,
                    )
                )

            if subtotal == Decimal(0.00):
                raise RuntimeError('zero value transaction!')

            if onum not in order_numbers:
                order_numbers[onum] = []
            else:
                print(
                    'multiple records for order number {}'.format(onum),
                    file=sys.stderr
                )
            order_numbers[onum].append(inrec)

            if oid in order_item_ids:
                raise RuntimeError('duplicate order item id {}!'.format(oid))
            order_item_ids[oid] = inrec

            if db.get(pid) is not None:
                is_already_uploaded = True
                if pid not in already_uploaded:
                    already_uploaded[pid] = []

                if args.verbose:
                    print(
                        'already uploaded: name={}, pdate={}, pid={}'.format(
                            name, pdate, pid
                        ), file=sys.stderr
                    )
            else:
                is_already_uploaded = False
                if pid not in output_records:
                    output_records[pid] = []

                total_netamount += netamount
                total_phqfee += phqfee
                total_subtotal += subtotal
                total_gvapplied += gvapplied
                total_vapplied += vapplied

            desc = '{} - ${:.2f} x {:d}'.format(product, oprice, quantity)

            orec = {
                'Date': xdate.strftime(dfmt),
                'Amount': '{:.2f}'.format(subtotal),
                'Payee': name,
                'Description': '{}: subtotal'.format(desc),
                'Reference': '{} on {}'.format(pid, pdate.strftime(dfmt)),
                'Cheque Number': onum,
                'Account code': config['sales_account'],
                'Tax Rate (Display Name)': config['taxrate'],
                'Tracking1': tracking1,
                'Tracking2': tracking2,
                'Transaction Type': 'credit',
                'Analysis code': oid,
            }
            if is_already_uploaded:
                already_uploaded[pid].append(orec)
            else:
                output_records[pid].append(orec)

            if phqfee != Decimal('0.00'):
                orec = {
                    'Date': xdate.strftime(dfmt),
                    'Amount': '-{:.2f}'.format(phqfee),
                    'Payee': name,
                    'Description': '{}: playhq fees'.format(desc),
                    'Reference': '{} on {}'.format(pid, pdate.strftime(dfmt)),
                    'Cheque Number': onum,
                    'Account code': config['fees_account'],
                    'Tax Rate (Display Name)': config['taxrate'],
                    'Tracking1': tracking1,
                    'Tracking2': tracking2,
                    'Transaction Type': 'debit',
                    'Analysis code': oid,
                }
                if is_already_uploaded:
                    already_uploaded[pid].append(orec)
                else:
                    output_records[pid].append(orec)

            if gvapplied != Decimal('0.00'):
                orec = {
                    'Date': xdate.strftime(dfmt),
                    'Amount': '{:.2f}'.format(gvapplied),
                    'Payee': gov_voucher_desc,
                    'Description': '{}: get active for {}'.format(desc, name),
                    'Reference': '{} on {}'.format(pid, pdate.strftime(dfmt)),
                    'Cheque Number': onum,
                    'Account code': config['other_revenue_account'],
                    'Tax Rate (Display Name)': config['taxrate'],
                    'Tracking1': tracking1,
                    'Tracking2': tracking2,
                    'Transaction Type': 'credit',
                    'Analysis code': oid,
                }
                if is_already_uploaded:
                    already_uploaded[pid].append(orec)
                else:
                    output_records[pid].append(orec)

    for pid, oreclist1 in already_uploaded.items():

        total_amount1 = sum(Decimal(orec['Amount']) for orec in oreclist1
                            if orec['Payee'] != gov_voucher_desc)

        dbval = db.get(pid)
        if dbval is None:
            raise RuntimeError('db get of pid {} failed!'.format(pid))
        oreclist2 = loads(dbval)
        if not isinstance(oreclist2, list):
            if args.verbose:
                print(
                    'cannot check old record: pid={}, amount=${:.2f}'.format(
                        pid, total_amount1
                    ), file=sys.stderr
                )
            continue

        total_amount2 = sum(Decimal(orec['Amount']) for orec in oreclist2
                            if orec['Payee'] != gov_voucher_desc)

        if total_amount1 != total_amount2:
            raise RuntimeError(
                'pid {} total amount mismatch (${:.2f} != ${:.2f})!'.format(
                    pid, total_amount1, total_amount2
                )
            )

        if args.verbose:
            print(
                'checked already uploaded: pid={}, amount=${:.2f}'.format(
                    pid, total_amount1
                ),
                file=sys.stderr
            )

    if total_pending > 0:
        print('total pending = ${:.2f}'.format(total_pending), file=sys.stderr)

    if len(output_records) == 0:
        print('No records were collected.', file=sys.stderr)
        return 0

    if total_subtotal - total_phqfee != total_netamount:
        raise RuntimeError(
            'total({:.2f})-fees({:.2f})!=net({:.2f})'.format(
                total_subtotal, total_phqfee, total_netamount
            )
        )

    print(
        '{} payment ids were collected.'.format(len(output_records)),
        file=sys.stderr
    )
    print('subtotal = ${:.2f}'.format(total_subtotal), file=sys.stderr)
    print('phqfee = ${:.2f}'.format(total_phqfee), file=sys.stderr)
    print('netamount = ${:.2f}'.format(total_netamount), file=sys.stderr)
    print('gov vouchers = ${:.2f}'.format(total_gvapplied), file=sys.stderr)
    print('disc vouchers = ${:.2f}'.format(total_vapplied), file=sys.stderr)

    for pid, oreclist in output_records.items():
        amount = Decimal(0.0)
        for outrec in oreclist:
            if outrec['Payee'] != gov_voucher_desc:
                amount += Decimal(outrec['Amount'])
        print(
            '    Payment Id {} = ${:.2f}{}'.format(
                pid, amount,
                ' (excluded)' if pid in config['exclude'] else ''
            ),
            file=sys.stderr
        )

    if args.dryrun:
        return 0

    if os.path.exists(xerofile):
        raise RuntimeError('will not overwrite file {}'.format(xerofile))

    with open(xerofile, 'w', newline='') as outfile:
        writer = DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for pid, oreclist in output_records.items():
            if pid in config['exclude']:
                continue
            for outrec in oreclist:
                writer.writerow(outrec)

    for pid, oreclist in output_records.items():
        if pid not in config['exclude']:
            db.set(pid, dumps(oreclist))

    return 0


if __name__ == "__main__":
    sys.exit(main())
