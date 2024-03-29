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
    parser.add_argument('teams', nargs='*',
                        help='limit checks to specified teams')
    args = parser.parse_args()

    teams = fetch_teams()

    if args.teams:
        newteams = {}
        for name in args.teams:
            if name not in teams:
                print('unknown team name: {}'.format(name), file=sys.stderr)
                sys.exit(1)
            newteams[name] = teams[name]
        teams = newteams

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
            #     FAILED, SUCCESS, CHANGED, EXPIRED, INVALID, BADRESPONSE
            if args.verbose:
                print('\t{}: {}\t\t- {}'.format(label, name, res))
            if res.status not in (
                WWCCheckStatus.NONE,  # @UndefinedVariable
                WWCCheckStatus.UNKNOWN,  # @UndefinedVariable
                WWCCheckStatus.SUCCESS,  # @UndefinedVariable
                WWCCheckStatus.UNDER18,  # @UndefinedVariable
                WWCCheckStatus.TEACHER,  # @UndefinedVariable
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
