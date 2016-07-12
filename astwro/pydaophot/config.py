import ConfigParser
import os, shutil

def get_package_config_path():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config')


std_config_dirs = [
    get_package_config_path(),
    '/etc/pydaophot/',
    '~/.config/pydaophot/'
    './'
]

std_config_files = [os.path.join(os.path.expanduser(d), 'pydaophot.cfg') for d in std_config_dirs]


def parse_config_files(files=None, parse_default_locations=True):
    if files is None:
        files = []
    if parse_default_locations:
        files = std_config_files + files
    config = ConfigParser.ConfigParser()
    config.read(files)
    return config


def create_config_file(filename='.'):
    """Creates sample config file (with default values)"""
    shutil.copy(os.path.join(get_package_config_path(), 'pydaophot.cfg'), filename)

