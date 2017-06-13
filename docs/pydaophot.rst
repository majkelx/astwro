.. _pydaophot:

================
astwro.pydaophot
================

Module `astwro.pydaophot` provides interface for Peter B. Stetson's command line tools `daophot` and `allstar`



Configuration
=============

`pydaophot.cnf` configuration file
----------------------------------
Module `astwro.pydaophot` uses configuration file `pydaophot.cfg`.

On import, pydaophot is looking for `pydaophot.cfg`
in following directories::

  /etc/pydaophot/
  ~/.config/pydaophot/
  ./

and reads found files in above order overwriting repeating parameters.

Default configuration file is included in module:
`[astwro path]/pydaophot/config/pydaophot.cfg`
which can be used as template for user's own.

Default configuration -- default `pydaophot.cfg` file content::

    # Patches (optional) and names of executables
    [executables]
    daophot = sdaophot
    allstar = sallstar

    # Location of standard config files
    [files]
    # daophot.opt =
    # allstar.opt =
    # photo.opt =

Daphot/Allstar `opt`-configuration files
----------------------------------------
Module provides various options to indicate location of following `daophot` configuration files::

  daophot.opt
  allstar.opt
  photo.opt

Routines looks up the following locations in provided order:

* parameter -- constructors if `Daophot` and `Allstar` objects and
  some routines have parameters to indicate `opt`-files location (e.g. `daophotopt`
  parameter of `Daophot` constructor). Also scripts command line parameters
  (e.g. `gapick --photo-opt`) are passed as arguments to appropriate routines.
* working directory -- if working directory of script process (not to be confused with
  `Daophot` object's working directory!) contains `opt` file, this file will be used.
* `pydaophot.cfg` -- module configuration file contain section `[files]` where
  location of `opt` files can be specified.
* default files -- if module cannot locate `opt` file in locations below, uses
  default file located in `[astwro path]/pydaophot/config`.

Note, that present order of searching means, that e.g. working directory
`daophot.opt` file have priority over one provided in `pydaophot.cfg`.

Files and directories
=====================

Paths
-----
For distinction between python program working directory and underlying `daophot`
process working directory, following naming convention is used here:

* *runner directory* is the working directory of underlying `daophot` process.
  It's directory accessible by `Runner.dir` property.
* *working directory* is current working directory of python program
  as obtained by `os.getcwd()`.

Runner directory
----------------
Each `Daophot` [#]_ object maintains it's own *runner directory*.
If directory is not specified in constructor, temporary directory is created.

.. [#] All information below applies to `Allstar` as well

Working directory is accessible by `dir` property.

Working directory of `Daophot` is set as working directory of `daophot` program.

Specifying files patch
----------------------
For all command methods (`FInd, PHotometry,`...) parameters referring to files
follows rules described below. Understanding those rules is important especially to
distinguish whether file in *runner directory* or another directory is addressed.

1 All filenames without *path* prefix, addresses files in *runner directory*.
2 Files with absolute path prefix (i.e. starting with `/`), are... absolute addressed files as expected.
3 Files with relative (but not empty) path prefix, are relative to *working directory*.
4 Files with patch prefix starting with `~` (tilde) are relative to user's home directory.

In other words, file pathnames are quite standard and reltive to script *working directory*, with exception than lack of
path prefix indicates file in *runner directory*.

During operation, all files has their representation in *runner directory*, and
underlying `daophot` processes works only on files in that directory. It's
implemented by creating symlink in *runner directory* for input files and by
copying output files from *runner directory* into destination directories for
output files.

Runner directory filenames
--------------------------
To avoid filename conflicts, link/file name in *runner directory* created for external file
consists of:

* hash of external pathname and
* original filename.

Input files
-----------
Because of limited length of directory paths maintained by `daophot` program, for all filepaths provided to 'Daophot'
object symlink in working directory is created, and this symlink is given to `daophot` as parameter.

Output files
------------
For output files, when filename contain path component, `daophot` is instructed to output into *runner directory*
file, then this file(s) are copied into path specified by the user.

Note, that in batch mode, copying occurs after execution of all commands in queue. That can have consequences when
using external file as an output to one command and input of further one. Usually everything should be OK, because
filenames generated for *runner directory* are deterministic.

In the following example

.. code:: python

    from astwro.pydaophot import Daophot
    from astwro.sampledata import fits_image

    d = Daophot(image=fits_image())
    d.mode = 'batch'
    d.FInd(starlist_file='~/my.coo')
    d.PHotometry(stars_file='~/my.coo')
    d.run()

`FInd` command instruct daophot to output into file `1b7afb3.my.coo` in  *runner directory*.
`PHotometry` command will read file `1b7afb3.my.coo` from  *runner directory*. After all `1b7afb3.my.coo` will
be copied into `~/my.coo`. But one it's easier to work on files inside *runner directory* explicitly:

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
`daophot` commands execution regime depends on the operation mode of `Daophot`
(more general any runner subleasing `Runner` class).

Operation modes
---------------
Property `Runner.mode` (type: `str`) indicates operation mode:

* `"normal"` (default) every command method (`FInd, PHotometry,`...) blocks until
  underlying `daophot` process completes processing and presents results. That's
  intuitive behaviour. Usually (see: `Runner.preserve_process`), every command
  is executed be brand new `daophot` process, which terminates after completion.

  Commands `ATtach` and `OPtions` are not available in `"normal"` mode. Instead
  use `set_image` and `set_options` methods which adds appropriate daophot
  commands for execution before every executed command.
* `"bath"` commands method doesn't trigger underlying `daophot` process. Instead,
  commands are stored in internal commands queue, and are send to `daophot` for
  execution together on explicitly called `run()` method. All commands are executed
  one by one in single `daophot` process, which terminates (until
  `Runner.preserve_process` is set) after completion of last command.

Asynchronous execution
----------------------
`"bath"` operation mode allows asynchronous execution by passing `wait=False`
into `run` method. In that case, `wait` method returns immediately after passing
commands to underlying `daophot` process. Further python program execution runs
in parallel to `daophot` process.

User can check whether `daophot` is still processing commands by testing `Runner.running` property.

Setting image and options
=========================
State of options and attached image are the parameters which persist in
`daophot` session. In `"normal"` mode each command is executed in separate
`daophot` process which terminates after command execution, thus set options and
attached image have to be set before each command execution.

`ATtach` and `OPtions` methods enqueues `AT` and `OP` commands like any other
command methods and are useless in `"normal"` mode.

`image` and `options`
---------------------
When `image` or `options` `Daophot` insurance properties are set
(explicite or by `image` and `options` attributes of constructor), appropriate
`AT` and/or `OP` commands will be automatically added for execution on the
beginning of every run. This is preferred method of setting image and options
for both modes, until multiple `ATTACH` or `OPTION` commands are needed
between other commands in `"batch"` mode.

Logging
=======
`astrwro.pydaophot` uses logger (from `logging`) named 'pydaophot' and it's child loggers.
