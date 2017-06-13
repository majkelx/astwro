# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import os.path
from .. import daophot_bialkow
from astwro.utils import tmpdir
from astwro.sampledata import fits_image, coo_file, lst_file

#@pytest.mark.skip('Long test, excluded temporary')
def test_daophot_bialkow():
    d = tmpdir()
    ipath, iname = os.path.split(fits_image())
    daophot_bialkow.daophot_photometry(iname, all_stars=coo_file(), psf_stars=lst_file(),IMGPATH=ipath, OUTPATH=d.path)
