from argparse import ArgumentParser
import sys

from sbci import fetch_teams, wwc_check, WWCCheckPerson, to_date, WWCCheckStatus


descs = (
    ('Manager',   ('tm_id', 'tm_name', 'tm_dob', 'tm_wwcnum', 'tm_wwcname')),
    ('Coach',     ('co_id', 'co_name', 'co_dob', 'co_wwcnum', 'co_wwcname')),
    ('Assistant', ('ac_id', 'ac_name', 'ac_dob', 'ac_wwcnum', 'ac_wwcname')),
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
            ident, name, dobstr, wwcnum, wwcname = map(
                lambda a: getattr(t, a), attrs
            )
            dob = to_date(dobstr, '%Y-%m-%d %H:%M:%S.%f')
            res = wwc_check(
                WWCCheckPerson(ident, name, wwcnum, dob, wwcname),
                args.verbose
            )
            # result is a WWCCheckStatus (IntEnum) and can be one of:
            #     NONE, UNKNOWN, EMPTY, UNDER18, TEACHER, BADNUMBER,
            #     FAILED, SUCCESS, EXPIRED, INVALID, BADRESPONSE
            if args.verbose:
                print('\t{}: {}\t\t- {}'.format(label, name, res))
            if res.status not in (
                WWCCheckStatus.NONE,
                WWCCheckStatus.UNKNOWN,
                WWCCheckStatus.SUCCESS,
                WWCCheckStatus.UNDER18,
                WWCCheckStatus.TEACHER,
            ):
                print(
                    '{} [{}]: {} ({}): {}'.format(
                        t.sname, t.edjba_id, name, label, res
                    ),
                    file=sys.stderr
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
