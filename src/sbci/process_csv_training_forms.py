from argparse import ArgumentParser
from csv import DictReader, DictWriter
from io import TextIOWrapper
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('csvfile',
                        help='csv file containing training feedback form input')
    args = parser.parse_args()

    with open(args.csvfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:

            writer = DictWriter(
                outfile, fieldnames=[
                    'Name', 'Code',
                    'Day1', 'Venue1', 'Slot1',
                    'Day2', 'Venue2', 'Slot2',
                    'Info',
                ]
            )

            writer.writeheader()

            for response in reader:

                code, name = response['Team Name'].split(' - ')

                day1, venue1, slot1 = \
                    response['First Nominated Training Spot'].split(' - ')

                day2, venue2, slot2 = \
                    response['Second Nominated Training Spot'].split(' - ')

                info = response['Additional Information']

                writer.writerow(
                    {
                        'Name': name,
                        'Code': code,
                        'Day1': day1,
                        'Venue1': venue1,
                        'Slot1': slot1,
                        'Day2': day2,
                        'Venue2': venue2,
                        'Slot2': slot2,
                        'Info': info,
                    }
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
