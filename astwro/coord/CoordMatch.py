# coding=utf-8
from __future__ import absolute_import, division, print_function
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np


class CoordMatch(object):
    """Deprecated """

    def __init__(self, cooA, cooB, radius_match=0.5, radius_separated=None, unit=None):
        super(CoordMatch, self).__init__()
        if radius_separated is None:
            radius_separated = radius_match
        if not isinstance(radius_match, u.Quantity):
            radius_match = radius_match * u.arcsec
        if not isinstance(radius_separated, u.Quantity):
            radius_separated = radius_separated * u.arcsec


        self.r_match = radius_match
        self.r_spe = radius_separated

        kwargs = {} if unit is None else {'unit': unit}
        self.A = SkyCoord(cooA, **kwargs)
        self.B = SkyCoord(cooB, **kwargs)

        self._ABidx = None
        self._ABdist = None

    def _calc_diff(self):
        self._ABidx, self._ABdist, _ = self.A.match_to_catalog_sky(self.B)

    @property
    def sepAB(self):
        if self._ABdist is None:
            self._calc_diff()
        return self._ABdist

    @property
    def mapAB(self):
        if self._ABidx is None:
            self._calc_diff()
        return self._ABidx

    @property
    def lenB(self):
        return len(self.B)

    @property
    def lenA(self):
        return len(self.A)

    @property
    def mAB(self):
        return self.sepAB < self.r_match

    @property
    def mBA(self):
        r = np.zeros_like(self.B, dtype=bool)
        r[self.iBA] = True
        return r

    @property
    def mAonly(self):
        return ~self.mAB

    @property
    def mBonly(self):
        return ~self.mBA


    @property
    def iAonly(self):
        return np.arange(self.lenA)[self.mAonly]

    @property
    def iBonly(self):
        return np.arange(self.lenB)[self.mBonly]

    @property
    def iBA(self):
        return np.unique(self.mappediBA)

    @property
    def iAB(self):
        return np.arange(self.lenA)[self.mAB]

    @property
    def mappediBA(self):
        return self.mapAB[self.mAB]




