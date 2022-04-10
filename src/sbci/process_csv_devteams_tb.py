from argparse import ArgumentParser
from csv import DictReader, DictWriter
from datetime import datetime
from io import TextIOWrapper
import sys

from sbci import latest_report, make_address, make_phone, develdir


def main():

    parser = ArgumentParser()
    parser.add_argument('--csvfile', '-c', default=None, metavar='F',
                        help='csv file containing trybooking report')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    csvinput = args.csvfile
    if csvinput is None:
        csvinput, _ = latest_report(
            None, rdir=develdir,
            nre=r'^(\d{8}).csv$',
            n2dt=lambda m: datetime.strptime(m.group(1), '%d%m%Y'),
            verbose=args.verbose
        )
        if csvinput is None:
            raise RuntimeError('no trybooking report found!')
        if args.verbose:
            print(
                '[trybooking report selected: {}]'.format(csvinput),
                file=sys.stderr
            )

    with open(csvinput, 'r', newline='') as infile:

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

            name = inrec['Ticket Data: Player\'s First Name'] + ' ' + \
                inrec['Ticket Data: Player\'s Surname']
            date_of_birth = inrec['Ticket Data: Player\'s Date-of-Birth']
            paid = inrec['Net Booking']
            medical = inrec[
                'Ticket Data: Special Requirements/Medical Conditions'
            ]

            isparent = (
                inrec['Ticket Data: Purchaser is Player\'s Parent/Guardian']
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
        print('No CSV records in "{}"'.format(csvinput))
        sys.exit(0)

    with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:

        writer = DictWriter(outfile, fieldnames=orecs[0].keys())

        writer.writeheader()

        for outrec in orecs:

            writer.writerow(outrec)

    return 0


if __name__ == "__main__":
    sys.exit(main())
