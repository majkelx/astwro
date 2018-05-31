from __future__ import absolute_import, division, print_function
__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef

try:
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError # python 2
except ImportError:
    from configparser import ConfigParser, NoOptionError, NoSectionError # python3
import os, shutil, multiprocessing, logging
from .logger import logger

class __SinglethonConfig:
    config = None


def get_astwro_inst_dir():

    thisfile = __file__
    thisdir = os.path.dirname(thisfile)
    return os.path.abspath(os.path.join(thisdir, '..'))

def get_package_inst_dir(package):
    return os.path.join(get_astwro_inst_dir(), package)

def get_package_config_path(package=None):
    """Returns absolute path to directory containing default config files of package.

    It's `config` subdirectory of specified astwro package, if ``package`` arg not specified
    main astwro `config` package is assumed (`[...]/astwr/config/config`).

    :rtype:str
    """
    if package is None:
        package = 'config'
    return os.path.join(get_package_inst_dir(package), 'config')


def get_config():
    """ Returns astwro configuration singleton

    :rtype:ConfigParser
    """
    with multiprocessing.Lock():
        if __SinglethonConfig.config is None:
            parse_config()
    return __SinglethonConfig.config


def parse_config(files=None, parse_default_locations=True):
    """Parses astwro config from files and sets config singleton

    :rtype:ConfigParser
    """
    __SinglethonConfig.config = parse_config_files(files=files,
                                                   parse_default_locations=parse_default_locations,
                                                   default_filename='astwro.cfg')


__std_config_dirs = [
    get_package_config_path(),
    '/etc/astwro/',
    '~/.config/astwro/',
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
        logger.info('Using astwro conf files (in priority order):\n\t{}'.format(
            '\n\t'.join(read)))
    else:
        logger.error('No configuration file found.')
    return config


def create_config_file(destpath='.'):
    """Creates sample daophot config file (with default values) in destpath"""
    shutil.copy(os.path.join(get_package_config_path(), 'astwro.cfg'), destpath)


def find_opt_file(filename, package=None, mustexist=True):
    """Searches for opt file (e.g. daophot.opt) in working dir, configuration, default module file"""
    # 1. in local working dir
    if os.path.isfile(filename):
        return filename
    # 2. in config

    filepath = None
    try:
        filepath = get_config().get('files', filename)
    except (NoOptionError, NoSectionError):
        # 3. default file
        filepath = os.path.join(get_package_config_path(package), filename)
        if not os.path.isfile(filepath):
            logger.log('error' if mustexist else 'debug',
                       'File %s not found',
                       filename
                       )
            filepath = None
    else:
        if not os.path.isfile(filepath):
            logger.log('error' if mustexist else 'debug',
                       'File %s, specified in /files/%s entry of astwro.cfg, not found',
                       filepath,
                       filename
                       )
        filepath = None

    if mustexist and filepath is None:
        raise Exception('opt file {} not found'.format(filename))

    return filepath
