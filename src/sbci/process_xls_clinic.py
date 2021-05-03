from argparse import ArgumentParser
import sys
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime

from sbci import load_config


def main():

    parser = ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    config = load_config()

    if args.verbose:
        print('processing file {}'.format(config['file']), file=sys.stderr)

    book = open_workbook(config['file'])

    sheet = book.sheet_by_name(config['sheet'])

    rows = sheet.get_rows()

    _ = next(rows)

    for r in rows:

        num, paid, parent, mobile, name, *days = map(
            lambda c: c.value, r
        )

        print(
            'num={},paid={},parent={},mobile={},name={},days={}'.format(
                num, paid, parent, mobile, name, days
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
