# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from .. import daophot_bialkow
from astwro.utils import tmpdir
from astwro.sampledata import fits_image, coo_file, lst_file

@pytest.mark.skipif("not config.getvalue('long')")
def test_daophot_bialkow():
    d = tmpdir()
    daophot_bialkow.daophot_photometry(fits_image(), all_stars=coo_file(), psf_stars=lst_file(), OUTPATH=d.path)
