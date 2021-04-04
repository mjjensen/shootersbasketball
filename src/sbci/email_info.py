from __future__ import print_function
from argparse import ArgumentParser
from html import escape
from email.mime.text import MIMEText
from getpass import getpass
import os
from sbci import fetch_teams, fetch_participants, load_config, \
    fetch_trybooking, find_in_tb, to_fullname, season
from smtplib import SMTP, SMTPException
# from smtplib import SMTP_SSL
# from ssl import create_default_context, SSLError
import sys
from time import sleep


def nesc(s):
    if s is None:
        return ''
    else:
        return escape(s, True)


def person_tr(label, name, email, mobile):
    if not name:
        return ''
    return '   <tr><td>{}:</td><td>&nbsp;</td><td><tt>{}</tt></td></tr>\n'\
        .format(label, nesc(name), nesc(email), nesc(mobile))


class SMTP_dummy(object):

    def __init__(self, host=None):
        if not os.path.isdir('out'):
            os.mkdir('out')
        self.num = 0

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

    parser = ArgumentParser()
    parser.add_argument('--auth', '-a', action='store_true',
                        help='authenticate to the email server')
    parser.add_argument('--coaches', '-c', action='store_true',
                        help='send to coaches instead of team managers')
    parser.add_argument('--details', '-d', action='store_true',
                        help='include coach and player details')
    parser.add_argument('--dryrun', '-n', action='store_true',
                        help='dont actually send email')
    parser.add_argument('--pause', '-p', action='store_true',
                        help='pause for 2 secs between messages')
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
    args = parser.parse_args()

    config = load_config()

    smtp_host = '192.168.128.200'
    if args.auth:
        if 'email_auth' in config:
            smtp_user, smtp_pass = config['email_auth']
        else:
            smtp_user = input('SMTP User: ')
            smtp_pass = getpass('SMTP Password: ')

    admin_email = 'admin@shootersbasketball.org.au'
    testing_email = 'murrayjens@gmail.com'
    subject_fmt = 'Registration info for {}'
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
  <p><i>[automated email - send queries to: {}]</i></p>
  <table>
   <tr>
    <td>Season:</td><td>&nbsp;</td><td><b><tt>''' + season.replace('-', ' ').title() + '''</tt></b></td>
   </tr>
   <tr>
    <td></td><td></td><td></td>
   </tr>
   <tr>
    <td>Team Name:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
   <tr>
    <td>EDJBA Id:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
   <tr>
    <td>EDJBA Code:</td><td>&nbsp;</td><td><tt>{}</tt></td>
   </tr>
{}{}{}\
   <tr>
     <td>Rego Link:</td><td>&nbsp;</td><td><a href="{}"><tt>{}</tt></a></td>
   </tr>
  </table>
{}\
 <body>
</html>'''

    teams = fetch_teams()

    if args.details:

        fetch_participants(teams, args.partreport, args.verbose)

        if args.trybooking:
            tbmap = config['tbmap']

            tb = fetch_trybooking(teams, tbmap, args.tbreport, args.verbose)

            if len(tb) == 0:
                raise RuntimeError(
                    'no trybooking data in {}'.format(args.tbreport)
                )

    player_keys = [
        ('last name', 'surname'),
        ('first name', 'firstname'),
        ('uniform number', 'singlet#'),
        ('date of birth', 'd.o.b'),
        ('parent/guardian1 first name', 'parent firstname'),
        ('parent/guardian1 last name', 'parent surname'),
        ('parent/guardian1 mobile number', 'parent mobile'),
        ('parent/guardian1 email', 'parent email'),
    ]

    # ssl_ctx = create_default_context()
    # with SMTP_SSL(smtp_host, smtp_port, context=ssl_ctx) as smtp:
    if True:
        if args.writefiles:
            smtp = SMTP_dummy()
        else:
            smtp = SMTP(smtp_host)

        # smtp.set_debuglevel(99)
        if args.auth:
            smtp.login(smtp_user, smtp_pass)

        for t in teams.values():

            print('{} [{}, {}]:'.format(t.name, t.edjba_id, t.edjba_code),
                  file=sys.stderr)

            recips = []
            if args.coaches:
                if t.co_email:
                    recips.append(t.co_email)
                if t.ac_email:
                    recips.append(t.ac_email)
            else:
                recips.append(t.tm_email)

            if not recips:
                print('\tSKIPPING (no recipients).', file=sys.stderr)
                continue

            pt = []
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
                            '     <td class="pt">{}</td>\n'.format(nesc(p[k]))
                        )
                    if args.trybooking:
                        e = find_in_tb(
                            tb, to_fullname(p['first name'], p['last name'])
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

            msg = MIMEText(
                body_fmt.format(
                    '{', '}',
                    nesc(admin_email),
                    nesc(t.name),
                    nesc(t.edjba_id),
                    nesc(t.edjba_code),
                    person_tr(
                        'Team Manager', t.tm_name, t.tm_email, t.tm_mobile
                    ),
                    person_tr(
                        'Coach', t.co_name, t.co_email, t.co_mobile
                    ) if args.details else '',
                    person_tr(
                        'Asst Coach', t.ac_name, t.ac_email, t.ac_mobile
                    ) if args.details else '',
                    nesc(t.regurl),
                    nesc(t.regurl),
                    ''.join(pt),
                ),
                'html',
            )

            msg['From'] = admin_email
            msg['To'] = ', '.join(recips)
            msg['Cc'] = admin_email
            msg['Subject'] = subject_fmt.format(t.name)

            print('\tsending to {}...'.format(recips), end='', file=sys.stderr)
            if args.testing:
                recips = [testing_email]
            else:
                recips.append(admin_email)
            try:
                if args.dryrun:
                    print(
                        '\n*****|{}|{}|\n{}'.format(
                            admin_email, recips, msg.as_string()
                        ),
                        file=sys.stderr
                    )
                else:
                    smtp.sendmail(admin_email, recips, msg.as_string())
                print('done.', file=sys.stderr)
            except KeyboardInterrupt:
                print('\nInterrupted!', file=sys.stderr)
                sys.exit(0)
            except SMTPException as e:
                if hasattr(e, 'smtp_error'):
                    m = e.smtp_error
                else:
                    m = repr(e)
                print('exception - {}'.format(m), file=sys.stderr)

            if args.testing:
                break
            if args.pause:
                sleep(2)

        smtp.quit()

        if args.details and args.trybooking:

            if tb['by-name']:

                print(
                    '{} trybooking tickets unmatched'.format(
                        len(tb['by-name'])
                    ),
                    file=sys.stderr
                )

                for name, elist in tb['by-name'].items():

                    print(
                        '\t{} [{}]'.format(
                            name, ','.join(e['Ticket Number'] for e in elist)
                        ),
                        file=sys.stderr
                    )

            if tb['by-tnum']:

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

                    print('\t{} [{}]'.format(name, tnum), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
