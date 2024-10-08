# from smtplib import SMTP_SSL
# from ssl import create_default_context, SSLError

from __future__ import print_function

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from email.mime.text import MIMEText
from getpass import getpass
from html import escape
import os
from smtplib import SMTP, SMTPException
from ssl import create_default_context, Purpose
import sys
from time import sleep

from sbci import fetch_teams, fetch_participants, load_config, \
    fetch_trybooking, find_in_tb, to_fullname, season


def nesc(s):
    if s is None:
        return ''
    else:
        return escape(str(s), True)


def person_tr(label, name, email, mobile):
    if not name:
        return ''
    return '   <tr><td>{}:</td><td>&nbsp;</td><td><tt>{}</tt></td></tr>\n'\
        .format(label, nesc(name), nesc(email), nesc(mobile))


class SMTP_dummy(object):

    def __init__(self, *_args):
        if not os.path.isdir('out'):
            os.mkdir('out')
        self.num = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def set_debuglevel(self, n):
        pass

    def login(self, user, pw):
        pass

    def sendmail(self, sender, recips, msg):
        self.num += 1
        filename = os.path.join('out', 'msg{:02d}.html'.format(self.num))
        with open(filename, 'w') as fd:
            fd.write('{}\n'.format(msg))

    def quit(self):
        pass


def main():

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--auth', '-a', action='store_true',
                        help='authenticate to the email server')
    parser.add_argument('--both', '-b', action='store_true',
                        help='send to both team managers and coaches')
    parser.add_argument('--coaches', '-c', action='store_true',
                        help='send to coaches instead of team managers')
    parser.add_argument('--details', '-d', action='store_true',
                        help='include coach and player details')
    parser.add_argument('--nocoach', '-N', action='store_true',
                        help='do not include coach details')
    parser.add_argument('--dryrun', '-n', action='store_true',
                        help='dont actually send email')
    parser.add_argument('--pause', '-p', action='store_true',
                        help='pause for 5 secs between messages')
    parser.add_argument('--partreport', default=None, metavar='F',
                        help='specify participants report file to use')
    parser.add_argument('--testing', '-t', action='store_true',
                        help='just send one test email to a test address')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='print verbose messages')
    parser.add_argument('--writefiles', '-w', action='store_true',
                        help='write to files instead of sending email')
    parser.add_argument('--tbreport', default=None, metavar='F',
                        help='specify trybooking report file to use')
    parser.add_argument('--trybooking', '-T', action='store_true',
                        help='check trybooking payment and include in details')
    parser.add_argument('--prepend', '-P', default=None, metavar='F',
                        help='specify file to prepend to html body')
    parser.add_argument('--append', '-A', default=None, metavar='F',
                        help='specify file to append to html body')
    parser.add_argument('--relay', '-R', default='smtp-relay.gmail.com:587',
                        metavar='H[:P]', help='specify relay host and port')
    parser.add_argument('--fqdn', '-F', default=None, metavar='H',
                        help='specify the fqdn for the EHLO request')
    parser.add_argument('teams', nargs='*',
                        help='if present, limit teams that are sent info')
    args = parser.parse_args()

    config = load_config()

    if ':' in args.relay:
        smtp_host, smtp_port = args.relay.split(':')
    else:
        smtp_host = args.relay
        smtp_port = 587

    if args.auth:
        if 'email_auth' in config:
            smtp_user, smtp_pass = config['email_auth']
        else:
            smtp_user = input('SMTP User: ')
            smtp_pass = getpass('SMTP Password: ')

    smtp_fqdn = args.fqdn
    if smtp_fqdn is None:
        smtp_fqdn = config.get('email_fqdn')

    if args.writefiles:
        smtp_class = SMTP_dummy
    else:
        smtp_class = SMTP

    admin_email = 'admin@shootersbasketball.org.au'
    testing_email = 'murrayjens@gmail.com'
    subject_fmt = 'Registration info for {}'
    season_label = config.get('season', season.replace('-', ' ').title())
    body_fmt = '''\
<html>
 <head>
  <style>
   .pt {}
    border: 1px solid black;
    margin-top: 1em;
   {}
  </style>
 </head>
 <body>
{}\
  <table>
   <tr>
    <td>Season:</td><td>&nbsp;</td><td><b><tt>''' \
        + season_label + '''</tt></b></td>
   </tr>
   <tr>
    <td></td><td></td><td></td>
   </tr>
   <tr>
    <td>Team Name:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
   <tr>
    <td>EDJBA Name:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
   <tr>
    <td>EDJBA Code:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
{}{}{}{}\
   <tr>
    <td>Rego Link:</td>
    <td>&nbsp;</td>
    <td><a href="{}" target="_blank"><tt>{}</tt></a></td>
   </tr>
  </table>
{}{}\
  <p><i>[automated email - send queries to: {}]</i></p>
 <body>
</html>'''

    teams = fetch_teams()

    if len(args.teams) > 0:
        teamnames = args.teams[:]
        newteams = {}
        for sname, t in teams.items():
            if sname in teamnames:
                newteams[sname] = t
                teamnames.remove(sname)
        if len(teamnames) > 0:
            raise RuntimeError('Unknown team names: {}'.format(teamnames))
        teams = newteams

    if args.details:

        player_keys = [
            ('last_name', 'surname'),
            ('first_name', 'firstname'),
            ('date_of_birth', 'd.o.b'),
            ('parent1_first_name', 'parent firstname'),
            ('parent1_last_name', 'parent surname'),
            ('parent1_mobile', 'parent mobile'),
            ('parent1_email', 'parent email'),
        ]

        fetch_participants(teams, args.partreport, args.verbose,
                           player_moves=config.get('player_moves'))

        if args.trybooking:
            tbmap = config['tbmap']

            tb = fetch_trybooking(tbmap, args.tbreport, args.verbose)

            if len(tb) == 0:
                raise RuntimeError(
                    'no trybooking data in {}'.format(args.tbreport)
                )

    # used this:
    # https://stackoverflow.com/a/60301124

    with smtp_class(smtp_host, int(smtp_port), smtp_fqdn) as smtp:

        # smtp.set_debuglevel(99)

        if smtp_class is SMTP:
            smtp.starttls(
                context=create_default_context(purpose=Purpose.SERVER_AUTH)
            )
            if args.auth:
                smtp.login(smtp_user, smtp_pass)

        for t in teams.values():

            if args.verbose:
                print('{} [{}, {}]:'.format(t.name, t.edjba_id, t.edjba_code),
                      file=sys.stderr)

            recips = []
            if args.coaches or args.both:
                if t.co_email:
                    recips.append(t.co_email)
                if t.ac_email:
                    recips.append(t.ac_email)
            if not args.coaches or args.both:
                recips.append(t.tm_email)
                if t.tm2_email:
                    recips.append(t.tm2_email)

            if not recips:
                if args.verbose:
                    print('\tSKIPPING (no recipients).', file=sys.stderr)
                continue

            if args.verbose:
                print('\tRecipients: {}'.format(recips), file=sys.stderr)

            prepend_html = []
            if args.prepend:
                with open(args.prepend, 'r') as fd:
                    for line in fd.read().splitlines():
                        prepend_html.append('{}\n'.format(line))

            pt = []  # player table
            if args.details:
                pt.append('  <table class="pt">\n')
                pt.append('   <thead>\n')
                pt.append('    <tr>\n')
                pt.append('     <th class="pt">#</th>\n')
                for _, h in player_keys:
                    pt.append(
                        '     <th class="pt">{}</th>\n'.format(nesc(h.title()))
                    )
                if args.trybooking:
                    pt.append(
                        '     <th class="pt">{}</th>\n'.format(nesc('Ticket#'))
                    )
                pt.append('    </tr>\n')
                pt.append('   </thead>\n')
                pt.append('   <tbody>\n')
                for n, p in enumerate(t.players):
                    pt.append('    <tr>\n')
                    pt.append('     <td class="pt">{}</td>\n'.format(n + 1))
                    for k, _ in player_keys:
                        pt.append(
                            '     <td class="pt">{}</td>\n'.format(
                                nesc(getattr(p, k))
                            )
                        )
                    if args.trybooking:
                        e = find_in_tb(
                            tb, to_fullname(p.first_name, p.last_name)
                        )
                        pt.append(
                            '     <td class="pt">{}</td>\n'.format(
                                'unpaid' if e is None
                                else nesc(e['Ticket Number'])
                            )
                        )
                    pt.append('    </tr>\n')
                pt.append('   </tbody>\n')
                pt.append('  </table>\n')

            append_html = []
            if args.append:
                with open(args.append, 'r') as fd:
                    for line in fd.read().splitlines():
                        append_html.append('{}\n'.format(line))

            msg = MIMEText(
                body_fmt.format(
                    '{', '}',
                    ''.join(prepend_html),
                    nesc(t.name),
                    nesc(t.edjba_id),
                    nesc(t.edjba_code),
                    person_tr(
                        'Team Manager', t.tm_name, t.tm_email, t.tm_mobile
                    ),
                    person_tr(
                        'Coach', t.co_name, t.co_email, t.co_mobile
                    ) if args.details and not args.nocoach else '',
                    person_tr(
                        'Asst Coach', t.ac_name, t.ac_email, t.ac_mobile
                    ) if args.details and not args.nocoach else '',
                    person_tr(
                        'Alt Team Manager',
                        t.tm2_name, t.tm2_email, t.tm2_mobile
                    ) if args.details else '',
                    nesc(t.regurl),
                    nesc(t.regurl),
                    ''.join(pt),
                    ''.join(append_html),
                    nesc(admin_email),
                ),
                'html',
            )

            msg['From'] = admin_email
            msg['To'] = ', '.join(recips)
            msg['Cc'] = admin_email
            msg['Subject'] = subject_fmt.format(t.name)
            msg['Return-Path'] = admin_email

            if args.verbose:
                print('\tsending to {}...'.format(recips), end='',
                      file=sys.stderr)
            if args.testing:
                recips = [testing_email]
            else:
                recips.append(admin_email)
            try:
                if args.dryrun:
                    if args.verbose:
                        print(
                            '\n*****|{}|{}|\n{}'.format(
                                admin_email, recips, msg.as_string()
                            ),
                            file=sys.stderr
                        )
                else:
                    smtp.sendmail(admin_email, recips, msg.as_string())
                if args.verbose:
                    print('done.', file=sys.stderr)
            except KeyboardInterrupt:
                if args.verbose:
                    print('\nInterrupted!', file=sys.stderr)
                sys.exit(0)
            except SMTPException as e:
                if hasattr(e, 'smtp_error'):
                    m = e.smtp_error
                else:
                    m = repr(e)
                if args.verbose:
                    print('exception - {}'.format(m), file=sys.stderr)

            if args.testing:
                break
            if args.pause:
                sleep(5)

    if args.details and args.trybooking:

        if tb['by-name']:

            if args.verbose:
                print(
                    '{} trybooking tickets unmatched'.format(
                        len(tb['by-name'])
                    ),
                    file=sys.stderr
                )

            for name, elist in tb['by-name'].items():

                if args.verbose:
                    print(
                        '\t{} [{}]'.format(
                            name, ','.join(e['Ticket Number'] for e in elist)
                        ),
                        file=sys.stderr
                    )

        if tb['by-tnum']:

            if args.verbose:
                print('{} trybooking tickets unused'.format(len(tb['by-tnum'])),
                      file=sys.stderr)

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

                if args.verbose:
                    print('\t{} [{}]'.format(name, tnum), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
