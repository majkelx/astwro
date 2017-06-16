# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os.path as path
from astwro.tools.gapick import main
from astwro.utils.TmpDir import TmpDir
from astwro.starlist import read_dao_file, read_ds9_regions

def test_gapick_short():
    d = TmpDir()
    r = main(
        ga_max_iter = 2, # just two iteration of GA
        ga_pop = 15,  # small population
        overwrite = True,
        out_dir = d.path,
        fine = True,
    )
    assert (r.count() > 10)

    ap = read_dao_file(path.join(d.path, 'i.ap'))
    lst = read_dao_file(path.join(d.path, 'gen_last.lst'))
    coo = read_dao_file(path.join(d.path, 'i.coo'))
    nei = read_dao_file(path.join(d.path, 'i.nei'))
    reg = read_ds9_regions(path.join(d.path, 'gen_last.reg'))

