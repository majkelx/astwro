# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from astwro.phot import *


def prepare_testset():
    s = np.ma.masked_array([12.0, 12.6, 13.0, 13.2, 14.1]).reshape(5, 1)  # 5 stars magnitudes
    o = np.ma.masked_array([1.0, 1.08, 0.9, 1.3]).reshape(1, 4)  # 4 observations deviations
    x = s.dot(o) + np.random.normal(scale=0.1, size=[5, 4])  # 5x4 noisy observations simulated
    return s, o, x


def prepare_testset_masked():
    X = 0.0
    d = np.array([
        [ 11.5,   X,   12.5,   X  ],
        [ 10.0,   X,   11.0,  9.0 ],  # comp
        [ 11.0,   X,     X , 10.0 ],  # comp
        [   X ,   X,     X ,   X  ],
        [   X ,   X,     X ,   X  ],  # comp (bad)
        [ 12.0,   X,   13.0, 11.0 ],
    ])
    e = d * 0.01
    d = np.ma.masked_equal(d, X)
    e = np.ma.masked_equal(e, X)
    d += np.random.normal(scale=0.1, size=d.shape)

    c = [False, True, True, False, True, False]
    return d, e, c

def prepare_testset_real():
    import os
    import pickle
    pickelfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'some_stars_data.pkl')
    with open(pickelfile, 'rb') as f:
        d, e, c = pickle.load(f)
    return d, e, c

def test_masked():
    d, e, c = prepare_testset_masked()
    o, s, l, oe, se, le = dphot(d, e, c)
    pass

def test_real():
    d, e, f = prepare_testset_real()
    o, s, l, oe, se, le = dphot_filters(d, e, f)
    pass
