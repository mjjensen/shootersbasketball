from argparse import ArgumentParser
from csv import DictWriter
import sys

from sbci import load_config, fetch_program_participants, first_not_empty


def main():

    parser = ArgumentParser()
    parser.add_argument('--details', '-d', action='store_true',
                        help='print player details')
    parser.add_argument('--report', default=None, metavar='F',
                        help='specify participant report file to use')
    parser.add_argument('--square', default=None, metavar='F',
                        help='write csv upload file of Square customers')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    config = load_config(verbose=args.verbose)

    roles = fetch_program_participants(args.report, args.verbose)

    if args.square is not None:

        fieldnames = [
            'First Name',
            'Surname',
            'Company Name',
            'Email Address',
            'Phone Number',
            'Street Address 1',
            'Street Address 2',
            'City',
            'State',
            'Postal Code',
            'Reference ID',
            'Birthday',
            'Email Subscription Status',
        ]

        with open(args.square, 'w', newline='') as outfile:

            writer = DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for player in roles['Player']:

                if player['season'] != config['label']:
                    if args.verbose:
                        print('ignore out-of-season player: {}'.format(player))
                    continue

                outrec = dict(map(lambda k: (k, None), fieldnames))

                outrec['First Name'] = player['first name']
                outrec['Surname'] = player['last name']
                outrec['Email Address'] = first_not_empty(
                    player['email'],
                    player['parent/guardian1 email'],
                    player['parent/guardian2 email'],
                )
                outrec['Phone Number'] = first_not_empty(
                    player['mobile number'],
                    player['parent/guardian1 mobile number'],
                    player['parent/guardian2 mobile number'],
                )
                outrec['Street Address 1'] = player['address']
                outrec['City'] = player['suburb/town']
                outrec['State'] = player['state/province/region']
                outrec['Postal Code'] = player['postcode']
                outrec['Reference ID'] = player['profile id']
                outrec['Birthday'] = player['date of birth']
                outrec['Email Subscription Status'] = player['opted-in to marketing']

                writer.writerow(outrec)

    return 0


if __name__ == "__main__":
    sys.exit(main())
