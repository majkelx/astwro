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
`astwro` is developed and tested on Python 2.7. Most of the code is written with Python 3 compatibility in mind,
so if there will be such need, the port to that version will be made.

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
