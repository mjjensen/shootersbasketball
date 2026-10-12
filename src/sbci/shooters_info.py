from argparse import ArgumentParser
import sys

from sbci import season


def main() -> int:

    parser = ArgumentParser()
    parser.add_argument('--all', '-a', action='store_true',
                        help='print all info')
    parser.add_argument('--season', '-s', action='store_true',
                        help='print season info')
    parser.add_argument('--python', '-p', action='store_true',
                        help='print python info')
    args = parser.parse_args()

    if args.all or args.season:
        print(f'season: {season}')

    if args.all or args.python:
        print('.'.join(map(str, sys.version_info[:2])))

    return 0


if __name__ == "__main__":
    sys.exit(main())
