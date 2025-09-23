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
    'main',
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


summer_seasons = [Season(year, SeasonType.Summer) for year in range(2026, 2032)]
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
    parser.add_argument('--xlsx', '-x', action='store_true',
                        help='output xlsx instead of csv')
    args = parser.parse_args()

    if args.input == 'sys.stdin':
        sys.stdin.reconfigure(newline='')
        reader = csv.reader(sys.stdin)
    else:
        reader = csv.reader(open(args.input, 'r', newline=''))

    if args.skipheader:
        _ = next(reader)  # discard header from file

    header = ['Name', 'DoB']
    for season in all_seasons:
        header.append(str(season))

    rows = []

    for name, dobstr in reader:
        try:
            dob = datetime.strptime(dobstr, '%Y-%m-%d').date()
        except:
            dob = datetime.strptime(dobstr, '%d/%m/%Y').date()

        row = [name, dob]
        for season in all_seasons:
            ag = season.age_group_of(dob)
            if ag is None:
                row.append('??')
            else:
                row.append(str(ag))

        rows.append(row)

    if args.xlsx:
        if args.output == 'sys.stdout':
            raise RuntimeError('cannot output xlsx to sys.stdout')
        workbook = Workbook(args.output)
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
        seen = set()
        agcmap = {'??': norm}
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
        for row in rows:
            ri += 1
            ci = 0
            for cell in row:
                worksheet.write_string(
                    ri, ci, cell, bold if ci == 0 else agcmap[cell]
                )
                ci += 1
        worksheet.autofit()
        workbook.close()
    else:
        if args.output == 'sys.stdout':
            sys.stdout.reconfigure(newline='')
            writer = csv.writer(sys.stdout)
        else:
            writer = csv.writer(open(args.output, 'w', newline=''))
        writer.writerow(header)
        writer.writerows(rows)

    return 0


if __name__ == "__main__":
    sys.exit(main())
