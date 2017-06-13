.. _installation:

Installation
============

Installation via PyPI
---------------------

Use standard pip_ installation:

.. code-block:: bash

    $ pip install astwro

.. _pip: http://pip.readthedocs.org/

This installs also command line scripts from `astwro.tools`.

Dependencies
------------
`astwro` is developed and tested on Python 2.7. Most of the code is written with compatibility with Python 3 in mind,
so if there will be such need, porting to such version will be made.

Different submodules have different requirements, common requirements are:

* `pandas`
* `astropy`
* `scipy`

`pydaophot` module, and tools using it, requires installation of modern Peter B. Stetson's `DAOPHOT` package.
There is no guarantee however, that your's version will work with `pydaophot`.

Optimalization of PSF stars set using genetic algorithm (`astwro.tools.gapick.py` tool) uses `deap` GA
package and `bitarray`.


github_ Installation
--------------------
One can also install unreleased version from github_

.. _github: https://github.com/majkelx/astwro
