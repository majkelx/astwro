# coding=utf-8
from __future__ import absolute_import, division, print_function
from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np
from os import path
from io import StringIO
from .WCSUtilsRunner import WCSUtilsRunner



class Sky2XY(WCSUtilsRunner):
    def __init__(self, translator=None):
        # base implementation of __init__ calls `_reset` also
        super(Sky2XY, self).__init__(translator=translator)
        self._update_executable('sky2xy')

    def __call__(self, coo=None, ra=None, dec=None, unit=None, translator=None):
        """
        Parameters
        ----------
        coo : SkyCoord
        ra,dec : float or array_like or Angle or Quantity
        unit : str or Unit
            default deg


        Returns
        -------
        pixel : numpy.array
        """
        if coo is not None:
            assert ra is None and dec is None and unit is None
        else:
            assert ra is not None and dec is not None
            if unit is not None and unit != 'deg' and unit != u.deg:
                coo = SkyCoord(ra, dec, unit=unit)

        if coo is not None:
            ra = coo.ra.deg
            dec = coo.dec.deg

        if translator is None:
            translator = self.translator

        assert translator is not None, 'Set fits file with WCS as "translator"'

        translator = path.abspath(translator)
        self._prepare_input_file(translator, preservefilename = True)
        ra = np.atleast_1d(ra)
        dec = np.atleast_1d(dec)
        xyfile = path.join(self.dir.path, 'radec')
        np.savetxt(xyfile, np.column_stack([ra,dec]), fmt='%12.6f')


        self.arguments = ['-jn', '3', translator, '@radec']
        self.run()
        return  np.loadtxt(StringIO(self.output), usecols=[4,5], unpack=True)
