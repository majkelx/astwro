.. _pydaophot:

================
astwro.pydaophot
================

The :mod:`astwro.pydaophot` module provides an interface to the command line tools of Peter B. Stetson `daophot` and `allstar`


Daphot/Allstar `opt`-configuration files
========================================
The module provides various options to indicate the location of following `daophot` configuration files::

  daophot.opt
  allstar.opt
  photo.opt

Routines searches the following locations in the order provided:

* parameter -- constructors of :class:`~astwro.pydaophot.Daophot` and :class:`~astwro.pydaophot.Allstar` objects and
  some routines, have parameters to indicate the location of `opt`-files (e.g. the `daophotopt`
  parameter of the :class:`~astwro.pydaophot.Daophot` constructor). Also script's command line parameters
  (e.g. ``gapick --photo-opt``) are passed as arguments to appropriate routines.
* working directory -- if working directory of script process (not to be confused with
  :class:`~astwro.pydaophot.Daophot` object's working directory - *runner directory*!) contains `opt` file, this file will
  be used.
* `astwro.cfg` -- the astwro configuration files contains section `[files]` where
  location of the `opt` files can be specified.
* default files -- if module cannot locate `opt` file in locations below, uses the
  default file located in `[astwro path]/pydaophot/config`.

Note, that the presented order of searching means, that e.g. the working directory
`daophot.opt` file have priority over another one provided in  `astwro.cfg`.

Files and directories
=====================

Paths
-----
To distinguish between the working directory of the python program and the working directory
of the underlying `daophot` process,  the following naming convention is used:

* *runner directory* is the working directory of the underlying `daophot` process.
  This directory accessible by the :meth:`Daophot[Allstar].dir.path <astwro.pydaophot.Daophot.dir>` property.
* *working directory* is current working directory of python program
  as obtained by :func:`os.getcwd()`.

Runner directory
----------------
Each :class:`~astwro.pydaophot.Daophot` [#]_ object maintains it's own *runner directory*.
 If directory is not specified in constructor, the temporary directory is created.

.. [#] All information below applies to :class:`~astwro.pydaophot.Allstar` as well

The *runner directory* is accessible by the :meth:`Daophot[Allstar].dir.path <astwro.pydaophot.Daophot.dir>`  property.

:class:`~astwro.pydaophot.Daophot`'s *runner directory* is the working directory of `daophot` program.

Specifying the file patch
-------------------------
For all command methods (:meth:`~astwro.pydaophot.Daophot.FInd`, :meth:`~astwro.pydaophot.Daophot.PHotometry`, ...)
parameters that refer to files
follow the rules described below. Understanding those rules is especially important  to
distinguish whether the file in *runner directory* or another directory is addressed.

1. All filenames without *path* prefix, addresses the *runner directory* files.
2. Files with absolute path prefix (that is, starting with `/`), are... absolute addressed files as expected.
3. Files with relative (but not empty) path prefix, are relative to *working directory*.
4. Files with patch prefix starting with `~` (tilde) are relative to the user's home directory.

In other words, file pathnames are fairly standard and reltive to script *working directory*, with exception than lack of
path prefix indicates file in *runner directory*.

During operation, all files has representation in *runner directory*, and
underlying `daophot` processes only works on the files in that directory. It's
implemented by creating symbolic link  in *runner directory* for the input files and
copying the output files from *runner directory* into destination directories if such external output file is requested.


Runner directory file names
---------------------------
To avoid filename conflicts, the name of link/file in the *runner directory* created for external file
consists of:

* hash of absolute pathname and
* original filename.

Input files
-----------
Due to the  limited length of directory paths maintained by the `daophot` program, for all filepaths provided to
:class:`~astwro.pydaophot.Daophot`
object, the symbolic link is created in *runner directory*, and this link is given to the `daophot` process instead
of the original filename. Existing symbolic links of the same name are overwritten (because name is generated
from absolute patch it's not a problem at all).

Output files
------------
For output files, when the filename contains path component, `daophot` is instructed to output into the
*runner directory*
file, then, after `daophot` terminates, this file(s) are copied to the path specified by the user.

.. Warning::
    The output files, existing in *runner directory*, are deleted on queuing command. This can lead to unexpected
    behaviour in ``"batch"`` mode, when mixing input/output files. Consider following example:

.. code:: python

    d.mode = 'batch'
    d.GRoup(psf_file='i.psf')  # preexisting i.psf (input)
    d.PSf(psf_file='i.psf')    # deletes i.psf  (output)
    d.run()                    # GROUP will miss i.psf and fail

.. Note::
    In the batch mode, the copying occurs after execution of all commands in queue. This can have consequences when
    using the external file as an output of one command and input of further one. Usually everything should be fine,
    since the filenames generated for *runner directory* are deterministic as described above.

In the following example

.. code:: python

    from astwro.pydaophot import Daophot
    from astwro.sampledata import fits_image

    d = Daophot(image=fits_image())
    d.mode = 'batch'
    d.FInd(starlist_file='~/my.coo')
    d.PHotometry(stars_file='~/my.coo')
    d.run()

:meth:`~astwro.pydaophot.Daophot.FInd` command instruct daophot to output into file `1b7afb3.my.coo` in  *runner directory*.
:meth:`~astwro.pydaophot.Daophot.PHotometry` command will read file `1b7afb3.my.coo` from  *runner directory*.
After all `1b7afb3.my.coo` will
be copied to `~/my.coo`. Sometimes it's easier to work explicitly on the files inside the *runner directory* :

.. code:: python

    from astwro.pydaophot import Daophot
    from astwro.sampledata import fits_image

    d = Daophot(image=fits_image(), batch=True)
    d.FInd()        # equiv: d.FInd(starlist_file='i.coo')
    d.PHotometry()  # equiv: d.PHotometry(starlist_file='i.coo')
    d.run()
    d.copy_from_runner_dir('i.coo', '~/my.coo')

User can also get patch to this file without copying

.. code:: python

    d.file_from_runner_dir('i.coo')

or, without specifying names at all

.. code:: python

    d.FInd_result.starlist_file



Operation modes - batch and parallel execution
==============================================
The  execution regime of `daophot` commands depends on :class:`~astwro.pydaophot.Daophot`'s operation mode
(this applies to any runner subclassing the :class:`~astwro.pydaophot.Runner` class).

Operation modes
---------------
Property :meth:`Daophot.mode <astwro.pydaophot.Daophot.mode>` (type: `str`) indicates operation mode:

* ``"normal"`` (default) -  Every command method
  (:meth:`~astwro.pydaophot.Daophot.FInd`, :meth:`~astwro.pydaophot.Daophot.PHotometry`, ...) blocks until
  the underlying `daophot` process completes processing. That is
  intuitive behaviour. Every command
  is executed by brand new `daophot` process, which terminates once the command execution is finished.

  The :meth:`~astwro.pydaophot.Daophot.ATtach` and :meth:`~astwro.pydaophot.Daophot.OPtions` commands
  are not available in ``"normal"`` mode. Instead
  use :meth:`~astwro.pydaophot.Daophot.set_image` and :meth:`~astwro.pydaophot.Daophot.set_options` methods
  that enqueue the appropriate `daophot`
  commands for execution before any other command.
* ``"bath"`` - The command methods does not  trigger the underlying `daophot` process. Instead,
  commands are stored in the internal commands queue and are send to `daophot` for
  execution together on explicitly called :meth:`~astwro.pydaophot.Daophot.run()` method. All commands are executed
  one by one in a single `daophot` process, which terminates after completion of the last command.

Asynchronous execution
----------------------
The ``"bath"`` operation mode allows asynchronous execution by passing ``wait=False``
to the :meth:`run(wait=False) <astwro.pydaophot.Daophot.run>` method.
In that case, the :meth:`~astwro.pydaophot.Daophot.run()` method returns immediately after passing
the commands to the underlying `daophot` process. Further execution of the Python program runs in parallel
to the `daophot` process.

The user can check if `daophot` is still processing commands by testing the
:meth:`Daophot.running <astwro.pydaophot.Daophot.running>` property.

Setting image and options
=========================
The `daophot options and the attached image are the parameters that persist in
`daophot` session. In ``"normal"`` mode each command is executed in a separate
`daophot` process which terminates after execution of the command, so the configuration options and the
attached image must be set before each command execution.

The :meth:`~astwro.pydaophot.Daophot.ATtach` and :meth:`~astwro.pydaophot.Daophot.OPtions` methods
enqueues `ATTACH` and `OPTION` commands like any other
command methods and are useless in `"normal"`.
The :meth:`~astwro.pydaophot.Daophot.set_image` and :meth:`~astwro.pydaophot.Daophot.set_options` methods
should be used instead, which enqueue the appropriate `daophot`
commands for execution before every command.


Logging
=======
The :mod:`astwro.pydaophot` uses the logger (from the :py:mod:`logging`
module) named ``"pydaophot"`` and it's child loggers.
