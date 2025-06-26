from argparse import ArgumentParser
from datetime import datetime
from html import escape
from operator import itemgetter
import os
import sys

from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from xlutils.filter import process as xlutils_process, XLRDReader, XLWTWriter

from sbci import fetch_teams, find_team


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--club', '-c', default='Fairfield-Shooters',
                        help='change club id')
    parser.add_argument('--output', '-o', default='team-gradings.xls',
                        help='file to write excel output into')
    parser.add_argument('xlsfile',
                        help='xls file containing grading results')
    args = parser.parse_args()

    if os.path.exists(args.output):
        raise RuntimeError('Will not overwrite file "{}"!'.format(args.output))

    teams = fetch_teams()

    if args.verbose:
        print('processing file {}'.format(args.xlsfile), file=sys.stderr)

    ibook = open_workbook(args.xlsfile, formatting_info=True)
    isheet = ibook.sheet_by_index(0)
    rows = isheet.get_rows()
    _ = next(rows)

    # based on: https://stackoverflow.com/a/28240661/2130789
    writer = XLWTWriter()
    xlutils_process(XLRDReader(ibook, args.xlsfile), writer)
    obook = writer.output[0][1]
    ostyles = writer.style_list

    team_count = 0
    cur_grade = None
    sheet_list = []
    ginfo = []

    for r in rows:

        # Team=0,Grade=1,R1=2,R2=3,R3=4,R4=5,R5=6,R6=7,W=8,L=9,Team=10,Count=11

        if len(r) != 12:
            raise RuntimeError('bogus row: {} != 12'.format(len(r)))

        tinfo = []
        for ci, c in enumerate(r):
            w = isheet.computed_column_width(ci)
            tinfo.append((c.value, ostyles[c.xf_index], w))

        team = tinfo[0][0]
        grade = tinfo[1][0]
        team2 = tinfo[10][0]

        if team != team2:
            raise RuntimeError('bogus row: {} != {}'.format(team, team2))

        if grade != cur_grade:
            # a new grade - dump current if a Shooters team is in it
            for sheet in sheet_list:
                osheet = obook.add_sheet(sheet)
                ri = 0
                for tinfo in ginfo:
                    ci = 0
                    for v, s, w in tinfo:
                        osheet.write(ri, ci, v, s)
                        osheet.col(ci).width = w
                        ci += 1
                    ri += 1
            cur_grade = grade
            sheet_list = []
            ginfo = []

        ginfo.append(tinfo)

        if team.startswith(args.club):
            team_count += 1

            t = find_team(teams, edjba_id=team)
            if t is None:
                raise RuntimeError('unknown fairfield team: {}'.format(team))

            tn = t.sname
            if args.verbose:
                print('team: {}'.format(tn), file=sys.stderr)
            sheet_list.append(tn)

    obook.save(args.output)

    if args.verbose:
        print('{} teams.'.format(team_count), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
