# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os.path as path
from io import StringIO
from astropy.table import Table
import astwro.starlist as sl
import astwro.sampledata as data
from astwro.utils import tmpdir

def test_read_VOT_via_astropy():
    file = path.join(path.abspath(path.dirname(__file__)), 'NGC7142.vot')
    t_astropy = Table.read(file)
    t_starlist = sl.StarList.from_table(t_astropy)




