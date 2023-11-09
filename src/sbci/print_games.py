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
                        help='specify number of rounds to output')
    parser.add_argument('--report', '-r', default=None, metavar='F',
                        help='specify report file to use')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    teams = fetch_teams()

    def result(roundno, team_name, score_for, score_against):
        t = find_team(teams, edjba_id=team_name)
        if t is None:
            print('team {} not found!'.format(team_name), file=sys.stderr)
            return
        if not hasattr(t, 'results'):
            t.results = OrderedDict()
        if score_for is None:
            value = None
        else:
            value = score_for, score_against
        if roundno in t.results:
            raise RuntimeError('duplicate game: {}, {}'.format(roundno))
        t.results[roundno] = value

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
        print('team1,team2')

    with open(report_file, 'r', newline='') as csvfile:

        reader = DictReader(csvfile)

        for r in reader:
            # game date,grade,round,game status,venue,playing surface,game time,
            # home team,home team score,home team result,
            # home team players in lineup,home team player points used,
            # away team,away team score,away team result,
            # away team players in lineup,away team player points used,bye,
            # host organisation,competition,competition type,season,game alias,
            # game code,game id,result source,result timestamp (last updated)
            status = r['game status']
            if status == 'Upcoming' and not args.upcoming:
                continue
            _gdate = date(*strptime(r['game date'], '%d/%m/%Y')[:3])
            _grade = r['grade']
            roundno = r['round']
            bye = r['bye']
            team_a_name = r['home team']
            team_b_name = r['away team']
            _venue = r['venue']
            if not r['game time']:
                _gtime = time()
            else:
                _gtime = time(*strptime(r['game time'], '%H:%M')[3:5])

            if bye:
                result(roundno, bye, None, None)
            else:
                if status == 'Upcoming':
                    team_a_score = team_b_score = None
                else:
                    team_a_score = r['home team score']
                    _team_a_result = r['home team result']
                    team_b_score = r['away team score']
                    _team_b_result = r['away team result']

                if team_a_name.startswith(args.club):
                    result(roundno, team_a_name, team_a_score, team_b_score)
                if team_b_name.startswith(args.club):
                    result(roundno, team_b_name, team_b_score, team_a_score)

    results = []
    for t in teams.values():
        e = [t.sname, t.edjba_code]
        rcnt = totfor = totag = totmarg = 0
        for r, v in t.results.items():
            rcnt += 1
            if args.nrounds > 0:
                if rcnt > args.nrounds:
                    break
                if r.startswith('Round '):
                    r = r[6:]
                if r.isdigit():
                    rnum = int(r)
                    while rcnt < rnum:
                        e.append('BYE')
                        rcnt += 1
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
        if args.nrounds > 0:
            while rcnt < args.nrounds:
                e.append('')
                rcnt += 1
        e.append('{:.2f}'.format(float(totfor * 100) / float(totag)))
        e.append('{:.2f}'.format(float(totmarg) / float(rcnt)))
        results.append(e)

    if args.summary:
        if args.html:
            print('''\
<html>
 <head>
  <style>
   h1 {
    text-align: center;
   }
   table {
    margin-left: auto;
    margin-right: auto;
   }
   table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
    padding: 5px;
   }
   td.center {
    text-align: center;
   }
   td.right {
    text-align: right;
   }
   td.red {
    color: red;
   }
   td.green {
    color: green;
   }
   td.blue {
    color: blue;
   }
   td.orange {
    color: orange;
   }
  </style>
 </head>
 <body>
  <h1>Summary</h1>
  <table>
   <thead>
    <tr>
     <th>Name</th>
     <th>Code</th>
     <th></th>''')
            for r, _ in enumerate(results[0][2:-2], 1):
                print('     <th>R{}</th>'.format(r))
            print('''\
     <th></th>
     <th>Pct</th>
     <th>AvMrg</th>
    </tr>
   </thead>
   <tbody>''')
            colors = {'W': 'green', 'L': 'red', 'D': 'blue', 'B': 'orange'}
            for r in results:
                print('    <tr>')
                print('     <td>{}</td>'.format(r[0]))
                print('     <td class="center">{}</td>'.format(r[1]))
                print('     <td></td>')
                for cv in r[2:-2]:
                    cl = 'center'
                    if len(cv) > 0:
                        cl += ' ' + colors[cv[0]]
                    print('     <td class="{}">{}</td>'.format(cl, cv))
                print('     <td></td>')
                cv = r[-2]
                cf = float(cv)
                cl = 'right'
                if cf < 50.0 or cf > 150.0:
                    cl += ' red'
                print('     <td class="{}">{}</td>'.format(cl, cv))
                cv = r[-1]
                cf = float(cv)
                cl = 'right'
                if cf < -10.0 or cf > 10.0:
                    cl += ' red'
                print('     <td class="{}">{}</td>'.format(cl, cv))
                print('    </tr>')
            print('''\
   </tbody>
  </table>
 </body>
</html>''')
        else:
            print('name,code', end='')
            for r, _ in enumerate(results[0][2:-2], 1):
                print(',r{}'.format(r), end='')
            print(',pct,avmrg')
            for r in results:
                print(','.join(r))

    return 0


if __name__ == "__main__":
    sys.exit(main())
