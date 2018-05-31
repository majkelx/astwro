# coding=utf-8
"""Differential photometry as in Honeycutt 1992PASP..104..435H


See Also
--------
dphot         : function calcualting differential photometry and light curves
dphot_filters : convenience function calling dphot for multiple filters
 """
from .dphot import *
from .phot_error import err_poly_fit, PhotError

