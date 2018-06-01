=========
Changelog
=========
All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

[Unreleased]
============
Added
-----
* Extended filtering `gapick`

[0.7.0] -
=======
Added
-----
* `astwro.coord` package, now with wrappers around `xy2sky` and `sky2xy` WCS tools
* `astwro.coord.coord.match_catalogues` for matching multiple stars catlogs at once
* Base classes for external tools runners moved to new `astwro.exttools` package (from `pydaophot`)
* Added `astwro.phot.PhotError` class for fitting mag/mag_error relation
* New module `astwro.sex` -- wrapper around `sextractor` ans `scamp` (early stage)
* configuration of `astwro.pydaophot` moved to  `astwro.config` -- global configuration for all subpackages
* new options in `astwro.cfg` for `sextractro` and `xy2sky` executables
* `astwro.pydaophot.PSF_GAUSSIAN` ... constants for `daophot` PSF analytical functions added
* `astwro.starlist.read_ds9_regions` now can parse sky coordinates DS9 region files
* Option for providing custom `daophot.opt` in `gapick` tool
* Support for `glob`-like files spec for `astwro.tools.grepgisthdr`
* External tools wrappers exceptions (`RunnerException` and siblings) now provides stdin/stderr/stdout
* New constructor `astwro.starlist.StarList.from_skycoord` from `astropy` `SkyCoord`
* Convenience methods `astwro.starlist.StarList` for converting image to/from sky coordinates columns
* Several test added

Changed
-------
* `astwro.starlist.StarList` method `count()` renamed to `stars_number()` because of conflict with `pandas`
* `astwro.starlist.DAO` class moved from `astwro.starlist.daofiles.py` to new `astwro.starlist.fileformats.py`
* Sample FITS file `astwro.sampledata.fits_image()` changeg to one with astrometrical solution

Fixed
-----
* Closing and linking `astwro.utils.CycleFile` properly, fixes also `gapick` tool results linking.
* `astwro.starlist.write_ds9_regions` now properly sets default region size for sky coordinates
* Fixed `astwro.starlist.write_ds9_regions` to respect `color_column` argument
* Fixed `ds9reg` command line tool
* Fixed crash of `gapick` for some sets, caused by wrong fitenesses assignment

Deprecated
----------
* Support for `Python 2.x` will be dropped. New code may not be compatible. (Test are still pased)




[0.6.0] - initial version with changelog
=======
Added
-----
* Python 3 compatible

