from argparse import ArgumentParser
from collections import OrderedDict
from csv import DictReader
from datetime import datetime, timedelta
from dateutil.parser import parse as dateutil_parse
from io import TextIOWrapper
import os
from six import ensure_str
import sys

from sbci import make_address, make_phone, clinicdir, clinicterm, \
    load_config, to_bool, to_date, to_datetime, to_time, latest_report


def main():

    parser = ArgumentParser()
    parser.add_argument('--reportdir', default='reports', metavar='D',
                        help='directory containing report files')
    parser.add_argument('--partfile', default=None, metavar='F',
                        help='csv file containing program participant report')
    parser.add_argument('--merchfile', default=None, metavar='F',
                        help='csv file containing merchandise orders report')
    parser.add_argument('--reffile', default=None, metavar='F',
                        help='file to use as reference for last run')
    parser.add_argument('--refdt', default=None, metavar='T',
                        help='datetime to use as reference for last run')
    parser.add_argument('--basename', default='-', metavar='N',
                        help='basename of output file (- = stdout)')
    parser.add_argument('--asxls', action='store_true',
                        help='output excel data')
    parser.add_argument('--email', action='store_true',
                        help='print a list of email addresses')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    reportdir = args.reportdir
    if not os.path.isdir(reportdir):
        reportdir = os.path.join(clinicdir, args.reportdir)
    if not os.path.isdir(reportdir):
        raise RuntimeError('cannot locate reports directory')
    if args.verbose:
        print(
            '[reports found in directory {} (realpath={})]'.format(
                reportdir, os.path.realpath(reportdir)
            ), file=sys.stderr
        )

    partfile = args.partfile
    if partfile is None:
        partfile, dt = latest_report(
            'program_participant', reportdir, verbose=args.verbose
        )
    if args.verbose:
        print(
            '[program participant report file = {} (realpath={})]'.format(
                partfile, os.path.realpath(partfile)
            ), file=sys.stderr
        )

    merchfile = args.merchfile
    if merchfile is None:
        merchfile, dt = latest_report(
            'merchandiseorders', reportdir, r'^merchandiseorders_(\d{8})\.csv$',
            lambda m: datetime.strptime(m.group(1), '%Y%m%d'), args.verbose
        )
    if args.verbose:
        print(
            '[merchandise orders report file = {} (realpath={})]'.format(
                merchfile, os.path.realpath(merchfile)
            ), file=sys.stderr
        )

    if args.refdt is not None:
        refdt = dateutil_parse(args.refdt, dayfirst=True, fuzzy=True)
    elif args.reffile is not None:
        refdt = datetime.fromtimestamp(os.stat(args.reffile).st_mtime)
    else:
        refdt = None

    if refdt is not None and args.verbose:
        print('[reference datetime: {}]'.format(refdt), file=sys.stderr)

    config = load_config(prefix=clinicdir)

    with open(partfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        orecs = {}

        for inrec in reader:

            if inrec['role'] != 'Player' or inrec['status'] != 'Active':
                if args.verbose:
                    print(
                        'ignore Non-Player or Inactive rec: {}'.format(inrec),
                        file=sys.stderr
                    )
                continue

            school_term = inrec['season']
            if school_term != config['label']:
                raise RuntimeError(
                    'School Term mismatch! ({}!={})'.format(
                        school_term, config['label']
                    )
                )

            name = inrec['first name'] + ' ' + inrec['last name']
            date_of_birth = to_date(inrec['date of birth'], '%d/%m/%Y')
            email = inrec['email']
            if not email:
                email = inrec['parent/guardian1 email']
            phone = inrec['mobile number']
            if not phone:
                phone = inrec['parent/guardian1 mobile number']
            parent = inrec['parent/guardian1 first name'] + ' ' + \
                inrec['parent/guardian1 last name']

            regodt = to_datetime(inrec['registration date'], '%d/%m/%Y')
            if refdt is None or refdt < regodt:
                new = '*'
            else:
                new = ''

            orecs[name] = dict(
                new=new,
                name=name,
                date_of_birth=date_of_birth,
                parent=parent,
                email=email,
                phone=make_phone(phone),
                prepaid=0,
            )

    if len(orecs) == 0:
        print('No CSV records in "{}"'.format(partfile))
        sys.exit(0)

    with open(merchfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        for inrec in reader:
            name = inrec['First Name'] + ' ' + inrec['Last Name']
            quantity = int(inrec['Quantity'])
            sku = inrec['Merchandise SKU']

            if name not in orecs:
                raise RuntimeError('unknown participant {}!'.format(name))

            if sku == 'FULLTERM':
                if quantity != 1:
                    raise RuntimeError(
                        'quantity for FULLTERM is not 1 ({:d})'.format(quantity)
                    )
                orecs[name]['prepaid'] += len(config['dates'])
            elif sku == 'SINGLE':
                orecs[name]['prepaid'] += quantity

    if args.email:
        emails = set()
        for outrec in orecs.values():
            emails.add(outrec['email'].strip().lower())
        for email in sorted(emails):
            print(email)

    if args.asxls:
        from xlwt import Workbook
        from xlwt.Style import easyxf
        headings = [
            '#',
            'Paid',
            'Parent/Guardian Contact Details',
            'DoB/Mobile',
            'Name',
        ]
        headings.extend(config['dates'])
        styles = {
            'heading': easyxf(
                'font: name Arial, height 280, bold on; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'normal': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal left; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'centred': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'currency': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal right; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='$#,##0.00',
            ),
            'date': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='YYYY-MM-DD',
            ),
            'datetime': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='YYYY-MM-DD HH:MM:SS AM/PM',
            ),
            'normal_highlighted': easyxf(
                'font: name Arial, height 280; '
                'pattern: pattern solid, back_colour light_yellow; '
                'align: wrap off, vertical centre, horizontal left; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'centred_highlighted': easyxf(
                'font: name Arial, height 280; '
                'pattern: pattern solid, back_colour light_yellow; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'currency_highlighted': easyxf(
                'font: name Arial, height 280; '
                'pattern: pattern solid, back_colour light_yellow; '
                'align: wrap off, vertical centre, horizontal right; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='$#,##0.00',
            ),
            'date_highlighted': easyxf(
                'font: name Arial, height 280; '
                'pattern: pattern solid, back_colour light_yellow; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='YYYY-MM-DD',
            ),
            'datetime_highlighted': easyxf(
                'font: name Arial, height 280; '
                'pattern: pattern solid, back_colour light_yellow; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='YYYY-MM-DD HH:MM:SS AM/PM',
            ),
        }
        #    Paid    Parent/Guardian Contact Details    Mobile    Name
        col1styles = {
            'parent':        'normal',
            'date_of_birth': 'date',
            'name':          'normal',
        }
        col2styles = {
            'email':         'normal',
            'phone':         'centred',
        }
        book = Workbook()
        sheet = book.add_sheet(config['label'])
        r = 0
        for c, v in enumerate(headings):
            sheet.write(r, c, ensure_str(v), styles['heading'])
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(1)
        sheet.set_remove_splits(True)
        ndates = len(config['dates'])
        pnum = 0
        for outrec in orecs.values():
            pnum += 1
            r += 1
            sheet.write(r, 0, str(pnum), styles['normal'])
            sheet.write(r, 1, ' ', styles['normal'])
            for c, (k, s) in enumerate(col1styles.items()):
                v = outrec[k]
                s = col1styles[k]
                sheet.write(r, 2 + c, v, styles[s])
            for i in range(outrec['prepaid']):
                sheet.write(r, 2 + c + 1 + i, 'PP', styles['normal'])
            while i < ndates - 1:
                sheet.write(r, 2 + c + 2 + i, '  ', styles['normal'])
                i += 1
            r += 1
            for c, (k, s) in enumerate(col2styles.items()):
                v = outrec[k]
                s = col2styles[k]
                sheet.write(r, 2 + c, v, styles[s])
            c += 1
            sheet.write(r, 2 + c, '  ', styles['normal'])
            c += 1
            for i in range(len(config['dates'])):
                sheet.write(r, 2 + c + i, '  ', styles['normal'])
        book.save(sys.stdout.buffer)

    return 0


if __name__ == "__main__":
    sys.exit(main())
