from argparse import ArgumentParser
from operator import itemgetter
from sbci import fetch_teams, find_team
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from datetime import datetime
from html import escape
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--club', '-c', default='Fairfield-Shooters',
                        help='change club id')
    parser.add_argument('xlsxfiles', nargs='+',
                        help='xlsx file containing edjba fixtures')
    args = parser.parse_args()

    teams = fetch_teams()

    rounds = {}

    bye = datetime.strptime('00:00', '%H:%S').time()

    for xlsxfile in args.xlsxfiles:

        if args.verbose:
            print('processing file {}'.format(xlsxfile), file=sys.stderr)

        book = open_workbook(xlsxfile)

        sheet = book.sheet_by_index(0)

        rows = sheet.get_rows()

        _ = next(rows)

        for r in rows:

            grade, rdate, rnd, home, away, venue, crt, gtime = map(
                lambda c: c.value, r
            )

            clubmatches = [
                home.startswith(args.club), away.startswith(args.club)
            ]

            if any(clubmatches):

                rounds.setdefault(str(rnd), []).append(
                    [
                        clubmatches,
                        grade,
                        xldate_as_datetime(rdate, book.datemode).date(),
                        home,
                        '' if away == 'Bye' else away,
                        venue,
                        crt,
                        bye if away == 'Bye'
                        else xldate_as_datetime(gtime, book.datemode).time(),
                    ]
                )

    print('''<html>
     <head>
      <style>
       @media print {
        .pagebreak {
         clear: both;
         page-break-after: always;
        }
       }
       table tr td, table tr th {
        page-break-inside: avoid;
       }
       table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
       }
       th, td {
        padding: 5px;
        font-size: small;
       }
       table.center {
        margin-left: auto;
        margin-right: auto;
       }
       h3 {
        text-align: center;
       }
       caption {
         display: table-caption;
         text-align: center;
         font-weight: bold;
         margin-top: 36px;
         margin-bottom: 36px;
       }
      </style>
     </head>
     <body>''')

    rcount = 0

    for rnd, games in sorted(rounds.items(), key=itemgetter(0)):

        ngames = sum(2 if all(g[0]) else 1 for g in games)

        if args.verbose:
            print('Round {} - {} games'.format(rnd, ngames), file=sys.stderr)

        if ngames == 0:
            continue

        rcount += 1
        rdate = games[0][2]

        dom = rdate.strftime('%d')
        while dom[0] == '0':
            dom = dom[1:]
        mon = rdate.strftime('%B')
        header = 'Round {} - {} {}'.format(rnd, mon, dom)

        if rcount > 1:
            print('  <div class="pagebreak"></div>')
        print('  <table class="center">')
        print('   <caption>{}</caption>'.format(escape(header, True)))

        print(
            '   <tr>'
            '<th>Grade</th>'
            '<th>Home</th>'
            '<th>Away</th>'
            '<th>Time</th>'
            '<th>Venue</th>'
            '<th>Court</th>'
            '</tr>'
        )

        n = 0
        for (
            clubmatches, grade, rdate1, home, away, venue, crt, gtime
        ) in sorted(games, key=itemgetter(7)):
            n += 1

            if rdate1 != rdate:
                raise RuntimeError(
                    'differing Round dates ({}!={})'.format(rdate, rdate1)
                )

            if clubmatches[0]:
                home_team = find_team(teams, edjba_id=home)
                home += ' [<b>{}</b>]'.format(home_team.name[9:])
            if clubmatches[1]:
                away_team = find_team(teams, edjba_id=away)
                away += ' [<b>{}</b>]'.format(away_team.name[9:])

            print(
                '   <tr>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '<td>{}</td>'
                '</tr>'.format(
                    grade,
                    home,
                    away,
                    'BYE' if gtime is bye else gtime.strftime('%I:%M%p'),
                    venue,
                    crt,
                )
            )

        print('  </table>')

    print(' </body>')
    print('</html>')

    return 0


if __name__ == "__main__":
    sys.exit(main())
