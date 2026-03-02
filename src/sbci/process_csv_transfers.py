from argparse import ArgumentParser
from collections import defaultdict
from csv import DictReader, DictWriter
from datetime import datetime, date
from io import TextIOWrapper
import os
from pathlib import Path
import sys

from dateutil.parser import parse as dateutil_parse
from six import ensure_str
# from xlwt import Workbook
# from xlwt.Style import easyxf

from sbci import make_phone, seasondir, load_config, to_date, to_datetime, \
    latest_report, find_age_group


def main():

    parser = ArgumentParser()
    parser.add_argument('--reportdir', default='reports', metavar='D',
                        help='directory containing report files')
    parser.add_argument('--xferfile', default=None, metavar='F',
                        help='csv file containing transfers report')
    parser.add_argument('--xlsfile', default='transfer-summary.xls',
                        metavar='F', help='file to to use for xls output')
    parser.add_argument('--club', default='Shooters Basketball Club',
                        metavar='S', help='club to produce stats for')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    reportdir = args.reportdir
    if not os.path.isdir(reportdir):
        reportdir = os.path.join(seasondir, args.reportdir)
    if not os.path.isdir(reportdir):
        raise RuntimeError('cannot locate reports directory!')
    if args.verbose:
        print(
            '[reports found in directory {} (realpath={})]'.format(
                reportdir, os.path.realpath(reportdir)
            ), file=sys.stderr
        )

    xferfile = args.xferfile
    if xferfile is None:
        xferfile, _ = latest_report('transfers', reportdir)
        if xferfile is None:
            raise RuntimeError('cannot locate transfers file!')
    if args.verbose:
        print(
            '[transfers report file = {} (realpath={})]'.format(
                xferfile, os.path.realpath(xferfile)
            ), file=sys.stderr
        )

    config = load_config()

    with open(xferfile, 'r', newline='') as infile:

        reader = DictReader(infile)

        outgoing = {'total': 0}
        incoming = {'total': 0}
        for key in ('clubs', 'genders', 'age_groups'):
            outgoing[key] = defaultdict(int)
            incoming[key] = defaultdict(int)

        for inrec in reader:

            # "Date Created","First Name","Last Name","Profile ID",
            # "Date of Birth","Gender","Source Club","Source Association",
            # "Source Competition","Source Season","Destination Club",
            # "Destination Association","Destination Competition",
            # "Destination Season","Status","Declined Reason",
            # "Declined Detail","Date Last Updated"

            first_name = inrec['First Name']
            last_name = inrec['Last Name']
            name = first_name + ' ' + last_name
            date_of_birth = to_date(inrec['Date of Birth'], '%d/%m/%Y')
            age_group = find_age_group(config['age_groups'], date_of_birth)
            gender = inrec['Gender']
            if gender == 'Male':
                gender = 'Boys'
            elif gender == 'Female':
                gender = 'Girls'
            else:
                raise RuntimeError('bad gender {}'.format(gender))
            src_club = inrec['Source Club']
            src_season = inrec['Source Season']
            dst_club = inrec['Destination Club']
            dst_season = inrec['Destination Season']
            status = inrec['Status']

            if dst_season != config['edjba_season']:
                if args.verbose:
                    print(
                        'ignore bad dest season ({}!={})'.format(
                            dst_season, config['edjba_season'],
                        ),
                        file=sys.stderr,
                    )
                continue

            if src_club == args.club:
                # outgoing
                outgoing['total'] += 1
                outgoing['clubs'][dst_club] += 1
                outgoing['genders'][gender] += 1
                outgoing['age_groups'][age_group] += 1
            elif dst_club == args.club:
                # incoming
                incoming['total'] += 1
                incoming['clubs'][dst_club] += 1
                incoming['genders'][gender] += 1
                incoming['age_groups'][age_group] += 1
            else:
                raise RuntimeError(
                    'record not for club {} (src={},dst={})'.format(
                        args.club, src_club, dst_club,
                    )
                )

    if outgoing['total'] + incoming['total'] == 0:
        print('No CSV records in "{}"'.format(xferfile), file=sys.stderr)
        return 0

    if outgoing['total'] > 0:
        print('Outgoing:')
        print('\tTotal: {}'.format(outgoing['total']))
        print('\tClubs:')
        for key, val in outgoing['clubs'].items():
            print('\t\t{}: {}'.format(key, val))
        print('\tGenders:')
        for key, val in outgoing['genders'].items():
            print('\t\t{}: {}'.format(key, val))
        print('\tAge Groups:')
        for key, val in outgoing['age_groups'].items():
            print('\t\t{}: {}'.format(key, val))

    if incoming['total'] > 0:
        print('Incoming:')
        print('\tTotal: {}'.format(incoming['total']))
        print('\tClubs:')
        for key, val in incoming['clubs'].items():
            print('\t\t{}: {}'.format(key, val))
        print('\tGenders:')
        for key, val in incoming['genders'].items():
            print('\t\t{}: {}'.format(key, val))
        print('\tAge Groups:')
        for key, val in incoming['age_groups'].items():
            print('\t\t{}: {}'.format(key, val))

    # if os.path.exists(args.xlsfile):
    #     raise RuntimeError('will not overwrite: {}'.format(args.xlsfile))
    #
    # headings = [
    #     '#',
    #     'Paid',
    #     'Parent/Guardian Contact Details',
    #     'DoB/Mobile',
    #     'Name',
    # ]
    # headings.extend(config['dates'])
    # styles = {
    #     'heading': easyxf(
    #         'font: name Arial, height 280, bold on; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'normal': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal left; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'centred': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'right': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal right; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'currency': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal right; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='$#,##0.00',
    #     ),
    #     'date': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='YYYY-MM-DD',
    #     ),
    #     'datetime': easyxf(
    #         'font: name Arial, height 280; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='YYYY-MM-DD HH:MM:SS AM/PM',
    #     ),
    #     'normal_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal left; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'centred_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'right_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal right; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='@',
    #     ),
    #     'currency_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal right; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='$#,##0.00',
    #     ),
    #     'date_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='YYYY-MM-DD',
    #     ),
    #     'datetime_highlighted': easyxf(
    #         'font: name Arial, height 280, colour red; '
    #         'align: wrap off, vertical centre, horizontal centre; '
    #         'borders: left thin, right thin, top thin, bottom thin',
    #         num_format_str='YYYY-MM-DD HH:MM:SS AM/PM',
    #     ),
    # }
    # #    Paid    Parent/Guardian Contact Details    Mobile    Name
    # col1styles = {
    #     'parent':        'normal',
    #     'date_of_birth': 'date',
    #     'name':          'normal',
    # }
    # col2styles = {
    #     'email':         'normal',
    #     'phone':         'centred',
    # }
    #
    # book = Workbook()
    #
    # sheet = book.add_sheet('transfers')
    #
    # r = 0
    # for c, v in enumerate(headings):
    #     sheet.write(r, c, ensure_str(v), styles['heading'])
    # sheet.set_panes_frozen(True)
    # sheet.set_horz_split_pos(1)
    # sheet.set_remove_splits(True)
    # ndates = len(config['dates'])
    # pnum = 0
    # for outrec in sorted(orecs.values(), key=lambda d: d['name'].lower()):
    #     pnum += 1
    #     r += 1
    #     if outrec['new'] == '*':
    #         normal_style = styles['normal_highlighted']
    #         centred_style = styles['centred_highlighted']
    #         right_style = styles['right_highlighted']
    #         ssuf = '_highlighted'
    #     else:
    #         normal_style = styles['normal']
    #         centred_style = styles['centred']
    #         right_style = styles['right']
    #         ssuf = ''
    #     sheet.write(r, 0, str(pnum), right_style)
    #     sheet.write(r, 1, outrec['paid'], centred_style)
    #     for c, (k, s) in enumerate(col1styles.items()):
    #         v = outrec[k]
    #         s = col1styles[k]
    #         sheet.write(r, 2 + c, v, styles[s + ssuf])
    #     i = 0
    #     for v in outrec['prepaid']:
    #         if v == 'old':
    #             ppstyle = styles['centred']
    #         else:
    #             ppstyle = styles['centred_highlighted']
    #         sheet.write(r, 2 + c + 1 + i, 'PP', ppstyle)
    #         i += 1
    #     while i < ndates - 1:
    #         sheet.write(r, 2 + c + 2 + i, '  ', centred_style)
    #         i += 1
    #     r += 1
    #     sheet.write(r, 0, '  ', normal_style)
    #     sheet.write(r, 1, '  ', normal_style)
    #     for c, (k, s) in enumerate(col2styles.items()):
    #         v = outrec[k]
    #         s = col2styles[k]
    #         sheet.write(r, 2 + c, v, styles[s + ssuf])
    #     c += 1
    #     sheet.write(r, 2 + c, '  ', normal_style)
    #     c += 1
    #     for i in range(len(config['dates'])):
    #         sheet.write(r, 2 + c + i, '  ', normal_style)
    # book.save(xlsfile)

    return 0


if __name__ == "__main__":
    sys.exit(main())
