:Documentation: http://astwro.readthedocs.io/
:Source: https://github.com/majkelx/astwro
:Download: https://pypi.python.org/pypi/astwro

|version badge| |licence badge| |pythons badge|

.. |version badge| image:: https://img.shields.io/pypi/v/astwro.svg?maxAge=3600
   :target: https://pypi.python.org/pypi/astwro/
.. |licence badge| image:: https://img.shields.io/pypi/l/astwro.svg
    :target: https://pypi.python.org/pypi/astwro/
.. |pythons badge| image:: https://img.shields.io/pypi/pyversions/astwro.svg
    :target: https://pypi.python.org/pypi/astwro/

Welcome to astwro |release| documentation!
==========================================

**astwro** is the set of modules developed in Astronomical Institute of Wroclaw University.

It contains wrappers for `daophot` package, star lists (as `pandas` DataFrames) manipulation routines  with
export/import to `daophot` and `ds9` formats, genetic algorithm for the search for optimal PSF stars
and some other stuff.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   pydaophot
   gapick
   tools

.. toctree::
   :maxdepth: 1
   :caption: pydaophot example in ipython notebook:

   notebooks/deriving_psf_stenson


API Reference
=============

.. toctree::
   :maxdepth: 2

   api/modules

.. warning::

   `astwro.pydaophot` and many command line tools requires compatible `DAOPHOT` package installed. `pydaophot`
   should work with most of modern versions of `daophot II`, but is not compatible with IRAF's daophot.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contact
=======
For any comments or wishes please  send an email  to the following alias: astwro.0.5@2007.gfdgfdg.com

For any issues, use github tracker: https://github.com/majkelx/astwro/issues
