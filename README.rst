======
astwro
======
Astrophysical routines.

:Source: https://github.com/majkelx/astwro
:Download: https://pypi.python.org/pypi/astwro

|version badge| |licence badge| |pythons badge|

.. |version badge| image:: https://img.shields.io/pypi/v/astwro.svg?maxAge=3600
   :target: https://pypi.python.org/pypi/astwro/
.. |licence badge| image:: https://img.shields.io/pypi/l/astwro.svg
    :target: https://pypi.python.org/pypi/astwro/
.. |pythons badge| image:: https://img.shields.io/pypi/l/pyversions.svg
    :target: https://pypi.python.org/pypi/astwro/

Overview
========

Set of modules developed in Astronomical Institute of Wroclaw University.
Contains wrappers for `daophot` package, star lists manipulation as `pandas` DataFrames with
export/import to `daophot` and `ds9` formats, genetic algorithm for searchin for optimal PSF stars and other.

Instalation
===========

.. code:: bash

    pip install astwro

.. note:: You must have modern DAOPHOT suite installed to use `pydaophot` module (no no no IRAF's daophot).

Modules
=======
Package contains following modules:

* `pydaophot` - wrapper for Peter Stetson's DAOPHOT photometry  suite.
* `starlist` - provides pandas objects for stars list, with import/export do daophot and ds9 formats.
* `utils` - some helpers for scripts.
* `tools` - command line (callable form python also) tools including `gapick` for finding optimal PSF-stars set using generic algorithm.

Contact
=======
For any comments or wishes plaese e-mail for the following alias: astwro.0.5@2007.gfdgfdg.com

For any issues please use github tracker: https://github.com/majkelx/astwro/issues