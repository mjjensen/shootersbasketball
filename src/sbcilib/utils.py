'''
Created on 29 Jul. 2018

@author: jen117
'''
from __future__ import print_function

import __main__
from _collections import deque
from abc import ABCMeta, abstractmethod
from argparse import RawDescriptionHelpFormatter, ArgumentParser, SUPPRESS
import csv
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import inspect
import json
from logging import root, getLogger, Logger, basicConfig, DEBUG, INFO, WARN,\
    setLoggerClass
import os
import re
import sys
from threading import Lock

from enum import unique, IntEnum


class SbciCSVRecord(object):
    '''TODO'''

    # see: https://stackoverflow.com/a/25176504/2130789

    def __eq__(self, other):
        if isinstance(other, SbciCSVRecord):
            sdict = {k: v for k, v in self.__dict__.viewitems() if k[0] != '_'}
            odict = {k: v for k, v in other.__dict__.viewitems() if k[0] != '_'}
            return sdict == odict
        return NotImplemented

    def __ne__(self, other):
        result = self == other
        if result is not NotImplemented:
            return not result
        return NotImplemented

    def __hash__(self):
        return hash(tuple(sorted((k, v) for k, v in self.__dict__.viewitems()
                                 if k[0] != '_')))

    def __str__(self):
        return '[{}]'.format(
            ', '.join('{}={}'.format(k, v.encode('utf-8')
                                     if isinstance(v, unicode) else v)
                      for k, v in self.__dict__.viewitems() if k[0] != '_'))


class SbciCSVColumn(object):
    '''TODO'''

    def __init__(self, attr, parser, *args, **kwds):
        super(SbciCSVColumn, self).__init__()
        self.attr = attr
        self.parser = parser
        self.headings = args
        self.options = {'required': False, 'ignored': False}
        self.options.update(kwds)


class SbciCSVInfo(object):
    '''TODO'''

    def __init__(self, *args, **kwds):
        super(SbciCSVInfo, self).__init__()

        self.columns = args

        self.options = {}
        self.options.update(kwds)

        self.attrs = {}
        self.headings = {}
        self.required = []
        self.optional = []
        self.ignored = []

        for column in self.columns:
            if column.attr in self.attrs:
                raise RuntimeError('duplicate attr: {}'.format(column.attr))
            self.attrs[column.attr] = column

            if column.options['required']:
                self.required.append(column.attr)
            elif column.options['ignored']:
                self.ignored.append(column.attr)
            else:
                self.optional.append(column.attr)

            for heading in column.headings:
                if heading in self.headings:
                    raise RuntimeError('duplicate heading: {}'.format(heading))
                self.headings[heading] = column


def read_csv(csvfile, csvinfo, verbose=0, reverse=False,
             initiate=None, terminate=None, fieldnames=None):
    '''TODO'''

    if initiate is None:
        if 'initiate' in csvinfo.options:
            initiate = csvinfo.options['initiate']

    if terminate is None:
        if 'terminate' in csvinfo.options:
            terminate = csvinfo.options['terminate']

    if fieldnames is None:
        if 'fieldnames' in csvinfo.options:
            fieldnames = csvinfo.options['fieldnames']

    if verbose > 0:
        print('Reading CSV file: {} ... '.format(csvfile))

    records = deque()

    with open(csvfile) as fd:

        if initiate is not None:
            initiate(fd)

        reader = csv.DictReader(fd)

        if fieldnames is not None:
            reader.fieldnames = fieldnames

        required = list(csvinfo.required)
        optional = list(csvinfo.optional)
        for fieldname in reader.fieldnames:
            heading = fieldname.strip()
            if heading is None or heading == '':
                continue
            if heading not in csvinfo.headings:
                if verbose > 0:
                    print('\tunknown column heading: {}'.format(heading))
            else:
                column = csvinfo.headings[heading]
                if column.options['required']:
                    required.remove(column.attr)
                elif not column.options['ignored']:
                    optional.remove(column.attr)
        if len(required) > 0:
            raise RuntimeError('\trequired columns missing: {}'
                               .format(', '.join(required)))
        if len(optional) > 0 and verbose > 0:
            print('optional columns missing: {}'
                  .format(', '.join(optional)))

        for row in reader:
            if verbose > 2:
                print('\trow={}'.format(row))

            if terminate is not None and terminate(row):
                break

            record = SbciCSVRecord()
            for heading, value in row.viewitems():
                if heading not in csvinfo.headings:
                    continue
                column = csvinfo.headings[heading]
                setattr(record, column.attr, column.parser(value))

            if verbose > 1:
                print('\trecord={}'.format(record))

            if reverse:
                records.append(record)
            else:
                records.appendleft(record)

    if verbose > 0:
        print('{} records read.'.format(len(records)))

    return records


@unique
class SbciEnum(IntEnum):
    '''TODO'''

    @classmethod
    def __real_new__(cls, value, alt_value):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.alt_value = alt_value
        return obj

    def __new__(cls, value, alt_value):
        return cls.__real_new__(value, alt_value)

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name

    @classmethod
    def by_alt_value(cls, alt_value):
        if alt_value is None:
            return None
        for e in cls:
            if e.alt_value == alt_value:
                return e
        else:
            raise ValueError('{} not a valid SbciEnum!'.format(alt_value))


class SbciException(Exception):
    '''Generic exception to raise and log different fatal errors.'''

    def __init__(self, msg):
        super(SbciException).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def _class_logger_name(obj):
    '''TODO'''
    if obj is None:
        return None
    if not inspect.isclass(obj) and not inspect.ismodule(obj):
        obj = type(obj)
#         return '.'.join([obj.__module__, obj.__name__])
    return obj.__name__


def _class_logger(obj=None):
    '''TODO'''
    name = _class_logger_name(obj)
    if name is None or name == '':
        return root
    return getLogger(name)


class SbciLog(object):
    '''TODO'''

    _classlock = Lock()
    _configured = False
    _debug_level = 0
    _verbose_level = 0

    @property
    def logger(self):
        return _class_logger(self)

    @classmethod
    def try_configure(cls):
        with cls._classlock:
            if cls._configured:
                return

            if cls._debug_level > 0:
                logging_level = DEBUG
            elif cls._verbose_level > 0:
                logging_level = INFO
            else:
                logging_level = WARN

            setLoggerClass(SbciLogger)
            basicConfig(level=logging_level)

            cls._configured = True

    @classmethod
    def get_debug_level(cls):
        with cls._classlock:
            return cls._debug_level

    @classmethod
    def set_debug_level(cls, debug_level):
        with cls._classlock:
            result = cls._debug_level
            cls._debug_level = int(debug_level)
            return result

    @classmethod
    def get_verbose_level(cls):
        with cls._classlock:
            return cls._verbose_level

    @classmethod
    def set_verbose_level(cls, verbose_level):
        with cls._classlock:
            result = cls._verbose_level
            cls._verbose_level = int(verbose_level)
            return result


class SbciLogger(Logger):
    '''TODO'''

    def __init__(self, name=None, *args, **kwds):
        if name is None:
            name = _class_logger_name(self)
        super(SbciLogger, self).__init__(name, *args, **kwds)

    def _log(self, level, msg, args, exc_info=None, extra=None):
        '''all logger methods that actually log something go through this'''
        SbciLog.try_configure()
        super(SbciLogger, self)._log(level, msg, args, exc_info, extra)

    def debugif(self, msg_debug_level, msg, *args, **kwds):
        if SbciLog._debug_level >= msg_debug_level:
            self.debug(msg, *args, **kwds)


class SbciHelpFormatter(RawDescriptionHelpFormatter):
    '''I don't like usage: - make it Usage: ...'''

    def add_usage(self, *args):
        '''override add_usage() and set the usage prefix if not specified'''
        if len(args) == 4 and args[3] is None:
            args = args[:3]
        if len(args) == 3:
            args += ('Usage: ', )
        super(SbciHelpFormatter, self).add_usage(*args)


def _get_docstring_lines(obj=None):
    '''locate and return the __doc__ string of the main python module'''
    if obj is not None:
        if hasattr(obj, '__module__'):
            name = obj.__module__
        elif hasattr(obj, '__name'):
            name = obj.__name__
        else:
            name = obj
        if name in sys.modules:
            m = sys.modules[name]
            if hasattr(m, '__doc__') and m.__doc__ is not None:
                lines = m.__doc__.splitlines()
                if len(lines) >= 4:
                    return lines
    if hasattr(__main__, '__doc__') and __main__.__doc__ is not None:
        lines = __main__.__doc__.splitlines()
        if len(lines) >= 4:
            return lines
    return('', '<program __doc__ string UNAVAILABLE!>') * 2


_docstring_pattern = re.compile(r'^[$@]([^:\$]+):?\s*(.*?)\s*\$?$')


def _get_program_info():
    '''TODO'''
    lines = _get_docstring_lines()

    info = {}

    # idea taken from:
    # https://doughellmann.com/blog/2012/04/30/determining-the-name-of-a-process-from-python/
    if hasattr(__main__, '__file__'):
        progfile = __main__.__file__
    else:
        progfile = sys.argv[0]
    info['file'] = os.path.abspath(progfile)

    progname = os.path.basename(info['file'])
    if progname.lower().endswith('.py'):
        info['name'] = progname[:-3]
    else:
        info['name'] = progname

    info['shortdesc'] = lines[1]

    n = 4
    for line in lines[4:]:
        if line.startswith(('@', '$', '--')):
            break
        n += 1
    e = n
    while e > 4 and lines[e - 1] == '':
        e -= 1
    info['longdesc'] = '\n'.join(lines[3:e])

    for line in lines[n:]:
        m = _docstring_pattern.match(line)
        if m is not None:
            info[m.group(1).lower()] = m.group(2)

    return info


class SbciMain(SbciLog):
    '''TODO'''
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwds):
        super(SbciMain, self).__init__(*args, **kwds)

        self.info = _get_program_info()

        self.parser = ArgumentParser(
            prog=self.info['name'],
            description='''{shortdesc}

  Created by {author} on {created}.
  Copyright {copyright}.

  Licensed under the {license}.
'''.format(**self.info),
            formatter_class=SbciHelpFormatter,
            add_help=False)

        self.define_args()

        self.args = self.parser.parse_args()

        debug_level = getattr(self.args, 'debug', 0)
        SbciLog.set_debug_level(debug_level)

        verbose_level = getattr(self.args, 'verbose', 0)
        SbciLog.set_verbose_level(verbose_level)

        self.try_configure()

        self.logger.info('{name} {version} ({date})'.format(**self.info))

        verbose = getattr(args, 'verbose', 0)
        if verbose > 0:
            self.logger.info('%s', self.program_shortdesc)
            self.logger.info("Verbose mode on (level %d)", verbose)

            if hasattr(args, 'debug'):
                if args.debug > 0:
                    self.logger.info("Debug mode on (level=%d)", args.debug)
                else:
                    self.logger.info("Debug mode off")

    def define_args(self):
        '''TODO'''

        self.parser.add_argument(
            '--help', '-h',
            action='help', default=SUPPRESS,
            help='show this help message and exit')

        self.parser.add_argument(
            '--version', '-V',
            action='version',
            version='%(prog)s {version} ({date})'.format(**self.info))

        self.parser.add_argument(
            '--verbose', '-v',
            action='count', default=0,
            help='increase verbosity level [default: %(default)d]')

        self.parser.add_argument(
            "--debug", "-D",
            type=int, default=0,
            nargs='?', const=1, metavar='N',
            help="set debugging level [default: %(default)d]")

        self.parser.add_argument(
            "--profile",
            action="store_true",
            help="enable profile data output [default: %(default)s]")

    def run(self):
        '''TODO'''
        result = os.EX_OSERR

        try:
            self.setup()
        except BaseException as e:
            self.logger.exception('Exception (during setup): %r', e)
        else:
            try:
                result = self.main()
            except (KeyboardInterrupt, SystemExit):
                self.logger.info('Attempting normal exit ...')
                result = os.EX_OK
            except BaseException as e:
                self.logger.exception('Exception: %r', e)
        finally:
            try:
                self.cleanup()
            except BaseException as e:
                self.logger.exception('Exception (during cleanup): %r', e)

        return result

    def setup(self):
        '''TODO'''
        pass

    @abstractmethod
    def main(self):
        '''TODO'''
        pass

    def cleanup(self):
        '''TODO'''
        pass

    def profile_run(self):
        '''TODO'''
        import cProfile
        import pstats
        program_name = self.info['name']
        profile_filename = program_name + '_profile_data'
        stats_filename = program_name + "_profile_stats.txt"
        cProfile.runctx('self.run()', globals(), locals(), profile_filename)
        with open(stats_filename, "wb") as statsfile:
            p = pstats.Stats(profile_filename, stream=statsfile)
            stats = p.strip_dirs().sort_stats('cumulative')
            stats.print_stats()
        return os.EX_OK

    @classmethod
    def setuptools_entry(cls, *args, **kwds):
        '''class method to implement a standard "setuptools" entry point'''
        if not issubclass(cls, SbciMain):
            sys.stderr.write('%r is not a subclass of SbciMain!\n' % cls)
            return os.EX_SOFTWARE

        main = cls(*args, **kwds)

        if getattr(main.args, 'test', False):
            import doctest
            nfails, ntests = doctest.testmod(
                sys.modules[cls.__module__],
                verbose=(getattr(main.args, 'verbose', 0) > 0)
            )
            sys.stderr.write('%d out of %d tests failed.\n' % (nfails, ntests))
            return nfails
        if getattr(main.args, 'profile', False):
            return main.profile_run()
        else:
            return main.run()


def deduplicate(seq):
    # see: https://stackoverflow.com/a/25887387/2130789
    # but then I found ...
    # see: https://stackoverflow.com/a/480227/2130789
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def end_of_season():
    '''TODO'''
    today = date.today()
    end_of_summer = date(today.year, 3, 31)  # near enough is good enough
    if today <= end_of_summer:
        return end_of_summer
    end_of_winter = date(today.year, 9, 30)  # near enough is good enough
    if today <= end_of_winter:
        return end_of_winter
    return date(today.year + 1, 3, 31)


def is_under18(date_of_birth):
    '''TODO'''
    diff = relativedelta(end_of_season(), date_of_birth)
    return (diff.years < 18)


def prepare_str(s, allow_none):
    '''TODO'''
    if s is None:
        if allow_none:
            return None
        raise ValueError('string is None!')
    stmp = s.strip()
    if s == '':
        if allow_none:
            return None
        raise ValueError('string is empty!')
    return stmp


def date_str(s, fmt='%Y-%m-%d', allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt).date()


def time_str(s, fmt='%I:%M:%S %p', allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt).time()


def datetime_str(s, fmt='%Y-%m-%d %H:%M:%S.%f', allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return datetime.strptime(stmp, fmt)


def latin1_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return unicode(stmp, encoding='latin-1')


def currency_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    return float(stmp.replace(',', ''))


name2postcode = {
    'Melbourne':                 3000,
    'Southbank':                 3006,
    'Hoppers Crossing':          3029,
    'Moonee Ponds':              3039,
    'Brunswick East':            3057,
    'Sumner':                    3057,
    'Coburg':                    3058,
    'Fitzroy':                   3065,
    'Abbotsford':                3067,
    'Clifton Hill':              3068,
    'Northcote':                 3070,
    'Thornbury':                 3071,
    'Preston':                   3072,
    'Reservoir':                 3073,
    'Fairfield':                 3078,
    'Alphington':                3078,
    'Ivanhoe':                   3079,
    'Ivanhoe East':              3079,
    'Heidelberg Heights':        3081,
    'Bellfield':                 3081,
    'Eaglemont':                 3084,
    'Macleod':                   3085,
    'Macleod West':              3085,
    'Yallambie':                 3085,
    'Watsonia':                  3087,
    'Kew':                       3101,
    'East Kew':                  3102,
    'Balwyn North':              3104,
    'Bulleen':                   3105,
    'Doncaster':                 3108,
    'Camberwell':                3124,
    'Camberwell East':           3126,
    'Canterbury':                3126,
    'Box Hill South':            3128,
    'Patterson Lakes':           3197,
    'Carrum':                    3197,
    'Albert Park':               3206,
    'South Morang':              3752,
    'Como, WA':                  6152,
    'Little Lonsdale St, Vic':   8011,
}


postcode2name = {postcode: name for name, postcode in name2postcode.viewitems()}


def postcode_str(s, allow_none=True):
    '''TODO'''
    stmp = posint_str(s, allow_none)
    if stmp is None:
        return None
    postcode = int(stmp)
    if postcode not in postcode2name:
        raise RuntimeError('not a known postcode! (%r)' % s)
    return postcode


_phone_fixups = {}
try:
    with open('../misc/phone_fixups.json') as fd:
        _phone_fixups.extend(json.load(fd))
except BaseException:
    pass
_phone_pattern = re.compile(r'^\+?(61|0)?')


def phone_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    for r in ' \t\r\n-()[].':
        stmp = stmp.replace(r, '')
    if stmp.startswith('+61'):
        stmp = '0' + stmp[3:]
    if stmp.startswith(('3', '4')):
        stmp = '0' + stmp
    if stmp in _phone_fixups:
        return _phone_fixups[stmp]
    if _phone_pattern.match(stmp) is None:
        raise RuntimeError('not a valid phone number! (%r)' % s)
    return stmp


_email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def email_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    if _email_pattern.match(stmp) is None:
        raise RuntimeError('not a valid email address! (%r)' % s)
    return stmp


def posint_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    if not stmp.isdigit():
        raise RuntimeError('not a valid positive integer! (%r)' % s)
    return stmp


def boolean_str(s, allow_none=True):
    '''TODO'''
    stmp = prepare_str(s, allow_none)
    if stmp is None:
        return None
    if stmp.lower() in ('t', 'true', 'y', 'yes', 'on'):
        return True
    if stmp.lower() in ('f', 'false', 'n', 'no', 'off'):
        return False
    if not stmp.isdigit():
        raise RuntimeError('not a valid boolean string! (%r)' % s)
    return (int(stmp) != 0)
