#!/usr/bin/env python2.7
# encoding: utf-8
'''
progtmpl -- [shortdesc]

[longdesc]
--
@version:    [version]
@created:    [creation_date]
@author:     [user_name]
@copyright:  [year] [organization_name]. All rights reserved.
@license:    [license]
@contact:    [user_email]
$Date$
$Author$
$Revision$
'''
from __future__ import print_function

import os
from six.moves import xrange
import sys
from time import sleep

from sbcilib.utils import SbciMain


class Main(SbciMain):

    def main(self):
        try:
            print('Hello World!', end='')
            sys.stdout.flush()
            for _c in xrange(5):
                sleep(1)
                print('.', end='')
                sys.stdout.flush()
            print('Done!')
            return os.EX_OK
        except KeyboardInterrupt:
            print('\nGot Interrupted!')
            return os.EX_SOFTWARE


def main():
    '''function suitable for running via setuptools entry point'''
    return Main.setuptools_entry()


if __name__ == '__main__':
    sys.exit(main())
