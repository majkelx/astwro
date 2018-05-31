"""Coordinates calculations.

This package is in early development stage nad can be deeply changed or even excluded

Actually allows image/WCS coordinates calculation using external xt2sky/sky2xy
tools from WCS tools. (which supports sextractor fits header format for distortion)
and matching multiple catalogs at once.
"""

from .coord_tools import *
from .CoordMatch import CoordMatch
from .XY2Sky import XY2Sky
from .Sky2XY import Sky2XY