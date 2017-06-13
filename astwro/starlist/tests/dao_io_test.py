# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os.path as path
import astwro.starlist as sl
import astwro.sampledata as data
from astwro.utils import tmpdir


def check_starlist_daotype(s, daotype):
    assert s.DAO_type == daotype
    assert s.count() > 5
    assert s.columns[0] == 'id'
    assert (s.index == s.id).all()

def check_readwritereadqueals(f1):
    s1 = sl.read_dao_file(f1)
    d = tmpdir()
    f2 = path.join(d.path, 'tmp' + s1.DAO_type.extension)
    sl.write_dao_file(s1, f2)
    s2 = sl.read_dao_file(f2)
    assert s1.equals(s2)


def test_read_coo():
    s = sl.read_dao_file(data.coo_file())
    check_starlist_daotype(s, sl.DAO.COO_FILE)

def test_read_lst():
    s = sl.read_dao_file(data.lst_file())
    check_starlist_daotype(s, sl.DAO.LST_FILE)

def test_read_nei():
    s = sl.read_dao_file(data.nei_file())
    check_starlist_daotype(s, sl.DAO.NEI_FILE)

def test_read_ap():
    s = sl.read_dao_file(data.ap_file())
    check_starlist_daotype(s, sl.DAO.AP_FILE)

def test_read_als():
    s = sl.read_dao_file(data.als_file())
    check_starlist_daotype(s, sl.DAO.ALS_FILE)



def test_write_coo():
    check_readwritereadqueals(data.coo_file())

def test_write_lst():
    check_readwritereadqueals(data.lst_file())

def test_write_nei():
    check_readwritereadqueals(data.nei_file())

def test_write_ap():
    check_readwritereadqueals(data.ap_file())

def test_write_als():
    check_readwritereadqueals(data.als_file())

def test_convert_ap_to_als():
    s1 = sl.read_dao_file(data.als_file())
    d = tmpdir()
    f2 = path.join(d.path, 'tmp' + '.als')
    sl.write_dao_file(s1, f2, sl.DAO.ALS_FILE)
    s2 = sl.read_dao_file(f2)
    cols_to_compare = ['id', 'x', 'y', 'mag', 'sky']
    assert s1.round(4)[cols_to_compare].equals(s2.round(4)[cols_to_compare])


