from argparse import ArgumentParser
import csv
from datetime import date, datetime
import sys

from xlsxwriter.workbook import Workbook

from sbci import all_seasons, excel_colours, html_colours, OutputFormat


def write_age_groups(
    players: list[tuple[str, date]], filename: str,
    format: OutputFormat = OutputFormat.csv, incl_dobs: bool = False,
    width: flaot = 2.0, add: int = 1
) -> None:

    heading = ['Name']
    widths = [4]
    if incl_dobs:
        heading.append('DoB')
        widths.append(3)
    for season in all_seasons:
        s = str(season)
        heading.append(s)
        widths.append(len(s))

    rows = []

    for name, dob in players:

        wi = 0

        s = str(name)
        l = len(s)
        row = [(s, -1)]
        if l > widths[wi]:
            widths[wi] = l
        wi += 1

        if incl_dobs:
            s = '{} {} &frac12;'.format(
                dob.year, '1st' if dob.month <= 6 else '2nd'
            )
            l = len(s)
            row.append((s, -1))
            if l > widths[wi]:
                widths[wi] = l
            wi += 1

        for season in all_seasons:

            ag = season.age_group_of(dob)
            if ag is None:
                s = '???'
                i = -1
            else:
                s = str(ag)
                i = ag.index
            l = len(s)
            row.append((s, i))
            if l > widths[wi]:
                widths[wi] = l
            wi += 1

        rows.append(row)

    if format == OutputFormat.xlsx:

        if filename == 'sys.stdout':
            raise RuntimeError('cannot output xlsx to sys.stdout')

        workbook = Workbook(filename)

        try:
            worksheet = workbook.add_worksheet()

            font = {
                'font_name': 'Arial',
                'font_size': 14,
            }

            norm = workbook.add_format(font)
            bold = workbook.add_format(dict(font, bold=True))
            hfmt = workbook.add_format(dict(font, bold=True, align='center'))

            colours = [
                workbook.add_format(
                    dict(
                        font,
                        align='center',
                        pattern=2,
                        fg_color=cname,
                        bg_color='white',
                    )
                ) for cname in excel_colours
            ]
            ncolours = len(colours)

            ri = ci = cc = 0

            for hcell in heading:
                worksheet.write_string(ri, ci, hcell, hfmt)
                ci += 1
            ri += 1

            for row in rows:

                ci = 0
                for s, i in row:
                    if i < 0:  # no colour
                        if ci == 0:
                            fmt = bold
                        elif incl_dobs and ci == 1:
                            fmt = hfmt
                        else:
                            fmt = norm
                    else:
                        fmt = colours[i % ncolours]
                    worksheet.write_string(ri, ci, s, fmt)
                    ci += 1
                ri += 1

            # worksheet.autofit() - doesn't seem to work
            for i, w in enumerate(widths):
                worksheet.set_column(i, i, (w + add) * width)

        finally:
            workbook.close()

    elif format == OutputFormat.html:

        if filename == 'sys.stdout':
            outfile = sys.stdout
        else:
            outfile = open(filename, 'w')

        ncolours = len(html_colours)

        print(
            '''<html><head><style>
table, th, td {
 border: 1px solid black;
 border-collapse: collapse;
 padding: 5px;
}
th {
 text-align: center;
 font-weight: bold;
}
</style></head><body><table><thead><tr>''',
            file=outfile,
        )

        for hcell in heading:
            print('<th>{}</th>'.format(hcell), file=outfile)

        print('</tr></thead><tbody>', file=outfile)

        for row in rows:

            print('<tr>', file=outfile)

            ci = 0
            for s, i in row:
                if i < 0:  # no colour
                    if ci == 0 or (incl_dobs and ci == 1):
                        print(
                            '<td style="font-weight: bold;">{}</td>'.format(s),
                            file=outfile,
                        )
                    else:
                        print('<td">{}</td>'.format(s), file=outfile)
                else:
                    print(
                        '<td style="text-align: center; background-color: {};">'
                        '{}</td>'.format(html_colours[i % ncolours], s),
                        file=outfile,
                    )
                ci += 1

            print('</tr>', file=outfile)

        print('</tbody></table></body></html>', file=outfile)

    elif format == OutputFormat.csv:

        if filename == 'sys.stdout':
            sys.stdout.reconfigure(newline='')
            outfd = sys.stdout
        else:
            outfd = open(filename, 'w', newline='')

        try:
            writer = csv.writer(outfd)
            writer.writerow(heading)
            writer.writerows(rows)
        finally:
            if filename != 'sys.stdout':
                outfd.close()

    else:
        raise RuntimeError('unknown output format: {}'.format(format))


def main() -> int:

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--input', '-i', default='sys.stdin', metavar='F',
                        help='input csv file containing name,dob pairs')
    parser.add_argument('--skipheader', '-s', action='store_true',
                        help='skip first row of input csv file')
    parser.add_argument('--output', '-o', default='sys.stdout', metavar='F',
                        help='output csv file')
    parser.add_argument('--format', '-f', type=OutputFormat.from_string,
                        choices=list(OutputFormat), default=OutputFormat.csv,
                        help='output type')
    parser.add_argument('--dobs', '-d', action='store_true',
                        help='include Date of Birth column')
    parser.add_argument('--width', '-w', type=float, default=2.0,
                        help='factor to multiply no. of column chars')
    parser.add_argument('--add', '-a', type=int, default=1,
                        help='no. of chars to add to column len')
    args = parser.parse_args()

    if args.input == 'sys.stdin':
        sys.stdin.reconfigure(newline='')
        reader = csv.reader(sys.stdin)
    else:
        reader = csv.reader(open(args.input, 'r', newline=''))

    if args.skipheader:
        _ = next(reader)  # discard header from file

    players = []

    for name, dobstr in reader:
        try:
            dob = datetime.strptime(dobstr, '%Y-%m-%d').date()
        except:
            dob = datetime.strptime(dobstr, '%d/%m/%Y').date()

        players.append((name, dob))

    write_age_groups(
        players, args.output, args.format,
        incl_dobs=args.dobs, width=args.width, add=args.add,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
