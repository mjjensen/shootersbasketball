from __future__ import print_function
from argparse import ArgumentParser
from sbci import fetch_teams, verbose_info
from re import sub
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--tmemail', action='store_true',
                        help='just print team manager email addrs')
    parser.add_argument('--cemail', action='store_true',
                        help='just print coach email addrs')
    parser.add_argument('--caddrs', action='store_true',
                        help='just print coach names and addresses')
    parser.add_argument('--noresponse', action='store_true',
                        help='print list of teams that have not responded')
    parser.add_argument('--csv', action='store_true',
                        help='print info as csv instead of multi-line text')
    parser.add_argument('--terse', action='store_true',
                        help='print one terse line instead of multi-line text')
    parser.add_argument('--verbose', action='store_true',
                        help='be verbose about actions')
    parser.add_argument('--details', action='store_true',
                        help='print more detail in multi-line text')
    parser.add_argument('--urls', action='store_true',
                        help='print list of teams and urls')
    args = parser.parse_args()

    teams = fetch_teams(verbose=args.verbose)

    # info to print for a person
    p_fmt = '{} <{}>, {} [WWC: #{}, exp: {}]'

    def dateonly(s):
        if s is None:
            return None
        else:
            return sub(r' [0:\.]+$', '', s)

    if args.csv:
        print(
            'Name,Id,Code,Age Group,Gender,Number,Grade,'
            'Team Manager,Email,Mobile'
        )

    first = True

    for t in teams.values():

        if args.tmemail:
            print(t.tm_email)
            continue

        if args.cemail:
            if t.co_email:
                print(t.co_email)
            if t.ac_email:
                print(t.ac_email)
            continue

        if args.caddrs:
            if t.co_address:
                print('{}, {}'.format(t.co_name, t.co_address))
            if t.ac_address:
                print('{}, {}'.format(t.ac_name, t.ac_address))
            continue

        if args.noresponse and t.responded == 1:
            continue

        if args.csv:
            print(
                '{},{},{},{:02d},{},{:02d},{},{},{},{}'.format(
                    t.sname, t.edjba_id, t.edjba_code, t.age_group, t.gender,
                    t.number, t.grade if t.grade else '',
                    t.tm_name, t.tm_email, t.tm_mobile
                )
            )
            continue

        if args.terse:
            # snm = t.sname[:9] + '...' if len(t.sname) > 12 else t.sname
            # tmn = t.tm_name[:15] + '...' if len(t.tm_name) > 18 else t.tm_name
            # tme = t.tm_email[:22] + '...' if len(t.tm_email) > 25 \
            #     else t.tm_email
            print(
                '{} {:12} {:18} {:40} {}'.format(
                    t.edjba_code, t.sname, t.tm_name, t.tm_email, t.tm_mobile
                )
            )
        elif args.urls:
            print('{},{},{}'.format(t.sname, t.edjba_id, t.regurl))
        else:
            if first:
                first = False
            else:
                print('')
            print(t.sname + ':')
            print('      Id: ' + t.edjba_id)
            if args.details:
                print('    Code: ' + t.edjba_code)
                if t.regurl:
                    print('     URL: ' + t.regurl)
                if t.compats:
                    print(' Compats: ' + t.compats)
            if t.grade:
                print('  Grade?: ' + t.grade)
            print(
                '     T/M: ' + p_fmt.format(
                    t.tm_name, t.tm_email, t.tm_mobile,
                    t.tm_wwcnum, dateonly(t.tm_wwcexp)
                )
            )
            if args.details:
                if t.co_name and t.co_name != 'Nothing':
                    print('       C: ' + p_fmt.format(
                        t.co_name, t.co_email, t.co_mobile,
                        t.co_wwcnum, dateonly(t.co_wwcexp)
                    ))
                if t.ac_name and t.ac_name != 'Nothing':
                    print('     A/C: ' + p_fmt.format(
                        t.ac_name, t.ac_email, t.ac_mobile,
                        t.ac_wwcnum, dateonly(t.ac_wwcexp)
                    ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
