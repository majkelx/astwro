# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from astwro.utils import make_fits_table
from astwro.sampledata import sampledata_dir


def test_fits_list():
    t = make_fits_table(directory=sampledata_dir(), fields=['FILTER', 'EXPTIME', 'OBJECT'], stats=True)
    #t = make_fits_table(directory='/Users/mka/szkola/PhD/iris12bin/input/TZ_For_ND/', fields=['FILTER', 'EXPTIME', 'OBJECT'], stats=True)
    assert (len(t) > 0)
