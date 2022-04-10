from argparse import ArgumentParser
from csv import DictReader, DictWriter
from io import TextIOWrapper
from datetime import datetime
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('csvfile',
                        help='csv file containing trybooking transactions')
    args = parser.parse_args()

    with open(args.csvfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        records = []

        for trx in reader:

            date = datetime.strptime(trx['Date'], '%d%b%y %I:%M %p')

            debit = float(trx['Debit'])
            credit = float(trx['Credit'])
            if debit != 0.0:
                if credit != 0.0:
                    raise RuntimeError(
                        'both debit ({}) and credit ({}) non-zero!'.format(
                            debit, credit
                        )
                    )
                amount = -debit
            else:
                if credit == 0.0:
                    raise RuntimeError(
                        'both debit ({}) and credit ({}) zero!'.format(
                            debit, credit
                        )
                    )
                amount = credit

            payee = trx['Customer'].strip().replace('  ', ' ')
            reference = trx['Booking ID'].strip()
            description = trx['Description'].strip()

            record = {
                'Date': date.strftime('%d/%m/%Y'),
                'Amount': amount,
                'Payee': payee,
                'Reference': reference,
                'Description': description,
            }

            if record in records:
                raise RuntimeError('duplicate record: {}'.format(record))

            records.append(record)

    if len(records) == 0:
        raise RuntimeError('no transactions were read!')

    with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:

        writer = DictWriter(outfile, fieldnames=records[0].keys())

        writer.writeheader()

        for record in sorted(records, key=lambda r: r['Date']):

                writer.writerow(record)

    return 0


if __name__ == "__main__":
    sys.exit(main())
