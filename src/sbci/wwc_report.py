from argparse import ArgumentParser
from datetime import datetime
import sys

from sbci import fetch_teams, wwc_check, WWCCheckPerson


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    teams = fetch_teams()

    for t in teams.values():

        if args.verbose:
            print('{} [{}]:'.format(t.sname, t.edjba_id))
            verbose = 2
        else:
            verbose = 0

        if t.tm_name:
            if args.verbose:
                print('\t   Team Manager: {}'.format(t.tm_name))
            dob = datetime.strptime(t.tm_dob.strip(), '%Y-%m-%d %H:%M:%S.%f')
            p = WWCCheckPerson(t.tm_id, t.tm_name, t.tm_wwcnum, dob)
            r = wwc_check(p, verbose)
            print('\t\t- {}'.format(r))

        if t.co_name:
            if args.verbose:
                print('\t          Coach: {}'.format(t.co_name))

        if t.ac_name:
            if args.verbose:
                print('\Assistant Coach: {}'.format(t.ac_name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
