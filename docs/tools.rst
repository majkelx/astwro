.. _tools:
===============================
astwro.tools command line tools
===============================

Astwro tools are python scripts, ready to use from command line.

Each script has ``--help`` option to display usage.

All scripts can be also used as python modules (this is the reason they have ``py`` extension).
Each script exports ``main(**kwargs)`` function which
exposes it's functionality. Also scripts exports ``info()`` function which returns usage string -- convenient
way to find out script purpose and ``main()`` parameters for ones working with python interactively.

Some of the scipts are installed in system by ``pip install astwro``:

* :mod:`gapick <astwro.tools.gapick>` see: :ref:`gapick`
* :mod:`grepfitshdr <astwro.tools.grepfitshdr>`

