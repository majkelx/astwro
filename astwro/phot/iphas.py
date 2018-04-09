# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type


class Simulated_ri_rHa_Colors(object):
    """
    Simulated patches on (r' - i') -> (r' - Ha') diagram

    For different reddening and spectral types. Implemented after
    G. Barentsen et al. *T Tauri candidates in IC 1396 using IPHAS*
    [2011  MNRAS 415, 103–132]

    Parameters
    ----------
    reddening : float
        E(B-V)
    """
    _table = None

    def __init__(self, reddening=0.0):
        super(Simulated_ri_rHa_Colors, self).__init__()
        self._reddening = reddening
        self._r_i = None
        self._r_Ha = None

    @property
    def reddening(self):
        return self._reddening

    @reddening.setter
    def reddening(self, value):
        if value != self._reddening:
            self._r_i = None
            self._r_Ha = None
            self._reddening = value

    @property
    def r_i(self):
        if self._r_i is None:
            t = self._get_table()
            n = int(self._reddening)
            self.r_i = t.r_i[:, :, n] + self.reddening * (t.r_i[:, :, n+1] - t.r_i[:, :, n])
        return self.r_i

    @property
    def r_Ha(self):
        if self._r_Ha is None:
            t = self._get_table()
            n = int(self._reddening)
            self._r_Ha = t.r_Ha[:, :, n] + self.reddening * (t.r_Ha[:, :, n+1] - t.r_Ha[:, :, n])
        return self._r_Ha




    @classmethod
    def _get_table(cls):
        if cls._table is None:
            import os
            import pickle
            pickelfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'iphas_simulated_paths.pkl')
            with open(pickelfile, 'rb') as f:
                cls._table = pickle.load(f)
        return cls._table
