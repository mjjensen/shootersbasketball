from argparse import ArgumentParser
from csv import DictReader
from sbci import latest_report, fetch_teams, find_team, load_config
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    report_file, _ = latest_report('team_entries')
    if report_file is None:
        print('No team_entries reports.')
        sys.exit(1)
    print('[team_entries report selected: {}]'.format(report_file))

    config = load_config(verbose=args.verbose)
    mismatches = config.get('mismatches', {})

    teams = fetch_teams()

    ilst = ('name', 'email', 'mobile')

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for tent in reader:

            team_name = tent.get('team name', tent['Team Name'])
            if not team_name:
                if args.verbose:
                    print('no team name in {}!'.format(tent))
                continue

            t = find_team(teams, edjba_id=team_name)
            if t is None:
                if args.verbose:
                    print('team not found for {}!'.format(team_name))
                continue

            if hasattr(t, 'found'):
                raise RuntimeError('team appears twice in report!!')
            t.found = True

            grade = tent.get('allocated grade', tent['Allocated Grade'])
            # if grade != t.grade:
            #    print(
            #        '    ***** team grade mismatch! ({}!={})'.format(
            #            grade, t.grade
            #        )
            #    )

            print('{} [{}] ({}):'.format(t.sname, t.edjba_code, grade))

            ttype = tent.get('team type', tent['Team Type'])
            if ttype != 'Club':
                print('    ***** team type not Club! ({})'.format(ttype))

            tgen = tent.get('team gender', tent['Team Gender'])
            if tgen.lower() != t.gender.lower():
                print('    ***** team gender mismatch! ({})'.format(tgen))

            # tm1info = [tent['team manager1 ' + k] for k in ilst]
            tm_not_registered = True
            tm_errs = []
            for k in ilst:
                v1 = tent.get('team manager1 ' + k,
                              tent['Team Manager1 ' + k.capitalize()])
                if v1:
                    tm_not_registered = False
                    if k == 'mobile':
                        if v1.startswith('+61'):
                            v1 = '0' + v1[3:]
                        elif not v1.startswith('0'):
                            v1 = '0' + v1
                    else:
                        v1 = v1.lower()
                v2 = getattr(t, 'tm_' + k)
                if v2:
                    v2 = v2.lower()
                if v1 != v2:
                    mm = mismatches.get(k)
                    if not mm or mm.get(v1) != v2:
                        tm_errs.append('    ***** team manager {} mismatch! '
                            '({}!={})'.format(k, v1, v2))
            if tm_not_registered:
                print('    ***** team manager has not registered!')
            else:
                for err in tm_errs:
                    print(err)

            tm2info = [tent.get(
                'team manager2 ' + k, tent['Team Manager2 ' + k.capitalize()]
            ) for k in ilst]
            if any(tm2info):
                print(
                    '    ***** team has 2nd team manager! ({})'.format(tm2info)
                )

    for t in teams.values():
        if not hasattr(t, 'found'):
            print('***** {} was not in report!'.format(t.name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
