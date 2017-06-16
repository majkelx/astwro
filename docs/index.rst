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

Contains wrappers for `daophot` package, star lists manipulation as `pandas` DataFrames with
export/import to `daophot` and `ds9` formats, genetic algorithm for searching for optimal PSF stars
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
   should work with most of modern version of `daophot II`, but is not compatible with IRAF's daophot.



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contact
=======
For any comments or wishes plaese e-mail for the following alias: astwro.0.5@2007.gfdgfdg.com

For any issues please use github tracker: https://github.com/majkelx/astwro/issues
