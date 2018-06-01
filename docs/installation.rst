.. _installation:

Installation
============

Installation through PyPI
-------------------------

Use standard pip_ installation:

.. code-block:: bash

    $ pip install astwro

.. _pip: http://pip.readthedocs.org/

This also installs `astwro.tools` command line scripts.

Dependencies
------------
Developed of `astwro` have been switched to Python 3. Most of the code still works with Python 2,
but support for  this version will be dropped.

The different submodules have different requirements, the common requirements are:

* `pandas`
* `astropy`
* `scipy`

`pydaophot` module, and tools that use it, requires the installation of modern Peter B. Stetson's `DAOPHOT` package.
However, there is no guarantee that yours version will work with `pydaophot`.

The optimization of PSF stars set using genetic algorithm (`astwro.tools.gapick.py` tool) uses `deap` GA
package and `bitarray`.


github_ Installation
--------------------
One can also install unreleased version from github_

.. _github: https://github.com/majkelx/astwro
