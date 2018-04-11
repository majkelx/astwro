# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from astwro.phot import stype
import numpy as np

def test_spectral_get_color_values():
    zz = stype.SpectralType({'B-V': 1.5})
    np.testing.assert_allclose(zz.get_color_values('B-V', 'BAFGKM'), [1.2, 1.49, 1.82, 2.1, 2.31, 2.97])

def test_plot_aids():
    zz = stype.SpectralType({'B-V': 1.5})
    aids = zz.generate_plot_aids('B-V')
    print (aids.fill_x)

