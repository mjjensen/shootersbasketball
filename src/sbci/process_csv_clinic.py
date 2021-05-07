from argparse import ArgumentParser
from csv import DictReader, DictWriter
from datetime import datetime
from io import TextIOWrapper
import os
import sys

from sbci import make_address, make_phone, clinicdir, clinicterm, \
    cliniclabel, get_reports


def main():

    parser = ArgumentParser()
    parser.add_argument('--csvfile', '-C', default=None, metavar='F',
                        help='csv file containing trybooking report')
    parser.add_argument('--reffile', '-R', default=None, metavar='F',
                        help='file to use as reference for last run')
    parser.add_argument('--ascsv', '-c', action='store_true',
                        help='output csv data (no highlighting)')
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
            '[trybooking report selected: {}]'.format(csvfile),
            file=sys.stderr
        )
        if reffile is not None:
            print(
                '[reference file selected: {}]'.format(reffile),
                file=sys.stderr
            )

    with open(csvfile, 'r', newline='') as infile:

        _ = infile.read(1)

        reader = DictReader(infile)

        orecs = []

        for inrec in reader:

            if inrec['Void'] == 'Yes':
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
            date_of_birth = inrec['Ticket Data: Player\'s Date-of-Birth']
            paid = inrec['Net Booking']
            medical = inrec[
                'Ticket Data: Special Requirements/Medical Conditions'
            ]

            isparent = (
                inrec['Ticket Data: Is Purchaser the child\'s Parent/Guardian']
                ==
                'Yes'
            )
            if isparent:
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
            else:
                parent = inrec['Ticket Data: Parent/Guardian Name']
                address = inrec['Ticket Data: Parent/Guardian Address']
                phone = inrec['Ticket Data: Parent/Guardian Phone']
                email = inrec['Ticket Data: Parent/Guardian Email']

            orecs.append(
                dict(
                    paid=paid,
                    name=name,
                    date_of_birth=date_of_birth,
                    parent=parent,
                    email=email,
                    phone=make_phone(phone),
                    address=address.title(),
                    medical=medical,
                )
            )

    if len(orecs) == 0:
        print('No CSV records in "{}"'.format(csvfile))
        sys.exit(0)

    if args.ascsv:
        with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:
            writer = DictWriter(outfile, fieldnames=orecs[0].keys())
            writer.writeheader()
            for outrec in orecs:
                writer.writerow(outrec)
    else:
        raise NotImplementedError('html/xls output not implemented!')

    return 0


if __name__ == "__main__":
    sys.exit(main())
