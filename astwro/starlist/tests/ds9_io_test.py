# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os.path as path
from io import StringIO
import astwro.starlist as sl
import astwro.sampledata as data
from astwro.utils import tmpdir


def test_read_write_ds9():
    s1 = sl.read_dao_file(data.ap_file())
    d = tmpdir()
    f2 = path.join(d.path, 'i.reg')
    sl.write_ds9_regions(s1, f2)
    s2 = sl.read_ds9_regions(f2)
    assert s2[['id', 'x', 'y']].equals(s1[['id', 'x', 'y']])
    assert not s2.auto_id.any()

def test_read_noid_reg():
    reg = u"""
# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
image
circle(869.40377,745.33678,13.888889)
circle(1225.6722,742.09608,13.888889)
circle(753.77706,465.33857,13.888889)
circle(1034.8725,499.95079,13.888889)
circle(1194.5182,211.78505,13.888889)
    """
    regstrm = StringIO(reg)
    s = sl.read_ds9_regions(regstrm)
    assert s.id[1] == 1
    assert s.x[3] == 753.77706
    assert s.auto_id.all()


def test_read_mixedid_reg():
    reg = u"""
# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
image
circle(869.40377,745.33678,13.888889)
circle(1225.6722,742.09608,13.888889)
circle(753.77706,465.33857,13.888889)  #  id=160
circle(1034.8725,499.95079,13.888889)
circle(1194.5182,211.78505,13.888889)
    """
    regstrm = StringIO(reg)
    s = sl.read_ds9_regions(regstrm)
    assert s.x[161] == 869.40377
    assert s.y[160] == 465.33857
    assert s.auto_id.any()
    assert not s.auto_id.all()


def test_read_wcs_reg():
    reg = u"""
# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5
circle(21:45:00.7278,+65:45:56.751,2.275") # color=#38ACFB text={1} id=1
circle(21:45:33.1351,+65:50:07.545,2.275") # color=#38ACFB text={7} 
circle(21:45:41.7344,+65:45:45.371,2.275") # color=#38ACFB text={8} id=8
circle(21:45:46.9471,+65:45:43.794,2.275") # color=#38ACFB text={9} id=9
    """
    regstrm = StringIO(reg)
    s = sl.read_ds9_regions(regstrm)
    assert s.ra[8] == '21:45:41.7344'
    assert s.dec[1] == '+65:45:56.751'
    assert s.auto_id.any()
    assert not s.auto_id.all()
