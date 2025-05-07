from __future__ import print_function
from argparse import ArgumentParser
from csv import DictWriter, QUOTE_ALL
from io import TextIOWrapper
from sbci import fetch_teams, fetch_wwc_list
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
    parser.add_argument('--coaches', action='store_true',
                        help='print coaches instead of team managers in terse')
    parser.add_argument('--both', action='store_true',
                        help='print both coaches and team managers in terse')
    parser.add_argument('--altsort', action='store_true',
                        help='use alternate sorting (age/gender/number)')
    parser.add_argument('--verbose', action='store_true',
                        help='be verbose about actions')
    parser.add_argument('--details', action='store_true',
                        help='print more detail in multi-line text')
    parser.add_argument('--urls', action='store_true',
                        help='print list of teams and urls')
    parser.add_argument('--google', action='store_true',
                        help='print csv suitable for transfer to google sheets')
    parser.add_argument('--compats', action='store_true',
                        help='print csv suitable for transfer to compat sheet')
    parser.add_argument('--wwclist', action='store_true',
                        help='print list suitable for bulk wwc check')
    parser.add_argument('teams', nargs='*',
                        help='limit output to the list of teams specified')
    args = parser.parse_args()

    if args.google:
        args.csv = True
        args.terse = False
        args.both = True
        args.altsort = True

    if args.compats:
        args.csv = True
        args.altsort = True

    if args.wwclist:
        wwc_list = fetch_wwc_list()
        with TextIOWrapper(sys.stdout.buffer, newline='') as outfile:
            writer = DictWriter(outfile, ['FamilyName', 'CardNumber'],
                                quoting=QUOTE_ALL, quotechar='"')
            writer.writeheader()
            for fn, cn in wwc_list:
                writer.writerow({'FamilyName': fn, 'CardNumber': cn})
        return 0

    if args.altsort:
        teams = fetch_teams(
            order_by='age_group, gender, team_number, team_name',
            verbose=args.verbose
        )
    else:
        teams = fetch_teams(verbose=args.verbose)

    # info to print for a person
    p_fmt = '{} <{}>, {} [WWC: #{}, exp: {}]'

    def dateonly(s):
        if s is None:
            return None
        else:
            return sub(r' [0:\.]+$', '', s)

    if args.csv:
        if args.compats:
            print('Gender,Club,Age,No')
        elif args.terse:
            if args.both:
                print(
                    'Code,Name,Team Manager,Email,Mobile,Coach,Email,Mobile'
                )
            else:
                print(
                    'Code,Name,{},Email,Mobile'.format(
                        'Coach' if args.coaches else 'Team Manager'
                    )
                )
        else:
            if args.both:
                print(
                    '#,Name,Grade,EDJBA Id,EDJBA Code,'
                    'Team Manager,Email,Mobile,'
                    'Coach,Email,Mobile,'
                    'URL'
                )
            else:
                print(
                    'Name,Id,Code,Age Group,Gender,Number,Grade,'
                    'Team Manager,Email,Mobile'
                )

    team_list = []
    if args.teams:
        for team in args.teams:
            team_list.append(teams[team])
    else:
        team_list.extend(teams.values())

    first = True

    for c, t in enumerate(team_list, start=1):

        if args.tmemail:
            print(t.tm_email)
            if t.tm2_email:
                print(t.tm2_email)
            continue

        if args.cemail:
            if t.co_email:
                print(t.co_email)
            if t.ac_email:
                print(t.ac_email)
            continue

        if args.caddrs:
            if t.co_address:
                print(
                    '{:<31} {}, {}'.format(
                        'Shooters {} (Coach):'.format(t.sname),
                        t.co_name, t.co_address
                    )
                )
            if t.ac_address:
                print(
                    '{:<31} {}, {}'.format(
                        'Shooters {} (Assistant):'.format(t.sname),
                        t.ac_name, t.ac_address
                    )
                )
            continue

        if args.noresponse and t.responded == 1:
            continue

        if args.terse:
            # snm = t.sname[:9] + '...' if len(t.sname) > 12 else t.sname
            # tmn = t.tm_name[:15] + '...' if len(t.tm_name) > 18 else t.tm_name
            # tme = t.tm_email[:22] + '...' if len(t.tm_email) > 25 \
            #     else t.tm_email
            if args.both:
                if args.csv:
                    print(
                        '{},{},{},{},{},{},{},{}'.format(
                            t.edjba_code or '?',
                            t.sname or '?',
                            t.tm_name or '?',
                            t.tm_email or '?',
                            t.tm_mobile or '?',
                            t.co_name or '?',
                            t.co_email or '?',
                            t.co_mobile or '?',
                        )
                    )
                else:
                    print(
                        '{:7} {:12} {:25} {:40} {:10} {:25} {:40} {:10}'.format(
                            t.edjba_code or '?',
                            t.sname or '?',
                            t.tm_name or '?',
                            t.tm_email or '?',
                            t.tm_mobile or '?',
                            t.co_name or '?',
                            t.co_email or '?',
                            t.co_mobile or '?',
                        )
                    )
            elif args.csv:
                print(
                    '{},{},{},{},{}'.format(
                        t.edjba_code or '?',
                        t.sname or '?',
                        (t.co_name if args.coaches else t.tm_name) or '?',
                        (t.co_email if args.coaches else t.tm_email) or '?',
                        (t.co_mobile if args.coaches else t.tm_mobile) or '?',
                    )
                )
            else:
                print(
                    '{:7} {:12} {:25} {:40} {:10}'.format(
                        t.edjba_code or '?',
                        t.sname or '?',
                        (t.co_name if args.coaches else t.tm_name) or '?',
                        (t.co_email if args.coaches else t.tm_email) or '?',
                        (t.co_mobile if args.coaches else t.tm_mobile) or '?',
                    )
                )
        elif args.csv:
            if args.compats:
                print('{},FS,{},{}'.format(t.gender,t.age_group,t.number))
            elif args.both:
                print(
                    '{},{},{},{},{},{},{},{},{},{},{},{}'.format(
                        c, t.sname, t.grade or '?', t.edjba_id, t.edjba_code,
                        t.tm_name or '?', t.tm_email or '?', t.tm_mobile or '?',
                        t.co_name or '?', t.co_email or '?', t.co_mobile or '?',
                        t.regurl or '?',
                    )
                )
            else:
                print(
                    '{},{},{},{:02d},{},{:02d},{},{},{},{}'.format(
                        t.sname, t.edjba_id, t.edjba_code, t.age_group, t.gender,
                        t.number, t.grade if t.grade else '',
                        t.tm_name, t.tm_email, t.tm_mobile
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
