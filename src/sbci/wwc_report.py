from argparse import ArgumentParser
import sys

from sbci import fetch_teams, wwc_check, WWCCheckPerson, to_date


descs = (
    ('Team Manager',    ('tm_id', 'tm_name', 'tm_wwcnum', 'tm_dob')),
    ('Coach',           ('co_id', 'co_name', 'co_wwcnum', 'co_dob')),
    ('Assistant Coach', ('ac_id', 'ac_name', 'ac_wwcnum', 'ac_dob')),
)


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    teams = fetch_teams()

    for t in teams.values():

        if args.verbose:
            print('{} [{}]:'.format(t.sname, t.edjba_id))

        for label, attrs in descs:
            ident, name, wwcnum, dobstr = map(lambda a: getattr(t, a), attrs)
            if args.verbose:
                print('\t{}: {}'.format(label, name))
            dob = to_date(dobstr, '%Y-%m-%d %H:%M:%S.%f')
            res = wwc_check(WWCCheckPerson(ident, name, wwcnum, dob))
            print('\t\t- {}'.format(res))

    return 0


if __name__ == "__main__":
    sys.exit(main())
