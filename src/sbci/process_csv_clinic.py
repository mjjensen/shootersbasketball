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
    cliniclabel, get_reports, load_config, to_bool, to_date, to_datetime, \
    to_time


def booking_data(inrec):
    parent = inrec['Booking First Name'] + ' ' + \
        inrec['Booking Last Name']
    address = make_address(
        inrec['Booking Address 1'],
        inrec['Booking Address 2'],
        inrec['Booking Suburb'],
        inrec['Booking Post Code'],
    )
    phone = inrec['Booking Telephone']
    email = inrec['Booking Email']
    return parent, address, phone, email


def ticket_data(inrec):
    parent = inrec['Ticket Data: Parent/Guardian Name']
    address = inrec['Ticket Data: Parent/Guardian Address']
    phone = inrec['Ticket Data: Parent/Guardian Phone']
    email = inrec['Ticket Data: Parent/Guardian Email']
    return parent, address, phone, email


def main():

    parser = ArgumentParser()
    parser.add_argument('--csvfile', default=None, metavar='F',
                        help='csv file containing trybooking report')
    parser.add_argument('--reffile', default=None, metavar='F',
                        help='file to use as reference for last run')
    parser.add_argument('--refdt', default=None, metavar='D',
                        help='datetime to use as reference for last run')
    parser.add_argument('--basename', default='-', metavar='S',
                        help='basename of output file (- = stdout)')
    parser.add_argument('--ascsv', action='store_true',
                        help='output csv data (no highlighting)')
    parser.add_argument('--ashtml', action='store_true',
                        help='output html data')
    parser.add_argument('--asxls', action='store_true',
                        help='output excel data')
    parser.add_argument('--email', action='store_true',
                        help='print a list of email addresses')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    if args.csvfile is not None:
        csvfile = args.csvfile
        reffile = args.reference
    else:
        def repkey(e):
            _, m = e
            dstr, suff = m.groups()
            dt = datetime.strptime(dstr, '%d%m%Y')
            if suff is not None:
                dt += datetime.timedelta(seconds=int(suff[1:]))
            return dt
        rlist = sorted(
            get_reports(None, clinicdir, r'^(\d{8})(-\d)?.csv$', args.verbose),
            key=repkey,
        )
        try:
            csvfile = os.path.join(clinicdir, rlist.pop()[0])
        except IndexError:
            raise RuntimeError('No Trybooking reports found!')
        try:
            reffile = os.path.join(clinicdir, rlist.pop()[0])
        except IndexError:
            reffile = None

    if args.verbose:
        print(
            '[trybooking report file: {}]'.format(csvfile),
            file=sys.stderr
        )
        if reffile is not None:
            print(
                '[reference datetime file: {}]'.format(reffile),
                file=sys.stderr
            )

    if args.refdt is not None:
        refdt = dateutil_parse(args.refdt, dayfirst=True, fuzzy=True)
    elif reffile is not None:
        refdt = datetime.fromtimestamp(os.stat(reffile).st_mtime)
    else:
        refdt = None

    if refdt is not None and args.verbose:
        print('[reference datetime: {}]'.format(refdt), file=sys.stderr)

    config = load_config(prefix=clinicdir)

    with open(csvfile, 'r', newline='') as infile:

        _ = infile.read(1)

        reader = DictReader(infile)

        orecs = []

        for inrec in reader:

            if to_bool(inrec['Void']):
                if args.verbose:
                    print(
                        'ignore VOID record: {}'.format(inrec),
                        file=sys.stderr
                    )
                continue

            school_term = inrec['Ticket Data: School Term']
            if school_term != cliniclabel:
                raise RuntimeError(
                    'School Term mismatch! ({}!={})'.format(
                        school_term, clinicterm
                    )
                )

            name = inrec['Ticket Data: Player\'s First Name'] + ' ' + \
                inrec['Ticket Data: Player\'s Surname']
            date_of_birth = to_date(
                inrec['Ticket Data: Player\'s Date-of-Birth'], '%Y-%m-%d'
            )
            paid = float(inrec['Net Booking'])
            medical = inrec[
                'Ticket Data: Special Requirements/Medical Conditions'
            ].strip()

            isparent = to_bool(
                inrec['Ticket Data: Is Purchaser the child\'s Parent/Guardian']
            )
            if isparent:
                parent_data = booking_data(inrec)
            else:
                parent_data = ticket_data(inrec)
                if not any(parent_data):
                    # they answered No to isparent, but did not fill in
                    # parent ticket data - use the booking data instead ...
                    parent_data = booking_data(inrec)
                    print(
                        'empty ticket data - using booking data ({})'.format(
                            parent_data
                        ),
                        file=sys.stderr
                    )
            parent, address, phone, email = parent_data

            # "27Apr21","1:58:48 PM"
            dbdt = to_datetime(inrec['Date Booked (UTC+10)'], '%d%b%y')
            tbt = to_time(inrec['Time Booked'], '%I:%M:%S %p')
            booked = dbdt + timedelta(
                hours=tbt.hour, minutes=tbt.minute, seconds=tbt.second
            )
            if refdt is None or refdt < booked:
                new = '*'
            else:
                new = ''

            orecs.append(
                OrderedDict(
                    new=new,
                    paid=paid,
                    name=name,
                    date_of_birth=date_of_birth,
                    parent=parent,
                    email=email,
                    phone=make_phone(phone),
                    address=address.title().replace('\n', ', '),
                    medical=medical,
                    booked=booked,
                )
            )

    if args.email:
        emails = set()
        for outrec in orecs:
            emails.add(outrec['email'].strip().lower())
        for email in sorted(emails):
            print(email)

    if len(orecs) == 0:
        print('No CSV records in "{}"'.format(csvfile))
        sys.exit(0)

    if args.ascsv:
        from csv import DictWriter
        with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:
            writer = DictWriter(outfile, fieldnames=orecs[0].keys())
            writer.writeheader()
            for outrec in orecs:
                writer.writerow(outrec)

    if args.ashtml:
        raise NotImplementedError('html output not implemented!')

    if args.asxls:
        from xlwt import Workbook
        from xlwt.Style import easyxf
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
        colstyles = {
            'new':           'centred',
            'paid':          'currency',
            'name':          'normal',
            'date_of_birth': 'date',
            'parent':        'normal',
            'email':         'normal',
            'phone':         'centred',
            'address':       'normal',
            'medical':       'normal',
            'booked':        'datetime',
        }
        book = Workbook()
        sheet = book.add_sheet(config['label'])
        r = 0
        for c, v in enumerate(orecs[0].keys()):
            sheet.write(r, c, ensure_str(v), styles['heading'])
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(1)
        sheet.set_remove_splits(True)
        for outrec in orecs:
            r += 1
            is_new = outrec['new'] == '*'
            for c, (k, v) in enumerate(outrec.items()):
                if k == 'address':
                    v = v.replace('\n', ', ')
                s = colstyles[k]
                if is_new:
                    s += '_highlighted'
                sheet.write(r, c, v, styles[s])
        book.save(sys.stdout.buffer)

    return 0


if __name__ == "__main__":
    sys.exit(main())
