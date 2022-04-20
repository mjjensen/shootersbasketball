from argparse import ArgumentParser
from collections import OrderedDict
from csv import DictReader
from datetime import date, time
from sbci import fetch_teams, find_team, latest_report
import sys
from time import strptime


def main():

    parser = ArgumentParser()
    parser.add_argument('--club', '-c', default='Fairfield-Shooters',
                        help='change club id')
    parser.add_argument('--summary', '-R', action='store_true',
                        help='print results summary')
    parser.add_argument('--upcoming', '-F', action='store_true',
                        help='print results summary')
    parser.add_argument('--html', '-H', action='store_true',
                        help='print html instead of csv')
    parser.add_argument('--nrounds', '-n', type=int, default=0, metavar='N',
                        help='specify report file to use')
    parser.add_argument('--report', '-r', default=None, metavar='F',
                        help='specify report file to use')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    teams = fetch_teams()

    def result(roundno, grade, team_name, score_for=None, score_against=None):
        t = find_team(teams, edjba_id=team_name)
        if t is None:
            print('team {} not found!'.format(team_name), file=sys.stderr)
            sys.exit(1)
        if not hasattr(t, 'results'):
            t.results = OrderedDict()
        if score_for is None:
            value = None
        else:
            value = score_for, score_against
        if (roundno, grade) in t.results:
            raise RuntimeError('duplicate game: {}, {}'.format(roundno, grade))
        t.results[roundno, grade] = value

    report_file = args.report
    if report_file is None:
        report_file, _ = latest_report('advanced_fixture')
        if report_file is None:
            raise RuntimeError('no advanced fixture report found!')
        if args.verbose:
            print(
                '[advanced fixture report selected: {}]'.format(report_file),
                file=sys.stderr
            )

    if args.upcoming:
        print('grade,team1,team2')

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for r in reader:

            _gdate = date(*strptime(r['game date'], '%d/%m/%Y')[:3])
            grade = r['grade']
            roundno = r['round']
            status = r['game status']
            bye = r['bye']
            team_a_name = r['team a']
            team_b_name = r['team b']
            _venue = r['venue']
            if not r['time']:
                _gtime = time()
            else:
                _gtime = time(*strptime(r['time'], '%H:%M:%S')[3:5])

            if status == 'UPCOMING':
                if args.upcoming:
                    if team_a_name.startswith('Fairfield'):
                        t = find_team(teams, edjba_id=team_a_name)
                        xa = ' [' + t.name[9:] + ']'
                    else:
                        xa = ''
                    if team_b_name.startswith('Fairfield'):
                        t = find_team(teams, edjba_id=team_b_name)
                        xb = ' [' + t.name[9:] + ']'
                    else:
                        xb = ''
                    print(
                        '{},{}{},{}{}'.format(
                            grade,
                            team_a_name, xa,
                            team_b_name, xb,
                        )
                    )
                continue

            if bye:
                result(roundno, grade, bye)
            else:
                team_a_score = r['team a score']
                _team_a_result = r['team a result']
                team_b_score = r['team b score']
                _team_b_result = r['team b result']

                if team_a_name.startswith(args.club):
                    result(
                        roundno, grade, team_a_name, team_a_score, team_b_score
                    )
                if team_b_name.startswith(args.club):
                    result(
                        roundno, grade, team_b_name, team_b_score, team_a_score
                    )

    results = []
    for t in teams.values():
        e = [t.sname, t.edjba_code, t.grade]
        rcnt = totfor = totag = totmarg = 0
        for (r, _), v in t.results.items():
            rcnt += 1
            if args.nrounds > 0 and rcnt > args.nrounds:
                break
            if v is None:
                e.append('BYE')
            else:
                f, a = v
                if f and a:
                    f = int(f)
                    a = int(a)
                    if f > a:
                        s = 'W'
                    elif f < a:
                        s = 'L'
                    else:
                        s = 'D'
                    e.append('{}{:02d}-{:02d}'.format(s, f, a))
                    totfor += f
                    totag += a
                    totmarg += f - a
        e.append('{:.2f}'.format(float(totfor * 100) / float(totag)))
        e.append('{:.2f}'.format(float(totmarg) / float(rcnt)))
        results.append(e)

    if args.summary:
        if args.html:
            print('<html><body><table>')
            for r in results:
                print('\t<tr>')
                print('\t\t<td>' + '</td><td>'.join(r) + '</td>')
                print('\t</tr>')
            print('</table></body></html>')
        else:
            for r in results:
                print(','.join(r))

    return 0


if __name__ == "__main__":
    sys.exit(main())
