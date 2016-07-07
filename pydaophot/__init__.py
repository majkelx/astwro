from __future__ import absolute_import, division, print_function
from pydaophot.DPRunner import DPRunner, fname
from pydaophot import config

__all__ = ['DPRunner']

daophot_cfg = config.parse_config_files()

def daophot():
    return DPRunner(daophot_cfg)