from argparse import ArgumentParser
import sys

from sbci import fetch_teams, fetch_participants, load_config, \
    fetch_trybooking, find_in_tb, to_fullname, to_date, find_age_group, to_bool


def main():

    parser = ArgumentParser()
    parser.add_argument('--details', '-d', action='store_true',
                        help='print player details')
    parser.add_argument('--partreport', default=None, metavar='F',
                        help='specify participant report file to use')
    parser.add_argument('--tbreport', default=None, metavar='F',
                        help='specify trybooking report file to use')
    parser.add_argument('--trybooking', '-t', action='store_true',
                        help='check trybooking payment')
    parser.add_argument('--rollover', '-r', action='store_true',
                        help='print team agegroups for next season')
    parser.add_argument('--unpaid', '-u', action='store_true',
                        help='print a list of unpaid players')
    parser.add_argument('--unpaidem', '-U', action='store_true',
                        help='print an email list for unpaid players')
    parser.add_argument('--younger', '-y', action='store_true',
                        help='flag players too young for age group')
    parser.add_argument('--diversity', '-D', action='store_true',
                        help='include diversity details')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    args = parser.parse_args()

    config = load_config()

    teams = fetch_teams()

    fetch_participants(teams, args.partreport, args.verbose)

    if args.trybooking:

        if not args.details:
            raise RuntimeError(
                'trybooking payment check requires --details arg'
            )

        tb = fetch_trybooking(config['tbmap'], args.tbreport, args.verbose)

        if len(tb) == 0:
            raise RuntimeError('no trybooking data in {}'.format(args.tbreport))

        npaid = nunpaid = 0

        if args.unpaid:
            unpaid_players = []

    nteams = nplayers = nbteams = ngteams = nboys = ngirls = 0

    for t in teams.values():

        nteams += 1
        nplayers += len(t.players)
        if t.gender == 'Boys':
            nbteams += 1
            nboys += len(t.players)
        else:
            ngteams += 1
            ngirls += len(t.players)

        if args.rollover:
            ctag = None
            cags = {}
            ntag = None
            nags = {}

        lines = []

        for p in t.players:

            name = to_fullname(p['first name'], p['last name'])
            dob = to_date(p['date of birth'])

            if args.rollover:
                cag = int(find_age_group(config['age_groups'], dob)[1:])
                cags[cag] = cags.setdefault(cag, 0) + 1
                if ctag is None or cag > ctag:
                    ctag = cag

                nag = int(
                    find_age_group(config['age_groups_next_season'], dob)[1:]
                )
                nags[nag] = nags.setdefault(nag, 0) + 1
                if ntag is None or nag > ntag:
                    ntag = nag

            if args.details:

                extra1 = extra2 = extra3 = ''

                if args.rollover:
                    extra1 += ' [U{:02d} => U{:02d}]'.format(cag, nag)

                if args.trybooking:
                    e = find_in_tb(tb, name)
                    if e is None:
                        extra2 += ' [unpaid]'
                        nunpaid += 1
                        if args.unpaid:
                            email_addrs = []
                            for k in (
                                'email',
                                'parent/guardian1 email',
                                'parent/guardian2 email',
                                # not really an emergency ...
                                # 'emergency contact email',
                            ):
                                email_addr = p.get(k, '').strip().lower()
                                if email_addr and email_addr not in email_addrs:
                                    if not email_addr.endswith('@icoud.com'):
                                        email_addrs.append(email_addr)
                            unpaid_players.append((name, email_addrs))
                    else:
                        npaid += 1
                        extra2 += ' [{}]'.format(e['Ticket Number'])

                ag_start, ag_end = map(
                    to_date,
                    config['age_groups']['U{:d}'.format(t.age_group)]
                )
                if dob < ag_start:
                    extra3 += ' [OLDER]'
                if args.younger and ag_end and dob > ag_end:
                    extra3 += ' [YOUNGER]'

                if args.diversity:
                    # aboriginal/torres strait islander
                    # parent/guardian born overseas? (NO/YES)
                    # parent/guardian 1 country of birth
                    # parent/guardian 2 country of birth
                    # disability? (NO/YES)
                    # disability type
                    # disability-other
                    # disability assistance
                    negatives = ('NO', 'Do not wish to disclose', 'NOT_SAYING')

                    v = p['aboriginal/torres strait islander']
                    atsi = None if v in negatives else v
                    if atsi:
                        extra3 += ' [ATSI: "{}"]'.format(atsi)

                    v = p['parent/guardian born overseas?']
                    pos = False if v in negatives else to_bool(v)
                    p1c = p['parent/guardian 1 country of birth']
                    p2c = p['parent/guardian 2 country of birth']
                    if pos:
                        extra3 += ' [POS: "{}","{}"]'.format(pos, p1c, p2c)

                    v = p['disability?']
                    disability = False if v in negatives else to_bool(v)
                    distype = p['disability type']
                    disother = p['disability-other']
                    disass = p['disability assistance']
                    if disability:
                        extra3 += ' [DISABILITY: "{}","{}","{}"]'.format(
                            distype, disother, disass
                        )

                lines.append(
                    '    {:30} - {}{}{}{}'.format(
                        name,
                        dob.strftime('%d/%m/%Y'), extra1,
                        extra2,
                        extra3,
                    )
                )

        extra = ''
        if args.rollover:
            if ctag is None:
                sctag = '___'
            else:
                sctag = 'U{:02d}'.format(ctag)
            if ntag is None:
                sntag = '___'
            else:
                sntag = 'U{:02d}'.format(ntag)
            extra += ' [{} => {}]'.format(sctag, sntag)
            if args.verbose:
                for k, v in sorted(nags.items(), key=lambda i: i[0]):
                    extra += ' {:d}xU{:02d}'.format(v, k)

        print(
            '{:12} [{}] - {:2d} players{}'.format(
                t.sname, t.edjba_code, len(t.players), extra
            )
        )
        for line in lines:
            print(line)

    if args.details:
        print(
            'Total of {:2d} teams ({} boys, {} girls)'.format(
                nteams, nbteams, ngteams
            )
        )
        print(
            'Total of {:2d} players ({} boys, {} girls)'.format(
                nplayers, nboys, ngirls
            )
        )
        if args.trybooking:
            print(
                'Total of {} have paid, {} have not paid'.format(
                    npaid, nunpaid
                )
            )
            if tb['by-name']:
                print(
                    '{} trybooking tickets unmatched'.format(
                        len(tb['by-name'])
                    )
                )
                for name, elist in tb['by-name'].items():
                    print(
                        '\t{} [{}]'.format(
                            name, ','.join(e['Ticket Number'] for e in elist)
                        )
                    )
            if tb['by-tnum']:
                print('{} trybooking tickets unused'.format(len(tb['by-tnum'])))
                for tnum, elist in tb['by-tnum'].items():
                    if len(elist) != 1:
                        raise RuntimeError('huh? (1)')
                    entry = elist[0]
                    if entry['Ticket Number'] != tnum:
                        raise RuntimeError('huh? (2)')
                    name = to_fullname(
                        entry['Ticket Data: Player First Name'],
                        entry['Ticket Data: Player Family Name'],
                    )
                    print('\t{} [{}]'.format(name, tnum))
            if args.unpaid and len(unpaid_players) > 0:
                if args.unpaidem:
                    emlist = []
                else:
                    print('Unpaid player email addresses:')
                for num, (name, email) in enumerate(sorted(unpaid_players)):
                    if args.unpaidem:
                        for email_addr in email:
                            if email_addr not in emlist:
                                emlist.append(email_addr)
                    else:
                        print(
                            '    {:2d} - {:25s}: {}'.format(
                                num + 1, name, ', '.join(email)
                            )
                        )
                if args.unpaidem:
                    print(','.join(emlist))

    return 0


if __name__ == "__main__":
    sys.exit(main())
