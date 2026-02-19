from argparse import ArgumentParser
import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import IntEnum
import sys
from typing import Tuple, Optional, Generator
from xlsxwriter.workbook import Workbook


__all__ = [
    'SeasonType', 'AgeGroup', 'Season',
    'age_group_generator', 'season_generator',
    'summer_age_groups', 'winter_age_groups', 'all_age_groups',
    'summer_seasons', 'winter_seasons', 'all_seasons',
    'OutputFormat', 'write_age_groups', 'main',
]


class SeasonType(IntEnum):
    Summer = 1
    Winter = 2


@dataclass(order=True, frozen=True)
class AgeGroup:

    limit: int
    stype: SeasonType

    duration: int = field(init=False, repr=False, hash=False, compare=False)

    def __post_init__(self) -> None:
        if (
            self.limit < 10
        or
            (self.stype == SeasonType.Summer and self.limit == 21)
        ):
            object.__setattr__(self, 'duration', 3)
        else:
            object.__setattr__(self, 'duration', 2)

    def __str__(self) -> str:
        return 'U{:02d}'.format(self.limit)

    @property
    def label(self) -> str:
        return 'Under {:02d}'.format(self.limit)

    def dates(self, year: int) -> Tuple[date, date]:
        if self.stype == SeasonType.Summer:
            base = year - 1 - self.limit
            return date(base, 7, 1), date(base + self.duration, 6, 30)
        else:
            base = year - self.limit
            return date(base, 1, 1), date(base + self.duration - 1, 12, 31)

    def date_is_in(self, year: int, d: date) -> bool:
        ds, de = self.dates(year)
        return d >= ds and d <= de


summer_age_groups = [
    AgeGroup(value, SeasonType.Summer) for value in (8, 10, 12, 14, 16, 18, 21)
]
winter_age_groups = [
    AgeGroup(value, SeasonType.Winter) for value in (9, 11, 13, 15, 17, 19, 21)
]

def age_group_generator() -> Generator[AgeGroup, None, None]:
    sag = list(summer_age_groups)
    wag = list(winter_age_groups)
    while True:
        try:
            yield sag.pop(0)  # summer first
            yield wag.pop(0)
        except IndexError:
            break

all_age_groups = [ag for ag in age_group_generator()]


@dataclass(order=True, frozen=True)
class Season:

    year: int  # for Summer this is the year of the end of the season
    stype: SeasonType

    def __str__(self) -> str:
        return '{}{:02d}'.format(self.stype.name[0], self.year % 100)

    @property
    def label(self) -> str:
        if self.stype is SeasonType.Summer:
            return '{:04d}/{:02d} {}'.format(
                self.year - 1, self.year % 100, self.stype.name
            )
        else:
            return '{:04d} {}'.format(self.year, self.stype.name)

    def age_group_of(self, d: date) -> Optional[AgeGroup]:
        if self.stype is SeasonType.Summer:
            age_groups = summer_age_groups
        else:
            age_groups = winter_age_groups
        for ag in age_groups:
            if ag.date_is_in(self.year, d):
                return ag
        return None


# winter season comes first so summer year needs to be winter year + 1
summer_seasons = [Season(year, SeasonType.Summer) for year in range(2027, 2032)]
winter_seasons = [Season(year, SeasonType.Winter) for year in range(2026, 2031)]

def season_generator() -> Generator[Season, None, None]:
    ss = list(summer_seasons)
    ws = list(winter_seasons)
    while True:
        try:
            yield ws.pop(0)  # winter first
            yield ss.pop(0)
        except IndexError:
            break

all_seasons = [season for season in season_generator()]


class OutputFormat(IntEnum):
    xlsx = 1
    html = 2
    csv = 3

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return OutputFormat[s]
        except KeyError:
            raise ValueError()


def write_age_groups(players, filename, format=OutputFormat.csv,
                     incl_dobs=False, width=2.0, add=1):

    header = ['Name']
    widths = [4]
    if incl_dobs:
        header.append('Dob')
        widths.append(3)
    for season in all_seasons:
        s = str(season)
        header.append(s)
        widths.append(len(s))

    rows = []

    for name, dob in players:

        wi = 0

        s = str(name)
        l = len(s)
        row = [s]
        if l > widths[wi]:
            widths[wi] = l
        wi += 1

        if incl_dobs:
            s = date.strftime(dob, '%Y-%m-%d')
            l = len(s)
            row.append(s)
            if l > widths[wi]:
                widths[wi] = l
            wi += 1

        for season in all_seasons:

            ag = season.age_group_of(dob)
            if ag is None:
                s = '??'
            else:
                s = str(ag)
            l = len(s)
            row.append(s)
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
                ) for cname in [
                    'blue', 'brown', 'cyan', 'gray', 'green', 'lime', 'magenta',
                    'navy', 'orange', 'pink', 'purple', 'red', 'silver', 'yellow',
                ]
            ]

            agcmap = {'??': norm}
            seen = set()
            cind = 0
            clen = len(colours)
            for ag in all_age_groups:
                if ag.limit not in seen:
                    seen.add(ag.limit)
                    agcmap[str(ag)] = colours[cind]
                    cind = (cind + 1) % clen

            ri = ci = cc = 0

            for hcell in header:
                worksheet.write_string(ri, ci, hcell, hfmt)
                ci += 1
            ri += 1

            for row in rows:

                ci = 0
                for cell in row:
                    worksheet.write_string(
                        ri, ci, cell,
                        bold if ci == 0 else hfmt if ci == 1 else agcmap[cell]
                    )
                    ci += 1
                ri += 1

            # worksheet.autofit() - doesn't seem to work
            for i, w in enumerate(widths):
                worksheet.set_column(i, i, (w + add) * width)

        finally:
            workbook.close()

    elif format == OutputFormat.html:

        if filename == 'sys.stdout':
            outfile=sys.stdout
        else:
            outfile = open(filename, 'w')

        print('''<html>
<head>
<style>
 table, th, td {
 border: 1px solid black;
 border-collapse: collapse;
 padding: 5px;
}
th {
 text-align: center;
 font-weight: bold;
}
</style>
</head>
<body>
<table>''',
            file=outfile,
        )

        colours = [
            # 'blue',
            'brown',
            'cyan',
            'gray',
            'green',
            'lime',
            'magenta',
            # 'navy',
            'orange',
            'pink',
            'purple',
            'red',
            'silver',
            'yellow',
            # '#F0F8FF',
            # '#FAEBD7',
            # '#00FFFF',
            # '#7FFFD4',
            # '#00FFFF',
            # '#FFF8DC',
            # '#ADFF2F',
            # '#90EE90',
            # '#FFB6C1',
            # '#87CEFA',
            # '#F5DEB3',
            # '#FF6347',
        ]

        agcmap = {'??': None}
        seen = set()
        cind = 0
        clen = len(colours)
        for ag in all_age_groups:
            if ag.limit not in seen:
                seen.add(ag.limit)
                agcmap[str(ag)] = colours[cind]
                cind = (cind + 1) % clen

        print('<thead><tr>', file=outfile)

        for hcell in header:
            print('<th>{}</th>'.format(hcell), file=outfile)

        print('</tr></thead><tbody>', file=outfile)

        for row in rows:

            print('<tr>', file=outfile)

            ci = 0
            for cell in row:
                if ci == 0 or (incl_dobs and ci == 1) or agcmap[cell] is None:
                    print(
                        '<td style="font-weight: bold;">{}</td>'.format(cell),
                        file=outfile,
                    )
                else:
                    print(
                        '<td style="text-align: center; background-color: {};">'
                        '{}</td>'.format(agcmap[cell], cell), file=outfile,
                    )
                ci += 1

            print('</tr>', file=outfile)

        print('</tbody></table></body></html>', file=outfile)

    elif format == OutputFormat.csv:

        if filename == 'sys.stdout':
            sys.stdout.reconfigure(newline='')
            writer = csv.writer(sys.stdout)
        else:
            writer = csv.writer(open(filename, 'w', newline=''))

        writer.writerow(header)
        writer.writerows(rows)

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
