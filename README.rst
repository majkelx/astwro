======
ASTWRO 
======


Instalation
===========
As long there is no release instaled via ``pip``, clone or download project, e.g.

.. code:: bash

    git clone https://github.com/majkelx/astwro.git
    
To have module accessible in your code, either:

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
*pydaophot* is a python module wrapper around  Peter Stetson's DAOPHOT photometry  suite.

Goal
----
To provide python interface to DAOPHOT suite which:

- is easy to use
- has convenient way to access daophot/allstar output data
- allows parallel execution of daophot/allstar

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

Example
-------
.. code:: python

    from astwro.pydaophot import daophot, allstar, fname

    # create single instance of daophot runner. This istance will create
    # temporary working directory. Without specifying daophotopt, and
    # photoopt parameters, default files, from astwro/pydaophot/config, will be used
    d = daophot()

    # add commands to execute (not executed yet)
    d.ATtach('NGC6871.fits')
    d.FInd(1, 1)
    d.PHotometry()
    d.PIck()

    # clone daophot instance to setup different parameters for PSF
    # each intance gets another option of PSF RADIUS
    psf_radius = [14,16,18,20,22,24]
    dphots = [d.clone() for _ in psf_radius]

    # dphots contains list of daophot runner instances: ``DPRunner`` identical to d
    # add OP and PS commands to execution stack
    for dp, ps in zip(dphots, psf_radius):
        dp.OPtion('PSF', ps)
        dp.PSf()

    # Run all six daophots in parallel
    for dp in dphots:
        dp.run(wait=False)

    # print result chi values. Each command has own results object e.g. PSf_result
    # which gives access to all command output data
    for dp in dphots:
        print "PSF radius = {} gives chi = {}".format(dp.OPtion_result.get_option('PSF'), dp.PSf_result.chi)

    # now prepare allstar runners, one for each daophot. By providing ``dir`` parameter, allstars will use
    # daophot's working dirs.
    allstars = [allstar(dp.dir, create_subtracted_image=True) for dp in dphots]

    # run all allstars at once
    for als in allstars:
        als.run(wait=False)

    # copy subtracted images to current dir with names corresponding to PSF RADIUS parameter
    for als, ps in zip(allstars, psf_radius):
        als.wait_for_results()  # file operations doesnt wait for completion (as ..._result.get_XXX do)
        als.copy_from_working_dir(fname.SUBTRACTED_IMAGE_FILE, "i-psf-{}.sub.fits".format(ps))

    # current directory should contain 6 subtracted images as a result
    # close al created runners (destructor of these objects closes them as well), this discards
    # all temporary working directories
    d.close()
    for runner in daophots + allstars:
        runner.close()



