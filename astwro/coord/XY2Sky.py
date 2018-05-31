# coding=utf-8
from __future__ import absolute_import, division, print_function
from astropy.coordinates import SkyCoord
import numpy as np
from os import path
from io import StringIO
from .WCSUtilsRunner import WCSUtilsRunner



class XY2Sky(WCSUtilsRunner):
    def __init__(self, translator=None):
        # base implementation of __init__ calls `_reset` also
        super(XY2Sky, self).__init__(translator=translator)
        self._update_executable('xy2sky')

    def __call__(self, x, y, translator=None):
        """
        Parameters
        ----------
        x,y : float or array_like

        Returns
        -------
        SkyCoord object
        """
        if translator is None:
            translator = self.translator

        assert translator is not None, 'Set fits file with WCS as "translator"'

        translator = path.abspath(translator)
        self._prepare_input_file(translator, preservefilename = True)
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        xyfile = path.join(self.dir.path, 'xy')
        np.savetxt(xyfile, np.column_stack([x,y]), fmt='%12.6f')


        self.arguments = ['-dn', '6', translator, '@xy']
        self.run()
        ra,dec = np.loadtxt(StringIO(self.output), usecols=[0,1], unpack=True)
        return  SkyCoord(ra,dec, unit='deg')
