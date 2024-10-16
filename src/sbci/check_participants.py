from argparse import ArgumentParser
from sbci import fetch_teams, fetch_participants, load_config, \
    to_date, to_fullname
import sys


def main():

    parser = ArgumentParser()
    parser.add_argument('--report', '-r', default=None, metavar='FILE',
                        help='specify report file to use')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--younger', '-y', action='store_true',
                        help='print players younger than their age group')
    args = parser.parse_args()

    config = load_config()

    teams = fetch_teams()

    fetch_participants(teams, args.report, args.verbose,
                       player_moves=config.get('player_moves'))

    def pcmp(what, sname, code, p, name, email, mobile, wwcnum, wwcexp):

        pname = p.first_name + ' ' + p.last_name
        if name is None:
            print(
                '***** {:12} [{}] : {} name is None! ({})'.format(
                    sname, code, what, pname
                )
            )
        elif name.strip().lower() != pname.lower():
            print(
                '***** {:12} [{}] : {} name mismatch! ({}!={})'.format(
                    sname, code, what, name, pname
                )
            )

        if email is None:
            print(
                '***** {:12} [{}] : [{}] : {} email is None! ({})'.format(
                    sname, code, pname, what, p.email
                )
            )
        elif email.lower() != p.email.lower():
            print(
                '***** {:12} [{}] : [{}] : {} email mismatch! ({}!={})'.format(
                    sname, code, pname, what, email, p.email
                )
            )

        if mobile is None:
            print(
                '***** {:12} [{}] : [{}] : {} mobile is None! ({})'.format(
                    sname, code, pname, what, p.mobile
                )
            )
        else:
            pmobile = p.mobile.lower()
            if pmobile.startswith('+61'):
                pmobile = pmobile.replace('+61', '0', 1)
            elif not pmobile.startswith('0'):
                pmobile = '0' + pmobile
            if mobile.strip().lower() != pmobile:
                print(
                    '***** {:12} [{}] : [{}] : {} mobile mismatch! '
                    '({}!={})'.format(
                        sname, code, pname, what, mobile, pmobile
                    )
                )

        if wwcnum is None:
            print(
                '***** {:12} [{}] : [{}] : {} wwcnum is None! ({})'.format(
                    sname, code, pname, what, p.wwcc_number
                )
            )
        else:
            if wwcnum.strip().lower() == '109234a--03':
                wwcnum = '1092343a-03'
            pwwcnum = p.wwcc_number.lower()
            if pwwcnum.startswith('vit '):
                if len(pwwcnum) == 11 and pwwcnum[8] == '-':
                    pwwcnum = pwwcnum[:8] + pwwcnum[9:]
            else:
                if len(pwwcnum) == 9 and pwwcnum.isdigit():
                    pwwcnum = '0' + pwwcnum
                if len(pwwcnum) == 8:
                    pwwcnum += '-01'
                elif (
                    len(pwwcnum) == 10 and
                    pwwcnum[8].isdigit() and pwwcnum[9].isdigit()
                ):
                    pwwcnum = pwwcnum[:8] + '-' + pwwcnum[8:]
            if wwcnum.strip().lower() != pwwcnum:
                print(
                    '***** {:12} [{}] : [{}] : {} wwc number mismatch! '
                    '({}!={})'.format(
                        sname, code, pname, what, wwcnum, pwwcnum
                    )
                )

        if wwcexp is None:
            print(
                '***** {:12} [{}] : [{}] : {} wwcexp is None! ({})'.format(
                    sname, code, pname, what, p.wwcc_expiry
                )
            )
        else:
            pwwcexp = p.wwcc_expiry.lower()
            if not pwwcexp.endswith(' 00:00:00.000'):
                pwwcexp += ' 00:00:00.000'
            if wwcexp.lower() != pwwcexp:
                print(
                    '***** {:12} [{}] : [{}] : {} wwcexp mismatch! '
                    '({}!={})'.format(
                        sname, code, pname, what, wwcexp, pwwcexp
                    )
                )

    for t in teams.values():

        ag_start_s, ag_end_s = config['age_groups']['U{:d}'.format(t.age_group)]

        ag_start = to_date(ag_start_s)
        ag_end = to_date(ag_end_s)

        for p in t.players:

            dob = p.date_of_birth

            if dob < ag_start or (args.younger and ag_end and dob > ag_end):
                print(
                    '***** {:12} [{}] : {} - {}'.format(
                        t.sname, t.edjba_code,
                        to_fullname(p.first_name, p.last_name),
                        p.date_of_birth,
                    )
                )
                # print('S={},E={},D={}'.format(ag_start, ag_end, dob))

        if len(t.managers) == 0:
            print(
                '***** {:12} [{}] : No Team Managers!'.format(
                    t.sname, t.edjba_code
                )
            )
        else:
            pcmp(
                'Team Manager', t.sname, t.edjba_code, t.managers[0],
                t.tm_name, t.tm_email, t.tm_mobile, t.tm_wwcnum, t.tm_wwcexp
            )
            if len(t.managers) > 1:
                print(
                    '***** {:12} [{}] : more than 1 team manager!'.format(
                        t.sname, t.edjba_code
                    )
                )
                n = 2
                for m in t.managers[1:]:
                    print(
                        '***** {:12} [{}] : T/M{} = {}'.format(
                            t.sname, t.edjba_code, n, m
                        )
                    )
                    n += 1

        if len(t.coaches) == 0:
            print(
                '***** {:12} [{}] : No Coaches!'.format(
                    t.sname, t.edjba_code
                )
            )
        else:
            pcmp(
                'Coach', t.sname, t.edjba_code, t.coaches[0],
                t.co_name, t.co_email, t.co_mobile, t.co_wwcnum, t.co_wwcexp
            )
            if len(t.coaches) > 1:
                pcmp(
                    'Assistant Coach', t.sname, t.edjba_code, t.coaches[1],
                    t.ac_name, t.ac_email, t.ac_mobile, t.ac_wwcnum, t.ac_wwcexp
                )
                if len(t.coaches) > 2:
                    print(
                        '***** {:12} [{}] : more than 2 coaches!'.format(
                            t.sname, t.edjba_code
                        )
                    )
                    n = 3
                    for m in t.coaches[1:]:
                        print(
                            '***** {:12} [{}] : Coach{} = {}'.format(
                                t.sname, t.edjba_code, n, m
                            )
                        )
                        n += 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
