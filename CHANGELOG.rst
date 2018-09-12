=========
Changelog
=========
All notable changes to this project will be documented in this file.

Inspired by [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

[Unreleased]
============
Added
-----
* `astwro.coord`: `box` and `central` convenience methods for finding ceneter and box boundaty of coors array
* `astwro.phot.DiffPhot`: Added possibility to set reference observation other than first one
* `astwro.coord.plot_coords`: Plotting sky charts

[0.7.2]
=======
Added
-----
* `astwro.starlist.write_ds9_regions`: accepts astropy.table.Table` as input

Changed
-------
* `astwro.pydaophot.Allstar.ALlstar`: `stars` parameter can be `StarList` without DAOType
* `astwro.starlist.write_dao_file`: parameter `with_header=None` by default. Means that header will be written if in `starlist`
* `astwro.starlist.Starlist`: `id` column/index correction when constructing from pandas or astropy `Table`
* `astwro.starlist.Starlist`: ra/dec columns detection an conversion when constructing from pandas or astropy `Table`

Fixed
-----
* `astwro.starlist.write_dao_file`: Files in DAOPHOT written in various places could have glued vaues belonging to differen column (no space)
* `astwro.pydaophot` input file type detection, for input files in daophot/allstar, improved



[0.7.1]
=======
Added
-----
* `gapick`: generation of control diagram
* `gapick`: extended filtering based on fitting err/mag relation from preliminary PSF astrometry - new options
* `gapick`: cleaned up and extend logging
* `gapick`: cleaned up `--help` output
* `astwro.phot.PhotError`: exponent fitting and other improvements
* `astwro.phot.plots`: Styles handling. General instrumentation, and specifically for `plot` and `scatter`
* `astwro.phot.DiffPhot` class added, as beginning of object interface for differential photometry routines

Changed
-------
* `astwro.phot.io`: renamed to `astwro.phot.lc_io`
* `gapick`: Minimized function is now mean of errors weighted by flux w=100^(-mag/5)
* `gapick`: by default (until `--include-psf`) PSF candidates are excluded from error evaluation
* `gapick`: options with underscore changed, e.g. `--out_dir` to `--out-dir`
* `gapick`: doesnt start without FITS file. For run on demo file, use new `--demo` option
* requrements.txt and dependencies clean up.
* `astwro.exttools.Runner`: error handling (when external tool hasn't generated expected output file) improved (a bit)

Fixed
-----
* `grepfitshdr`: Crash when using `-f` option with numeric field

[0.7.0]
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

