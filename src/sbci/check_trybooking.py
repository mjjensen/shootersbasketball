from argparse import ArgumentParser
from sbci import fetch_teams, fetch_participants, fetch_trybooking, \
    load_config, to_fullname, find_in_tb
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--partreport', '-p', default=None, metavar='F',
                        help='specify participant report file to use')
    parser.add_argument('--tbreport', '-t', default=None, metavar='F',
                        help='specify trybooking report file to use')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    config = load_config()

    teams = fetch_teams()

    fetch_participants(teams, args.partreport, args.verbose)

    tb = fetch_trybooking(config['tbmap'], args.tbreport, args.verbose)

    def match_names(fn1, fn2):
        if fn1.lower() == fn2.lower():
            return True
        else:
            return False

    unpaid = []
    paid = []

    for t in teams.values():

        for p in t.players:

            e = find_in_tb(tb, to_fullname(p['first name'], p['last name']))

            if e is None:
                unpaid.append(p)
            else:
                paid.append(p)

    if paid:
        print('Paid: ({})'.format(len(paid)))
        for p in sorted(
            paid, key=lambda p: to_fullname(p['first name'], p['last name'])
        ):
            print('    {}'.format(to_fullname(p['first name'], p['last name'])))
    if unpaid:
        print('Unpaid: ({})'.format(len(unpaid)))
        for p in sorted(
            unpaid, key=lambda p: to_fullname(p['first name'], p['last name'])
        ):
            print('    {}'.format(to_fullname(p['first name'], p['last name'])))
    if tb['by-name']:
        print('Unknown: ({})'.format(len(tb['by-name'])))
        for fn, e in sorted(tb['by-name'].items(), key=lambda e: e[0]):
            print('    {}'.format(fn))

    return 0


if __name__ == "__main__":
    sys.exit(main())
