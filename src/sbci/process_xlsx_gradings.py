from argparse import ArgumentParser
from datetime import datetime
from html import escape
from operator import itemgetter
import os
import sys

from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from xlutils.filter import process as xlutils_process, XLRDReader, XLWTWriter
from xlwt import Workbook

from sbci import fetch_teams, find_team


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--club', '-c', default='Fairfield-Shooters',
                        help='change club id')
    parser.add_argument('--output', '-o', default='team-gradings.xls',
                        help='file to write excel output into')
    parser.add_argument('xlsxfile',
                        help='xlsx file containing grading results')
    args = parser.parse_args()

    if os.path.exists(args.output):
        raise RuntimeError('Will not overwrite file "{}"!'.format(args.output))

    teams = fetch_teams()

    if args.verbose:
        print('processing file {}'.format(args.xlsxfile), file=sys.stderr)

    ibook = open_workbook(args.xlsxfile, formatting_info=True)
    isheet = ibook.sheet_by_index(0)
    rows = isheet.get_rows()
    _ = next(rows)

    # based on: https://stackoverflow.com/a/28240661/2130789
    writer = XLWTWriter()
    xlutils_process(XLRDReader(ibook, args.xlsxfile), writer)
    obook = writer.output[0][1]
    ostyles = writer.style_list

    tc = 0
    cg = None
    sl = []
    ginfo = []

    for r in rows:

        tinfo = []
        for ci, c in enumerate(r):
            w = isheet.computed_column_width(ci)
            tinfo.append((c.value, ostyles[c.xf_index], w))

        en = tinfo[0][0]
        c1 = tinfo[1][0]
        c2 = tinfo[8][0]

        if c1 != c2:
            raise RuntimeError('bogus row: {} != {}'.format(c1, c2))

        if c1 != cg:
            # a new grade - dump current if a Shooters team is in it
            for st in sl:
                osheet = obook.add_sheet(st)
                ri = 0
                for tinfo in ginfo:
                    ci = 0
                    for v, s, w in tinfo:
                        osheet.write(ri, ci, v, s)
                        osheet.col(ci).width = w
                        ci += 1
                    ri += 1
            cg = c1
            sl = []
            ginfo = []

        ginfo.append(tinfo)

        if en.startswith(args.club):
            tc += 1

            t = find_team(teams, edjba_id=en)
            if t is None:
                raise RuntimeError('unknown fairfield team: {}'.format(en))

            tn = t.sname
            if args.verbose:
                print('team: {}'.format(tn), file=sys.stderr)
            sl.append(tn)

    obook.save(args.output)

    if args.verbose:
        print('{} teams.'.format(tc), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
