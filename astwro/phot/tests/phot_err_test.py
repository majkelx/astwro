# coding=utf-8
from __future__ import absolute_import, division, print_function
import pytest
from astwro.phot.phot_error import PhotError


from astwro.phot import phot_error
import numpy as np

@pytest.fixture
def mag_err():
    import os
    import pickle
    pickelfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'mag_err.npz')
    dic = np.load(pickelfile)
    return dic


def test_ph_error_tofit(mag_err):
    mag, err = mag_err['mag'], mag_err['mag_err']
    pe = PhotError(mag, err)
    print (pe.err_fitted)
    print(pe.err_means)
    print(pe.mag_means)
    assert len(pe.outlayers_mask) == len(mag)


def test_ph_error_custom_fn(mag_err):
    mag, err = mag_err['mag'], mag_err['mag_err']
    zzz = lambda x: np.percentile(x, 20) if len(x) > 0 else np.nan
    pe = PhotError(mag, err, meanfn=zzz, fitting_order=6, weighted_fit=True)
    print (pe.err_fitted)
    print(pe.err_means)
    print(pe.mag_means)
    assert len(pe.outlayers_mask) == len(mag)

