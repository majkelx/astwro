# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os.path as path
import astwro.starlist as sl
import astwro.sampledata as data
from astwro.utils import tmpdir


def test_read_write_ds9():
    s1 = sl.read_dao_file(data.ap_file())
    d = tmpdir()
    f2 = path.join(d.path, 'i.reg')
    sl.write_ds9_regions(s1, f2)
    s2 = sl.read_ds9_regions(f2)
    assert s2.equals(s1[['id', 'x', 'y']])
