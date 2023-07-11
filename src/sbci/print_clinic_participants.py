from argparse import ArgumentParser
from csv import DictWriter
import sys

from sbci import load_config, fetch_program_participants, first_not_empty, \
    to_date, to_bool


def main():

    parser = ArgumentParser()
    parser.add_argument('--details', '-d', action='store_true',
                        help='print player details')
    parser.add_argument('--report', default=None, metavar='F',
                        help='specify participant report file to use')
    parser.add_argument('--square', default=None, metavar='F',
                        help='write csv upload file of Square customers')
    parser.add_argument('--email', '-e', action='store_true',
                        help='print email list')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    config = load_config(verbose=args.verbose)

    roles = fetch_program_participants(args.report, args.verbose)

    if args.email:
        email_list = []

        def extract_emails(p):
            for a in 'email', 'parent1_email', 'parent2_email':
                v = getattr(p, a)()
                if v is None or len(v) == 0:
                    continue
                e = v.lower()
                if e not in email_list:
                    email_list.append(e)

    for p in roles['Player']:

        if p.season() != config['label']:
            if args.verbose:
                print('ignore out-of-season player: {}'.format(p.full_name()))
            continue

        if args.email:
            extract_emails(p)
        else:
            print('{:20}'.format(p.full_name()))

    if args.email:
        for e in sorted(email_list):
            print(e)

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

            for p in roles['Player']:

                if p.season() != config['label']:
                    if args.verbose:
                        print(
                            'ignore out-of-season player: {}'.format(
                                p.full_name()
                            )
                        )
                    continue

                outrec = dict(map(lambda k: (k, None), fieldnames))

                outrec['First Name'] = p.first_name()
                outrec['Surname'] = p.last_name()
                outrec['Email Address'] = first_not_empty(
                    p.email(),
                    p.parent1_email(),
                    p.parent2_email(),
                )
                outrec['Phone Number'] = first_not_empty(
                    p.mobile(),
                    p.parent1_mobile(),
                    p.parent2_mobile(),
                )
                outrec['Street Address 1'] = p.address()
                outrec['City'] = p.suburb()
                outrec['State'] = p.state()
                outrec['Postal Code'] = p.postcode()
                outrec['Reference ID'] = p.profile_id()
                outrec['Birthday'] = \
                    to_date(p.date_of_birth()).strftime('%Y-%m-%d')
                outrec['Email Subscription Status'] = \
                    'subscribed' if to_bool(p.opted_in()) \
                    else 'unsubscribed'

                writer.writerow(outrec)

    return 0


if __name__ == "__main__":
    sys.exit(main())
