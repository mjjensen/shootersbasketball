#!/usr/bin/env python2.7
# encoding: utf-8
'''
progtmpl -- [shortdesc]

[longdesc]
--
@version:    [version]
@created:    [creation_date]
@author:     [user_name]
@copyright:  2018 [organization_name]. All rights reserved.
@license:    [license]
@contact:    [user_email]
$Date$
$Author$
$Revision$
'''
from __future__ import print_function

from argparse import ArgumentParser
import sys

from sbcilib.utils import get_program_info, SbciHelpFormatter


def main(argv=None):
    '''Command line options.'''

    if argv is not None:
        sys.argv.extend(argv)

    try:
        # Setup argument parser
        program_info = get_program_info()
        parser = ArgumentParser(
            description='''%{shortdesc}s

  Created by %{author}s on %{created}s.
  Copyright %{copyright}s

  Licensed under the %{license}s
''' % program_info,
            formatter_class=SbciHelpFormatter)
        parser.add_argument(
            '-V',
            '--version',
            action='version',
            version='%%(prog)s %(version)s (%(date)s)' % program_info)
        parser.add_argument(
            '-e',
            '--exclude',
            dest='exclude',
            help='exclude paths matching this regex pattern.'
            ' [default: %(default)s]',
            metavar='RE')
        parser.add_argument(
            '-i',
            '--include',
            dest='include',
            help='only include paths matching this regex pattern.'
            ' Note: exclude is given preference over include.'
            ' [default: %(default)s]',
            metavar='RE')
        parser.add_argument(
            '-r',
            '--recursive',
            dest='recurse',
            action='store_true',
            help='recurse into subfolders [default: %(default)s]')
        parser.add_argument(
            '-v',
            '--verbose',
            dest='verbose',
            action='count',
            help='set verbosity level [default: %(default)s]')
        parser.add_argument(
            dest='paths',
            help='paths to folder(s) with source file(s).'
            ' [default: %(default)s]',
            metavar='path',
            nargs='+')

        # Process arguments
        args = parser.parse_args()

        paths = args.paths
        verbose = args.verbose
        recurse = args.recurse
        inpat = args.include
        expat = args.exclude

        if verbose > 0:
            print('Verbose mode on')
            if recurse:
                print('Recursive mode on')
            else:
                print('Recursive mode off')

        if inpat and expat and inpat == expat:
            raise CLIError('include and exclude pattern are equal! Nothing will be processed.')

        for inpath in paths:
            ### do something with inpath ###
            print(inpath)
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * ' '
        sys.stderr.write(program_name + ': ' + repr(e) + '\n')
        sys.stderr.write(indent + '  for help use --help')
        return 2

if __name__ == '__main__':
    if DEBUG:
        sys.argv.append('-h')
        sys.argv.append('-v')
        sys.argv.append('-r')
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'teams.zzz_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open('profile_stats.txt', 'wb')
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
