from __future__ import absolute_import, division, print_function
__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef

try:
    from ConfigParser import ConfigParser, NoOptionError # python 2
except ImportError:
    from configparser import ConfigParser, NoOptionError # python3
import os, shutil, multiprocessing, logging
from .logger import logger

class __SinglethonConfig:
    config = None



def get_package_config_path():
    """Returns absolute path to directory containing default config files.

    :rtype:str
    """
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config')


def dao_config():
    """ Returns pydaophot module configuration singleton

    :rtype:ConfigParser
    """
    with multiprocessing.Lock():
        if __SinglethonConfig.config is None:
            parse_dao_config()
    return __SinglethonConfig.config


def parse_dao_config(files=None, parse_default_locations=True):
    """Parses pydaophot config from files and sets config singleton

    :rtype:ConfigParser
    """
    __SinglethonConfig.config = parse_config_files(files=files,
                                                   parse_default_locations=parse_default_locations,
                                                   default_filename='pydaophot.cfg')


__std_config_dirs = [
    get_package_config_path(),
    '/etc/pydaophot/',
    '~/.config/pydaophot/'
    './'
]


def parse_config_files(files=None, parse_default_locations=True, default_filename='config.cfg'):
    """Parses set of config files"""
    if files is None:
        files = []
    if parse_default_locations:
        files += [os.path.join(os.path.expanduser(d), default_filename) for d in __std_config_dirs]
    config = ConfigParser()
    read = config.read(files)
    read.reverse()
    if read:
        logger.info('Using pydaophot conf files (in priority order):\n\t{}'.format(
            '\n\t'.join(read)))
    else:
        logger.error('No configuration file found.')
    return config


def create_dao_config_file(destpath='.'):
    """Creates sample daophot config file (with default values) in destpath"""
    shutil.copy(os.path.join(get_package_config_path(), 'pydaophot.cfg'), destpath)


def find_opt_file(filename, mustexist=True):
    """Searches for opt file (e.g. daophot.opt) in working dir, configuration, default module file"""
    # 1. in local working dir
    if os.path.isfile(filename):
        return filename
    # 2. in config

    filepath = None
    try:
        filepath = dao_config().get('files', filename)
    except NoOptionError:
        # 3. default file
        filepath = os.path.join(get_package_config_path(), filename)
        if not os.path.isfile(filepath):
            logger.log('error' if mustexist else 'debug',
                       'File %s not found',
                       filename
                       )
            filepath = None
    else:
        if not os.path.isfile(filepath):
            logger.log('error' if mustexist else 'debug',
                       'File %s, specified in /files/%s entry of pydaophot.cfg, not found',
                       filepath,
                       filename
                       )
        filepath = None

    if mustexist and filepath is None:
        raise Exception('opt file not found')

    return filepath
