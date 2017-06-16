.. _gapick:

=========================================
gapick - Finding optimal set of PSF stars
=========================================


Overview
========

**gapick** - [g]enetic [a]lgorithm PICK (after daophot PICK), is command line and python module for
finding PSF stars set which minimizes goal function: mean of `allstar` errors for all good stars in field.
The "good stars" are those which passes filtering against magnitude (brighter than minimal threshold ``--max-ph-mag``)
and against aperture photometry error (error lower than threshold  ``--max-ph-err``).

The mineralization process is implemented as genetic algorithm, where individual is some subset of initial PSF stars
candidates.

**gapick** command line tool is automatically installed with `pip` installation of `astwro` package. Python function
interface is available as follows:

.. code:: python

    from astwro.tools import gapick
    gapick.main(arguments)

Arguments of :meth:`astwro.tools.gapick.main` corresponds to long version of command line arguments, eg command line::

  $ gapick gapick --overwite --out_dir results i.fits

is equivalent to:

.. code:: python

    from astwro.tools import gapick
    gapick.main(overwrite=True, out_dir='results', image='i.fits')

``image`` is only positional argument of commandline.


Parameters
==========
Commandline parameters help is displayed with ``--help`` option::

    $ gapick --help
    usage: gapick [-h] [--all-stars-file FILE] [--psf-stars-file FILE]
                  [--frames-av n] [--frames-sum n] [--photo-opt FILE]
                  [--photo-is r] [--photo-os r] [--photo-ap r [r ...]]
                  [--stars-to-pick n] [--faintest-to-pick MAG] [--fine]
                  [--max-psf-err-mult x] [--max-ph-err x] [--max-ph-mag m]
                  [--parallel n] [--out_dir output_dir] [--overwrite]
                  [--ga_init_prob x] [--ga_max_iter n] [--ga_pop n]
                  [--ga_cross_prob x] [--ga_mut_prob x] [--ga_mut_str x]
                  [--loglevel level] [--no_stdout] [--no_progress] [--version]
                  [image]

    Find best PSF stars using GA to minimize mean error 2nd version of PSF fit
    applied to all stars by allstar. Minimized function is the mean of allstar's
    chi value calculated on sigma-clipped (sigma=4.0) list of all stars. Results
    will be stored in --dir directory if provided. List of stars will be output to
    stdout until suppressed by -no_stdout

    positional arguments:
      image                 FITS image file (default: astwro sample image for
                            tests)

    optional arguments:
      -h, --help            show this help message and exit
      --all-stars-file FILE, -c FILE
                            all stars input file in one of daophot's formats
                            (default: obtained by daophot FIND)
      --psf-stars-file FILE, -l FILE
                            PSF candidates input file in one of daophot's formats,
                            the result of algorithm is a subset of those stars
                            (default: obtained by daophot PICK)
      --frames-av n         frames ave - parameter of daophot FIND when --all-
                            stars-file not provided (default: 1)
      --frames-sum n        frames summed - parameter of daophot FIND when --all-
                            stars-file not provided (default: 1)
      --photo-opt FILE, -O FILE
                            photo.opt file for aperture photometry (default: none)
      --photo-is r          PHOTOMETRY inner sky radius, overwrites photo.opt,
                            (default: from --photo-opt or 35)
      --photo-os r          PHOTOMETRY outher sky radius, overwrites photo.opt,
                            (default: from --photo-opt or 50)
      --photo-ap r [r ...]  PHOTOMETRY apertures radius (up to 12), overwrites
                            photo.opt, (default: from --photo-opt or 8)
      --stars-to-pick n, -P n
                            number of stars to PICK as candidates when --stars-to-
                            pick not provided (default: 100)
      --faintest-to-pick MAG
                            faintest magnitude to PICK as candidates when --stars-
                            to-pick not provided (default: 20)
      --fine, -f            fine tuned PSF calculation (3 iter) for crowded
                            fields, without this option no neighbourssubtraction
                            will be performed
      --max-psf-err-mult x  threshold for PSF errors of candidates - multipler of
                            average error; candidates with PSF error greater than
                            x*av_err will be rejected (default 3.0)
      --max-ph-err x        threshold for photometry error of stars for processing
                            by allstar; stars for which aperture photometry
                            (daophot PHOTO) error is greater than x will be
                            excluded form allstar run and have no effect on
                            quality measurment (default 0.1)
      --max-ph-mag m        threshold for photometry magnitude of stars for
                            processing by allstar; stars for which aperture
                            photometry (daophot PHOTO) magnitude is greater than m
                            (fainter than m) will be excluded form allstar run and
                            have no effect on quality measurement (default 20)
      --parallel n, -p n    how many parallel processes can be forked; n=1 avoids
                            parallelism (default: 8)
      --out_dir output_dir, -d output_dir
                            output directory; directory will be created and result
                            files will be stored there; directory should not exist
                            or --overwrite flag should be set (default: do not
                            produce output files)
      --overwrite, -o       if directory specified by --out_dir parameter exists,
                            then ALL its content WILL BE DELETED
      --ga_init_prob x, -I x
                            what portion of candidates is used to initialize GA
                            individuals; e.g. if there is 100 candidates, each of
                            them will be chosen to initialize individual genome
                            with probability x; in other words if x=0.3 first
                            population in GA will contain individuals with around
                            30 stars each; try to make size of first population
                            stars similar to expected number of resulting PDF
                            stars (default: 0.3)
      --ga_max_iter n, -i n
                            maximum number of iterations of generic algorithm -
                            generations (default: 50)
      --ga_pop n, -n n      population size of GA (default: 80)
      --ga_cross_prob x     crossover probability of GA (default: 0.5)
      --ga_mut_prob x       mutation probability of GA - probability to became a
                            mutant (default: 0.2)
      --ga_mut_str x        mutation strength of GA - probability of every bit
                            flip in mutant (default: 0.05)
      --loglevel level, -L level
                            logging level: debug, info, warning, error, critical
                            (default: info)
      --no_stdout, -t       suppress printing result (list of best choice of PSF
                            stars) to stdout at finish
      --no_progress, -b     suppress showing progress bar
      --version, -v         show version and exit


.. note::  Run ``gapick --help`` for actual set of parameters which can slightly differ from above.