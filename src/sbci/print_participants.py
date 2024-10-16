from argparse import ArgumentParser
from collections import namedtuple
from csv import DictReader
from datetime import datetime
from decimal import Decimal
from email.utils import getaddresses
from operator import itemgetter
import os
import re
import sys

from sbci import fetch_teams, fetch_participants, load_config, latest_report, \
    fetch_trybooking, find_in_tb, to_fullname, to_date, find_age_group, to_bool


def main():

    parser = ArgumentParser()
    parser.add_argument('--details', '-d', action='store_true',
                        help='print player details')
    parser.add_argument('--partreport', default=None, metavar='F',
                        help='specify participant report file to use')
    parser.add_argument('--tbreport', default=None, metavar='F',
                        help='specify trybooking report file to use')
    parser.add_argument('--xactreport', default=None, metavar='F',
                        help='specify PlayHQ transaction report file to use')
    parser.add_argument('--trybooking', '-t', action='store_true',
                        help='check trybooking payment')
    parser.add_argument('--unpaid', '-u', action='store_true',
                        help='print a list of unpaid players')
    parser.add_argument('--unpaidem', '-U', action='store_true',
                        help='print an email list for unpaid players')
    parser.add_argument('--rollover', '-r', action='store_true',
                        help='print team agegroups for next season')
    parser.add_argument('--playhq', '-p', action='store_true',
                        help='check PlayHQ payment')
    parser.add_argument('--younger', '-y', action='store_true',
                        help='flag players too young for age group')
    parser.add_argument('--diversity', '-D', action='store_true',
                        help='include diversity details')
    parser.add_argument('--postcodes', '-P', action='store_true',
                        help='include postcode summary')
    parser.add_argument('--allemail', '-A', action='store_true',
                        help='dump a list of all email addresses')
    parser.add_argument('--csv', '-C', action='store_true',
                        help='output in CSV format')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('teams', nargs='*',
                        help='limit output to the list of teams specified')
    args = parser.parse_args()

    if args.trybooking and args.playhq:
        raise RuntimeError('can\'t specify both --trybooking and --playhq!')

    config = load_config(verbose=args.verbose)

    teams = fetch_teams(verbose=args.verbose)

    fetch_participants(teams, args.partreport, args.verbose,
                       player_moves=config.get('player_moves'))

    team_list = []
    if args.teams:
        for team in args.teams:
            team_list.append(teams[team])
    else:
        team_list.extend(teams.values())

    if args.trybooking:

        if not args.details:
            raise RuntimeError('trybooking check requires --details arg')

        tb = fetch_trybooking(config['tbmap'], args.tbreport, args.verbose)

        if len(tb) == 0:
            raise RuntimeError('no trybooking data in {}'.format(args.tbreport))

    if args.playhq:

        if not args.details:
            raise RuntimeError('playhq check requires --details arg')

        def currency(s):
            if s is None or len(s) == 0:
                return Decimal()
            if not s.startswith('$'):
                raise RuntimeError('illegal currency value: {}'.format(s))
            return Decimal(s[1:])

        xactfile = args.xactreport
        if xactfile is None:
            xactfile, _ = latest_report('transactions')
            if xactfile is None:
                raise RuntimeError('no transactions report found!')
            if args.verbose:
                print(
                    '[transactions report selected: {} (realpath={})]'.format(
                        xactfile, os.path.realpath(xactfile)
                    )
                )

        # must match assignment below ...
        Xact = namedtuple('Xact', 'oip gvamt subt phqfee netamt vnam vcod vamt')

        # price = Decimal(config['pricing']['early'])
        xacts = {}

        with open(xactfile, 'r', newline='') as csvfile:

            reader = DictReader(csvfile)

            for xact in reader:

                name = xact.get('Name',
                                xact['First Name'] + ' ' + xact['Last Name'])
                rtype = xact.get('Type of Registration',
                                 xact['Type of Transaction'])
                role, rinfo, rseason, ptype, vnam, vcod, \
                    soip, sqty, sgvamt, ssubt, sphqfee, snetamt, svamt = \
                    itemgetter(
                        'Role', 'Registration',
                        'Season Name', 'Product Type', 'Voucher Name',
                        'Voucher Code', 'Order Item Price', 'Quantity',
                        'Government Voucher Amount Applied', 'Subtotal',
                        'PlayHQ Fee', 'Net Amount', 'Voucher Amount Applied',
                    )(xact)

                if (
                    role != 'Player' or
                    rtype != 'Competition' or
                    rinfo != 'EDJBA' or
                    rseason != config['edjba_season'] or
                    ptype != 'REGISTRATION'
                ):
                    if args.verbose:
                        print('ignore xact record: {}'.format(xact))
                    continue

                if int(sqty) != 1:
                    raise RuntimeError('Quantity not 1!')

                oip, gvamt, subt, phqfee, netamt, vamt = [
                    currency(s)
                    for s in (soip, sgvamt, ssubt, sphqfee, snetamt, svamt)
                ]

                if oip != gvamt + vamt + subt:
                    raise RuntimeError(
                        'oip[{}]!=gvamt[{}]+vamt[{}]+subt[{}]! {}'.format(
                            oip, gvamt, vamt, subt, xact
                        )
                    )

                if subt - phqfee != netamt:
                    raise RuntimeError(
                        'subt[{}]-phqfee[{}]!=netamt[{}]!'.format(
                            subt, phqfee, netamt
                        )
                    )

                if name in xacts:
                    print(
                        'duplicate transaction for {}! [xact={}]'.format(
                            name, xact
                        ),
                        file=sys.stderr
                    )
                    continue

                # must match namedtuple definition above ...
                xacts[name] = Xact(
                    oip, gvamt, subt, phqfee, netamt, vnam, vcod, vamt
                )

        if len(xacts) == 0:
            raise RuntimeError('no transactions in {}!'.format(xactfile))

    if args.trybooking or args.playhq:

        npaid = nunpaid = 0

        if args.unpaid:
            unpaid_players = []

    nteams = nplayers = nbteams = ngteams = nboys = ngirls = 0

    if args.postcodes:
        postcodes = {}
        councils = {}

        cn2pc = {
            'Darebin': (3070, 3071, 3072, 3073, 3078),
            'Banyule': (3079, 3081, 3084, 3085, 3087, 3088, 3093, 3094),
        }
        pc2cn = {pc: cn for cn in cn2pc for pc in cn2pc[cn]}

    if args.allemail:
        all_email_addrs = []

    for t in team_list:

        nteams += 1
        nplayers += len(t.players)
        if t.gender == 'Boys':
            nbteams += 1
            nboys += len(t.players)
        else:
            ngteams += 1
            ngirls += len(t.players)

        ctag = None
        cags = {}
        if args.rollover:
            ntag = None
            nags = {}

        lines = []

        for p in t.players:

            name = to_fullname(p.first_name, p.last_name, args.csv)
            dob = p.date_of_birth

            ags = find_age_group(config['age_groups'], dob)
            if ags is None:
                print(
                    '{} DoB {} not in any age group!'.format(name, dob),
                    file=sys.stderr
                )
                continue
            cag = int(ags[1:])
            cags[cag] = cags.setdefault(cag, 0) + 1
            if ctag is None or cag > ctag:
                ctag = cag

            email_addrs = []
            for a in 'email', 'parent1_email', 'parent2_email':
                email_addr = getattr(p, a)
                if email_addr is None:
                    continue
                email_addr = email_addr.lower()
                if email_addr and email_addr not in email_addrs:
                    if not email_addr.endswith('@icoud.com'):
                        email_addrs.append(email_addr)

            if args.allemail:
                for addr in getaddresses(email_addrs):
                    if addr not in all_email_addrs:
                        all_email_addrs.append(addr)

            if args.rollover:
                ags = find_age_group(config['age_groups_next_season'], dob)
                if ags is None:
                    print(
                        '{} DoB {} not in any age group!'.format(name, dob),
                        file=sys.stderr
                    )
                    continue
                nag = int(ags[1:])
                nags[nag] = nags.setdefault(nag, 0) + 1
                if ntag is None or nag > ntag:
                    ntag = nag

            if args.postcodes:
                pc = int(p.postcode)
                postcodes[pc] = postcodes.get(pc, 0) + 1

                cn = pc2cn.get(pc, 'Other')
                councils[cn] = councils.get(cn, 0) + 1

            if args.details:

                extra1 = extra2 = extra3 = ''

                if args.rollover:
                    extra1 += ' [U{:02d} => U{:02d}]'.format(cag, nag)

                if args.trybooking or args.playhq:
                    if args.trybooking:
                        e = find_in_tb(tb, name)
                    else:
                        k = p.first_name + ' ' + p.last_name
                        e = xacts.pop(k, None)
                    if e is None:
                        extra2 += ' [unpaid]'
                        nunpaid += 1
                        if args.unpaid:
                            unpaid_players.append((name, email_addrs))
                    else:
                        npaid += 1
                        if args.trybooking:
                            extra2 += ' [{}]'.format(e['Ticket Number'])
                        if args.playhq:
                            if e.vamt != 0:
                                extra2 += ' [{} <{}> = ${}]'.format(
                                    e.vnam, e.vcod, e.vamt
                                )
                            if e.gvamt != 0:
                                extra2 += ' [Govt Voucher = ${}]'.format(
                                    e.gvamt
                                )

                ag_start, ag_end = map(
                    to_date,
                    config['age_groups']['U{:d}'.format(t.age_group)]
                )
                if dob < ag_start:
                    extra3 += ' [OLDER]'
                if args.younger and ag_end and dob > ag_end:
                    extra3 += ' [YOUNGER]'

                if args.diversity:
                    # atsi
                    # parent/guardian born overseas
                    # parent/guardian 1 country of birth
                    # parent/guardian 2 country of birth
                    # disability?
                    # disability type
                    # disability-other
                    # disability assistance
                    negatives = ('NO', 'Do not wish to disclose', 'NOT_SAYING')

                    v = p.atsi  # aboriginal/torres strait islander
                    atsi = None if v in negatives else v
                    if atsi:
                        extra3 += ' [ATSI: "{}"]'.format(atsi)

                    v = p.parent_born_overseas
                    pos = False if v in negatives else to_bool(v)
                    p1c = p.parent1_country_of_birth
                    p2c = p.parent2_country_of_birth
                    if pos:
                        extra3 += ' [POS: "{}","{}"]'.format(p1c, p2c)

                    v = p.disability
                    disability = False if v in negatives else to_bool(v)
                    distype = p.disability_type
                    disother = p.disability_other
                    disass = p.disability_assistance
                    if disability:
                        extra3 += ' [DISABILITY: "{}","{}","{}"]'.format(
                            distype, disother, disass
                        )

                dobs = dob.strftime('%d/%m/%Y')
                if args.csv:
                    lines.append('{},{}'.format(name, dobs))
                else:
                    lines.append(
                        '    {:30} - {}{}{}{}'.format(
                            name, dobs, extra1, extra2, extra3,
                        )
                    )

        extra = ''
        if not args.rollover:
            extra += ' ['
            for k, v in sorted(cags.items(), key=lambda i: i[0]):
                extra += ' {:d}xU{:02d}'.format(v, k)
            extra += ' ]'
        else:
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

        if args.csv:
            print('{}'.format(t.sname))
        else:
            print(
                '{:12} [{} {}] - {:2d} players{}'.format(
                    t.sname, t.edjba_code, t.grade, len(t.players), extra
                )
            )
        for line in lines:
            print(line)

    if args.allemail:
        for _, addr in sorted(all_email_addrs):
            print(addr)

    if args.postcodes:
        print('Postcode Summary:')
        for pc, n in sorted(postcodes.items()):
            print('\t{}: {}'.format(pc, n))

        print('Council Summary:')
        for cn, n in sorted(councils.items()):
            print('\t{}: {}'.format(cn, n))

    if args.details and not args.csv:
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
        if args.trybooking or args.playhq:
            print(
                'Total of {} have paid, {} have not paid'.format(
                    npaid, nunpaid
                )
            )
        if args.trybooking:
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
        if args.trybooking or args.playhq:
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
