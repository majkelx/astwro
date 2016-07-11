===============================================
ASTWRO 
===============================================


Instalation
===========
As long there is no release instaled via ``pip``, clone or download project, e.g.

.. code:: bash

    git clone https://github.com/majkelx/astwro.git
    
To have module accesible in your code, either:

- Put the ``astwro`` folder in the same folder as your script.
- Put the ``astwro`` folder in the standard location for modules so it is available to all scripts
   - /Library/Python/2.6/site-packages/ (Mac OS X),
   - /usr/lib/python2.6/site-packages/ (Unix).
- Add the location of the module partent dir to sys.path in your script, before importing it. E.g. if ``astwro`` 
is in ``/users/majkelx/projects/astwro``:
.. code:: python

    astwro_path = '/users/majkelx/projects'
    import sys
    if astwro_path not in sys.path: sys.path.append(astwro_path)
    from astwro.pydaophot import *
    
.. note:: You must have DAOPHOT suite installed, to use pydaophot module.

pydaophot
=========
*pydaophot* is a python module wraper around  Peter Stetson's DAOPHOT photometry  suite. 

Configuration
-------------
*pydaophot* uses configuration files and dict to obtain various settings. Currently [path/]name of DAOPHOT
executables ``daophot`` and ``allstar`` can be configured.

Example ``pydaophot.cfg`` config file:
.. code::

    [executables]
    daophot = ~/bin/daophot/sdaophot
    allstar = ~/bin/daophot/sallstar

pydaophot searches for configuration file ``pydaophot.cfg`` in following directories:

- ``/etc/pydaophot/``
- ``~/.config/pydaophot/``
- ``./``

Alternatively, one can provide those settings directly from code as follows:

.. code:: python

    from astwro.pydaophot import daophot_cfg
    daophot_cfg.set('executables', 'daophot', '/usr/local/bin/daophot')


