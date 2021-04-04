from argparse import ArgumentParser
from csv import DictReader
from sbci import latest_report, fetch_teams, find_team
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

    teams = fetch_teams()

    ilst = ('name', 'email', 'mobile')

    mismatches = {
        'name': {
            'megan fairbank': 'megan grimmer',
            'nat power': 'natalie power',
        },
    }

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for tent in reader:

            team_name = tent['team name']
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

            grade = tent['allocated grade']
            # if grade != t.grade:
            #    print(
            #        '    ***** team grade mismatch! ({}!={})'.format(
            #            grade, t.grade
            #        )
            #    )

            print('{} [{}] ({}):'.format(t.sname, t.edjba_code, grade))

            ttype = tent['team type']
            if ttype != 'Club':
                print('    ***** team type not Club! ({})'.format(ttype))

            tgen = tent['team gender']
            if tgen.lower() != t.gender.lower():
                print('    ***** team gender mismatch! ({})'.format(tgen))

            # tm1info = [tent['team manager1 ' + k] for k in ilst]
            for k in ilst:
                v1 = tent['team manager1 ' + k]
                if v1:
                    if k == 'mobile':
                        v1 = '0' + v1
                    else:
                        v1 = v1.lower()
                v2 = getattr(t, 'tm_' + k)
                if v2:
                    v2 = v2.lower()
                if v1 != v2:
                    mm = mismatches.get(k)
                    if mm and mm.get(v1) == v2:
                        pass
                    else:
                        print(
                            '    ***** team manager {} mismatch! '
                            '({}!={})'.format(k, v1, v2)
                        )

            tm2info = [tent['team manager2 ' + k] for k in ilst]
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
