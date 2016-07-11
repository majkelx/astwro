from __future__ import absolute_import, division, print_function
from pydaophot.DPRunner import DPRunner
from pydaophot.ASRunner import ASRunner
from pydaophot.DAORunner import fname
from pydaophot import config

__all__ = ['allstar', 'daophot', 'fname']

daophot_cfg = config.parse_config_files()

def daophot(dir=None, daophotopt=None, photoopt=None):
    return DPRunner(daophot_cfg, dir=dir, daophotopt=daophotopt, photoopt=photoopt)

def allstar( dir=None,
             allstaropt=None,
             image_file=None,
             psf_file=None,
             photometry_file=None,
             create_subtracted_image=False):
    return ASRunner(daophot_cfg, dir, allstaropt, image_file, psf_file, photometry_file, create_subtracted_image)