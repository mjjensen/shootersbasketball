from argparse import ArgumentParser
from csv import DictReader, DictWriter
from datetime import datetime, date
from io import TextIOWrapper
import os
from pathlib import Path
import sys

from dateutil.parser import parse as dateutil_parse
from six import ensure_str

from sbci import make_phone, clinicdir, load_config, to_date, to_datetime, \
    latest_report


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
    parser.add_argument('--notouch', action='store_true',
                        help='do not touch the reference file')
    parser.add_argument('--basename', default='-', metavar='N',
                        help='basename of output file (- = stdout)')
    parser.add_argument('--asxls', action='store_true',
                        help='output excel data')
    parser.add_argument('--xlsfile', default=None, metavar='F',
                        help='file to to use for xls output')
    parser.add_argument('--email', action='store_true',
                        help='print a list of email addresses')
    parser.add_argument('--ascsv', action='store_true',
                        help='output csv data')
    parser.add_argument('--csvfile', default=None, metavar='F',
                        help='file to to use for csv output')
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

    partfile = args.partfile
    if partfile is None:
        partfile, _ = latest_report('program_participant', reportdir)
        if partfile is None:
            raise RuntimeError('cannot locate program participant file!')
    if args.verbose:
        print(
            '[program participant report file = {} (realpath={})]'.format(
                partfile, os.path.realpath(partfile)
            ), file=sys.stderr
        )

    merchfile = args.merchfile
    if merchfile is None:
        newmerchfile, newdate = latest_report('merchandise_orders', reportdir)
        oldmerchfile, olddate = latest_report(
            'merchandiseorders', reportdir,
            r'^merchandiseorders_(\d{8})\.csv$',
            lambda m: datetime.strptime(m.group(1), '%Y%m%d')
        )
        if newmerchfile:
            if oldmerchfile:
                if olddate < newdate:
                    merchfile = oldmerchfile
                else:
                    merchfile = newmerchfile
            else:
                merchfile = newmerchfile
        elif oldmerchfile:
            merchfile = oldmerchfile
        else:
            raise RuntimeError('cannot locate merchandise order file!')
    if args.verbose:
        print(
            '[merchandise orders report file = {} (realpath={})]'.format(
                merchfile, os.path.realpath(merchfile)
            ), file=sys.stderr
        )

    reffile = args.reffile
    if reffile is None:
        reffile = '.reffile'
        if not os.path.exists(reffile):
            reffile = os.path.join(clinicdir, reffile)
    if args.verbose:
        print(
            '[reference file = {} (realpath={})]'.format(
                reffile, os.path.realpath(reffile)
            ), file=sys.stderr
        )

    if args.refdt is not None:
        refdt = dateutil_parse(args.refdt, dayfirst=True, fuzzy=True)
    else:
        if os.path.exists(reffile):
            refdt = datetime.fromtimestamp(os.stat(reffile).st_mtime)
        else:
            refdt = None
    if args.verbose:
        if refdt is not None:
            print('[reference datetime = {}]'.format(refdt), file=sys.stderr)
        else:
            print('[No reference datetime available!]', file=sys.stderr)

    config = load_config(prefix=clinicdir)

    with open(partfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        orecs = {}

        for inrec in reader:

            role = inrec.get('role', inrec['Role'])
            status = inrec.get('status', inrec['Status'])

            if role != 'Player' or status != 'Active':
                if args.verbose:
                    print(
                        'ignore Non-Player or Inactive rec: {}'.format(inrec),
                        file=sys.stderr
                    )
                continue

            school_term = inrec.get('season', inrec['Season'])
            if school_term != config['label']:
                raise RuntimeError(
                    'School Term mismatch! ({}!={})'.format(
                        school_term, config['label']
                    )
                )

            first_name = inrec.get('first name', inrec['First Name'])
            last_name = inrec.get('last name', inrec['Last Name'])
            name = first_name + ' ' + last_name
            dob_str = inrec.get('date of birth', inrec['Date of Birth'])
            date_of_birth = to_date(dob_str, '%d/%m/%Y')
            gender = inrec.get('gender', inrec['Gender'])[0]
            all_email = [email for email in map(
                lambda key: inrec.get(key, '').strip().lower(),
                (
                    'email',
                    'Account Holder Email',
                    'parent/guardian1 email',
                    'Parent/Guardian1 Email',
                    'Parent/Guardian2 Email',
                    'Emergency Contact Email',
                )
            ) if email]
            email = all_email[0]
            phone = inrec.get('mobile number', inrec['Account Holder Mobile'])
            if not phone:
                phone = inrec.get('parent/guardian1 mobile number',
                                  inrec['Parent/Guardian1 Mobile Number'])
            parent_first_name = inrec.get('parent/guardian1 first name',
                                          inrec['Parent/Guardian1 First Name'])
            parent_last_name = inrec.get('parent/guardian1 last name',
                                          inrec['Parent/Guardian1 Last Name'])
            parent = parent_first_name + ' ' + parent_last_name

            regodt_str = inrec.get('registration date',
                                   inrec['Registration Timestamp'].split()[0])
            regodt = to_datetime(regodt_str, '%d/%m/%Y')
            if refdt is not None and refdt < regodt:
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
                prepaid=[],
                paid=' ',
                gender=gender,
                all_email=all_email,
            )

    if len(orecs) == 0:
        print('No CSV records in "{}"'.format(partfile), file=sys.stderr)
        sys.exit(0)

    with open(merchfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        inrecs = []
        for inrec in reader:
            orderdt = to_datetime(inrec['Order Date'], '%d/%m/%Y')
            name = inrec['First Name'] + ' ' + inrec['Last Name']
            quantity = int(inrec['Quantity'])
            sku = inrec['Merchandise SKU']
            inrecs.append((orderdt, name, quantity, sku))

        for data in sorted(inrecs, key=lambda t: t[0]):
            orderdt, name, quantity, sku = data

            if name not in orecs:
                print('unknown participant {}!'.format(name), file=sys.stderr)
                continue

            if sku.startswith('FULLTERM'):
                if quantity != 1:
                    raise RuntimeError(
                        'quantity for FULLTERM is not 1 ({:d})'.format(quantity)
                    )
                quantity = len(config['dates'])
                if len(sku) > 8 and quantity != int(sku[8:]):
                    raise RuntimeError(
                        '# of dates ({}) does not match sku ({})'.format(
                            quantity, sku
                        )
                    )
                orecs[name]['paid'] = 'Full'
            elif sku != 'SINGLE':
                raise RuntimeError('Unknown SKU {}!'.format(sku))

            if refdt is not None and refdt < orderdt:
                val = 'new'
            else:
                val = 'old'

            for _ in range(quantity):
                orecs[name]['prepaid'].append(val)

    if args.email:
        emails = set()  # using a set() will remove duplicates
        for outrec in orecs.values():
            emails.update(set(outrec['all_email']))
        for email in sorted(emails):
            print(email, file=sys.stderr)

    curdate = date.today().strftime('%Y%m%d')

    if args.ascsv:
        csvfile = args.csvfile
        if csvfile is None:
            csvfile = '{}-registrations.csv'.format(curdate)
        if os.path.exists(csvfile):
            raise RuntimeError('will not overwrite: {}'.format(csvfile))
        fieldnames = [
            'Modified', 'Paid', 'Parent/Guardian', 'Email',
            'Mobile', 'DOB', 'Gender', 'Child\'s Name',
        ]
        with open(csvfile, 'w', newline='') as outfile:
            writer = DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            sorecs = sorted(orecs.values(), key=lambda d: d['name'].lower())
            for outrec in sorecs:
                noutrec = {
                    'Modified': outrec['new'],
                    'Paid': len(outrec['prepaid']),
                    'Parent/Guardian': outrec['parent'],
                    'Email': outrec['email'],
                    'Mobile': outrec['phone'],
                    'DOB': outrec['date_of_birth'],
                    'Gender': outrec['gender'],
                    'Child\'s Name': outrec['name'],
                }
                if 'new' in outrec['prepaid']:
                    noutrec['Modified'] = '*'
                writer.writerow(noutrec)

    if args.asxls:
        xlsfile = args.xlsfile
        if xlsfile is None:
            xlsfile = '{}-registrations.xls'.format(curdate)
        if os.path.exists(xlsfile):
            raise RuntimeError('will not overwrite: {}'.format(xlsfile))
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
            'right': easyxf(
                'font: name Arial, height 280; '
                'align: wrap off, vertical centre, horizontal right; '
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
                'font: name Arial, height 280, colour red; '
                'align: wrap off, vertical centre, horizontal left; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'centred_highlighted': easyxf(
                'font: name Arial, height 280, colour red; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'right_highlighted': easyxf(
                'font: name Arial, height 280, colour red; '
                'align: wrap off, vertical centre, horizontal right; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='@',
            ),
            'currency_highlighted': easyxf(
                'font: name Arial, height 280, colour red; '
                'align: wrap off, vertical centre, horizontal right; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='$#,##0.00',
            ),
            'date_highlighted': easyxf(
                'font: name Arial, height 280, colour red; '
                'align: wrap off, vertical centre, horizontal centre; '
                'borders: left thin, right thin, top thin, bottom thin',
                num_format_str='YYYY-MM-DD',
            ),
            'datetime_highlighted': easyxf(
                'font: name Arial, height 280, colour red; '
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
        for outrec in sorted(orecs.values(), key=lambda d: d['name'].lower()):
            pnum += 1
            r += 1
            if outrec['new'] == '*':
                normal_style = styles['normal_highlighted']
                centred_style = styles['centred_highlighted']
                right_style = styles['right_highlighted']
                ssuf = '_highlighted'
            else:
                normal_style = styles['normal']
                centred_style = styles['centred']
                right_style = styles['right']
                ssuf = ''
            sheet.write(r, 0, str(pnum), right_style)
            sheet.write(r, 1, outrec['paid'], centred_style)
            for c, (k, s) in enumerate(col1styles.items()):
                v = outrec[k]
                s = col1styles[k]
                sheet.write(r, 2 + c, v, styles[s + ssuf])
            i = 0
            for v in outrec['prepaid']:
                if v == 'old':
                    ppstyle = styles['centred']
                else:
                    ppstyle = styles['centred_highlighted']
                sheet.write(r, 2 + c + 1 + i, 'PP', ppstyle)
                i += 1
            while i < ndates - 1:
                sheet.write(r, 2 + c + 2 + i, '  ', centred_style)
                i += 1
            r += 1
            sheet.write(r, 0, '  ', normal_style)
            sheet.write(r, 1, '  ', normal_style)
            for c, (k, s) in enumerate(col2styles.items()):
                v = outrec[k]
                s = col2styles[k]
                sheet.write(r, 2 + c, v, styles[s + ssuf])
            c += 1
            sheet.write(r, 2 + c, '  ', normal_style)
            c += 1
            for i in range(len(config['dates'])):
                sheet.write(r, 2 + c + i, '  ', normal_style)
        book.save(xlsfile)

    if not args.notouch:
        Path(reffile).touch()

    return 0


if __name__ == "__main__":
    sys.exit(main())
