from __future__ import absolute_import, division, print_function
__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef

try:
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError # python 2
except ImportError:
    from configparser import ConfigParser, NoOptionError, NoSectionError # python3

from astwro.config import *
from astwro.config.logger import logger



def find_opt_file(filename, mustexist=True):
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
        filepath = os.path.join(get_package_config_path('pydaophot'), filename)
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
        raise Exception('opt file not found')

    return filepath
