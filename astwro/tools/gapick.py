#! /usr/bin/env python
# coding=utf-8
""" Find best PSF stars using GA to minimize mean error.

    .. seealso:: :ref:`gapick`
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

# For now:
# TODO: --neigbours option: once for generation neightbour removal
# TODO: --timestamp: add current timestamp to directory name (+)
# TODO: conf option for
# TODO: warnings about: daophot.opt, allstar.opt
# TODO: single parameter --aperture, instead of photo.opt
# TODO: write down text based statistics from logbook.pkl
# TODO: some docs, and link to them in --help
# TODO: allstar.opt missing in result dir!
# For later, on request:
# TODO: Option for provide own PSF stars set, used for comaprision, including in candidates, put in initial population
# TODO: Checkpoints - continue calculation



import os
import logging
import random
import pickle
import time
from datetime import timedelta
from copy import deepcopy
from itertools import izip_longest

import numpy
from bitarray import bitarray
from scipy.stats import sigmaclip
from deap import base
from deap import creator
from deap import tools

import astwro.tools.__commons as commons
import astwro.starlist as sl
import astwro.pydaophot as dao
import astwro.tools
import astwro.utils as utils

_time_format = '%a %H:%M:%S'


# Definitions for genetic algorithm:
# 'individual' - subset of candidates competing with other subsets to be the best in fitness
# 'genome' - the individual's definition with subset of candidates stars, is represented by binary string
#     of length equal to number of candidate stars. '1' means that star is in subset.
# 'fitness' - minimized function on individual, mean of errors form allstar if individual's stars are
#     taken as PSF stars
# 'population' - set of all individuals in some iteration

# 2.1 Definition of routines used by algorithms: initializations, scoring
def select_stars(starlist, genome):
    # type: (sl.StarList, bitarray) -> sl.StarList
    #Select stars present in genome
    return starlist[genome.tolist()]


def random_genome(ind_class, len, prob):
    # type: (type, int, float) -> bitarray
    #Create random genome of length `len` in which probability of '1' on any position is `prob`.
    return ind_class([random.random() <= prob for _ in range(len)])


def clone_individual(individual):
    # type: (bitarray) -> bitarray
    #Make a deepcopy-clone - deepcopy genome bitarray and associated fitness
    n = deepcopy(individual)
    n.fitness = deepcopy(individual.fitness)
    return n

def calc_spectrum(pop):
    #calculates 'spectrogram' of population
    #which is a statistic of stars occurrences in population individuals
    spec = numpy.zeros(len(pop[0]))
    for ind in pop:
        spec += ind.tolist()
    return spec


def fitness_for_als(als):
    # type: (sl.StarList) -> (float,)
    #Calucalates fitness from allstar result
    return sigmaclip(als.chi)[0].mean(),  # fitness is tuple (val,)


def eval_population(population, candidates, workers, show_progress, fine_tune):
    if fine_tune:
        return eval_population_fine_psf(population, candidates, workers, show_progress)
    else:
        return eval_population_simple(population, candidates, workers, show_progress)


def eval_population_fine_psf(population, candidates, workers, show_progress):
    # type: (list(bitarray), sl.StarList, list(dict), bool) -> list
    # Evaluates fitness for all individual in population.

    # This version uses sofisticated process from daophot_bialkow
    # Uses daophots and allstars processes form `workers` running them in parallel.
    # :return: list fitnesses (1-element couples as `deap` lib likes)

    progress = None
    if show_progress:
        progress = utils.progressbar(total=len(population), step=len(workers))
        progress.print_progress(0)
    fitnesses = []
    f_max = None
    # https://docs.python.org/3/library/itertools.html#itertools-recipes grouper()
    # grouping population into chunks of size `parallel`
    for chunk in izip_longest(*([iter(population)] * len(workers))):
        active = [g is not None for g in chunk]  # all active, on errors some could be deactivated
        # PSF
        for individual, worker in zip(chunk, workers):
            if individual:
                pdf_s = select_stars(candidates, individual)
                worker['daophot'].write_starlist(pdf_s, 'i.lst')
                worker['daophot'].PSf(psf_stars='i.lst')  # add to queue only - batch mode
                worker['daophot'].run(wait=False)  # parallel start all workers without waiting
        # wait for PSF and start ALLSTAR nei
        for i, worker in enumerate(workers):
            if active[i]:
                worker['daophot'].wait_for_results()  # now wait before using results
                active[i] = worker['daophot'].PSf_result.converged  # PSF is not always successful
                if active[i]:
                    worker['allstar'].ALlstar(stars='i.nei')       # enqueue calculation
                    worker['allstar'].run(wait=False)  # asynchronous / parallel
        # second PSF
        for i, worker in enumerate(workers):
            if active[i]:
                worker['allstar'].wait_for_results()
                if worker['allstar'].ALlstars_result.success:
                    worker['daophot'].SUbstar(subtract='i.als', leave_in='i.lst')
                    worker['daophot'].run()  # quick run
                    worker['daophot'].ATtach('is')
                    worker['daophot'].PSf(photometry='i.als', psf_stars='i.lst')
                    worker['daophot'].run(wait=False)
                else:
                    active[i] = False
        # second allstar
        for i, worker in enumerate(workers):
            if active[i]:
                worker['daophot'].wait_for_results()
                if worker['daophot'].PSf_result.success:
                    worker['allstar'].ALlstar(stars='i.nei')       # enqueue calculation
                    worker['allstar'].run(wait=False)  # asynchronous / parallel
                else:
                    active[i] = False
        # third PSF
        for i, worker in enumerate(workers):
            if active[i]:
                worker['allstar'].wait_for_results()
                if worker['allstar'].ALlstars_result.success:
                    worker['daophot'].SUbstar(subtract='i.als', leave_in='i.lst')
                    worker['daophot'].run()  # quick run
                    worker['daophot'].ATtach('is')
                    worker['daophot'].PSf(photometry='i.als', psf_stars='i.lst')
                    worker['daophot'].run(wait=False)
                else:
                    active[i] = False
        # final allstar
        for i, worker in enumerate(workers):
            if active[i]:
                worker['daophot'].wait_for_results()
                if worker['daophot'].PSf_result.success:
                    worker['allstar'].ALlstar(stars='als.ap')       # enqueue calculation
                    worker['allstar'].run(wait=False)  # asynchronous / parallel
                else:
                    active[i] = False

        # wait for allstar for workers and process results
        for i, worker in enumerate(workers):
            if active[i]:
                worker['allstar'].wait_for_results()
                all_s = worker['allstar'].ALlstars_result.als_stars
                f = fitness_for_als(all_s)
                fitnesses.append(f)  # fitness is tuple (val,)
                f_max = max(f_max, f)
            else:
                fitnesses.append(None)
        # cut fitnesses if longer than population
        # (finesses mod parallel == 0, some None at the end can appear if population mod parallel != 0)
        fitnesses = fitnesses[:len(population)]
        # fill gaps in fitnesses by maximum of rest of population
        for i, f in enumerate(fitnesses):
            if f is None:
                fitnesses[i] = f_max
        if progress:
            progress.print_progress()

    return fitnesses


def eval_population_simple(population, candidates, workers, show_progress):
    # type: (list(bitarray), sl.StarList, list(dict), bool) -> list
    # Evaluates fitness for all individual in population.
    # Uses daophots and allstars processes form `workers` running them in parallel.
    # :return: list fitnesses (1-element couples as `deap` lib likes)

    progress = None
    if show_progress:
        progress = utils.progressbar(total=len(population), step=len(workers))
        progress.print_progress(0)
    fitnesses = []
    f_max = None
    # https://docs.python.org/3/library/itertools.html#itertools-recipes grouper()
    # grouping population into chunks of size `parallel`
    for chunk in izip_longest(*([iter(population)] * len(workers))):
        active = [g is not None for g in chunk]  # all active, on errors some could be deactivated
        # PSF
        for individual, worker in zip(chunk, workers):
            if individual:
                pdf_s = select_stars(candidates, individual)
                worker['daophot'].PSf(psf_stars=pdf_s)  # add to queue only - batch mode
                worker['daophot'].run(wait=False)  # parallel start all workers without waiting
        # wait for PSF and start ALLSTAR
        for i, worker in enumerate(workers):
            if active[i]:
                worker['daophot'].wait_for_results()  # now wait before using results
                active[i] = worker['daophot'].PSf_result.converged  # PSF is not always successful
                if active[i]:
                    worker['allstar'].ALlstar(stars='als.ap')       # enqueue calculation
                    worker['allstar'].run(wait=False)  # asynchronous / parallel
        # wait for allstar for workers and process results
        for i, worker in enumerate(workers):
            if active[i]:
                worker['allstar'].wait_for_results()
                all_s = worker['allstar'].ALlstars_result.als_stars
                f = fitness_for_als(all_s)
                fitnesses.append(f)  # fitness is tuple (val,)
                f_max = max(f_max, f)
            else:
                fitnesses.append(None)
        # cut fitnesses if longer than population
        # (finesses mod parallel == 0, some None at the end can appear if population mod parallel != 0)
        fitnesses = fitnesses[:len(population)]
        # fill gaps in fitnesses by maximum of rest of population
        for i, f in enumerate(fitnesses):
            if f is None:
                fitnesses[i] = f_max
        if progress:
            progress.print_progress()

    return fitnesses


def _prepare_output_dir(outdir, overwrite, srcdir, arg):
    # type: (str, bool, str, object) -> (utils.CycleFile, utils.CycleFile, utils.CycleFile, str)
    # Prepare output directory for results
    if outdir:
        from shutil import copytree, rmtree

        outdir = os.path.abspath(os.path.expanduser(outdir))
        if os.path.exists(outdir):
            if overwrite:
                rmtree(outdir)
            else:
                logging.error('--out_dir:{} already exists and no --overwrite requested.'.format(outdir))
                raise Exception('Output directory {} exists.'.format(outdir))
        copytree(srcdir, outdir)
        logging.info('Results dir created: {}'.format(outdir))
        # todo allstar.opt missing in result dir!
        basename = 'gen'
        lst_file = utils.cyclefile(outdir, basename, '.lst')
        reg_file = utils.cyclefile(outdir, basename, '.reg')
        gen_file = utils.cyclefile(outdir, basename, '.gen')
        # write down parameters
        with open(os.path.join(outdir, 'about.txt'), 'w') as f:
            print ("astwro pydaophot/tools version: {}/{}\n".format(dao.__version__, astwro.tools.__version__), file=f)
            for k, v in arg.__dict__.items():
                print ('{}\t= {}'.format(k,v), file=f)
        return lst_file, reg_file, gen_file, outdir
    else:
        return None, None, None, None

def __do(arg):
    # Main routine, common for command line, and python scripts call
    # :type arg: Namespace

    start_time = time.time()

    # Configure logging
    logging.basicConfig(format='[%(levelname)s] %(module)s: %(message)s', level=arg.loglevel.upper())
    clogger = logging.getLogger('clean logger')  # create another logger for stats without prefixes (clean)
    chandler = logging.StreamHandler()
    chandler.setFormatter(logging.Formatter('%(message)s'))
    clogger.propagate = False
    clogger.addHandler(chandler)

    # image_file
    if arg.image is None:
        from astwro.sampledata import fits_image
        arg.image = fits_image()  # sample image

        logging.warning('No image file argument provided (-h for help), using demonstration image: %s', arg.image)

    # get single daophot and ATtach file
    dp = dao.Daophot(image=arg.image)

    # all stars file
    if arg.all_stars_file is None:
        logging.warning('No all-stars-file provided, Stars will be found by daophot FIND (frames av/sum: %d/%d)', arg.frames_av, arg.frames_sum)
        find = dp.FInd(arg.frames_av, arg.frames_sum)
        logging.info('FIND found {} stars, sky estimation: {}, err/dev: {}/{}'.format(find.stars, find.sky, find.err, find.skydev))
        arg.all_stars_file = find.starlist_file

    # photometry
    if arg.photo_opt is None: # no file no problem, but recreate default radius if not provided
        if arg.photo_is == 0:
            arg.photo_is = 35
        if arg.photo_os == 0:
            arg.photo_os = 50
        if not arg.photo_ap:
            arg.photo_ap = [8]
    photometry = dp.PHotometry(photoopt=arg.photo_opt,
                               IS=arg.photo_is,
                               OS=arg.photo_os,
                               apertures=arg.photo_ap,
                               stars=arg.all_stars_file)

    # pick PFS stars candidates
    if arg.psf_stars_file is None:
        pick = dp.PIck(arg.stars_to_pick, arg.faintest_to_pick)
        arg.psf_stars_file = pick.picked_stars_file

    # psf (for errors collection)
    dp.PSf()

    # all stars (filtering by photometry errors and magnitudes)
    stars = photometry.photometry_starlist
    count0 = stars.shape[0]
    stars = stars[stars.mag < arg.max_ph_mag]
    count1 = stars.shape[0]
    stars = stars[stars.mag_err < arg.max_ph_err]
    count2 = stars.shape[0]
    logging.info('From {} stars {} left after filtering against {} magnitude threshold, '
                 'then finally {} left after {} photometry threshold'
                 .format(count0, count1, arg.max_ph_mag, count2, arg.max_ph_err))
    # for the sake of optimisation we write starlist to file to avoid multiple serialization of this list
    # (instead of more obvious providing starlist as the allstar argument)
    dp.write_starlist(stars, 'als.ap', sl.DAO.AP_FILE)

    # candidates (filter out big psf errors)
    candidates = dp.read_starlist(arg.psf_stars_file, add_psf_errors=True)
    org_cand_no = candidates.count()
    err = dp.PSf_result.errors
    averr = err.psf_err.mean()
    err = err[(err.psf_err < arg.max_psf_err_mult*averr) & (err.flag == ' ')]  # filter out big errors and * or ? marked stars
    candidates = candidates.loc[err.index]

    # candidates = candidates[candidates.psf_err < arg.max_psf_err]  # old filter, new above
    logging.info(
        "{} good candidates ({} rejected: * or ? or psf error exceeded max-psf-err-mult*averge-error = {}*{} = {})"
        .format(
        candidates.count(),
        org_cand_no - candidates.count(),
        arg.max_psf_err_mult,
        averr,
        arg.max_psf_err_mult * averr)
    )

    if candidates.count() < 15:
        logging.error("Number of candidates lass than 15. GA needs more. Sorry")

    # Prepare output directory for results
    lst_file, reg_file, gen_file, result_dir = _prepare_output_dir(arg.out_dir, arg.overwrite, str(dp.dir), arg)


    #  From all candidates find best subset, where best means minimizing mean of errors form allstar
    #       using genetic algorithm
    #  For details about setting up genetic algorithm with DEAP visit:
    #       http://deap.gel.ulaval.ca/doc/default/examples/ga_onemax.html

    creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
    creator.create("Individual", bitarray, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    # Structure initializes
    toolbox.register("individual", random_genome, creator.Individual, candidates.count(), arg.ga_init_prob)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register('clone', clone_individual)

    # The Genetic Operators

    # set min_stars to all_cand_no*ga_init_prob/2
    toolbox.register('mate', tools.cxTwoPoint)
    toolbox.register('mutate', tools.mutFlipBit, indpb=arg.ga_mut_str)
    toolbox.register('select', tools.selTournament, tournsize=3)

    # setup stats
    stats_fits = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats_star = tools.Statistics(key=sum)  # number of stars is an sum of bitarray: [001101010001] has 5 stars
    stats = tools.MultiStatistics(fitness=stats_fits, size=stats_star)
    stats.register('avg', numpy.mean)
    stats.register('std', numpy.std)
    stats.register('min', numpy.min)
    stats.register('max', numpy.max)

    # Initiate workers. Each worker has Daophot and Allstar objects sharing runner directory,
    # working in batch mode.
    workers = []
    workers_logger = logging.getLogger('worker')
    workers_logger.setLevel('ERROR')  # prevent workers flood output with logrecords
    for i in range(arg.parallel):
        d = dp.clone()       # clone previously used daophot
        d.batch_mode = True
        a = dao.Allstar(dir=d.dir, image=d.image, batch=True, options={'MA': 100})
        d.logger = workers_logger
        a.logger = workers_logger
        workers.append({'daophot': d, 'allstar': a})

    # Setup initial population, HoF and logbook and  or load it from checkpoint when continuing previous calculation
    start_gen = 0

#    if arg.checkpoint:   ## Not implemented
    if False:
        with open(os.path.expanduser(arg.checkpoint), "rb") as f:
            checkpoint = pickle.load(f)
        pop = checkpoint['population']
        start_gen = checkpoint['generation']
        hof = checkpoint['halloffame']
        logbook = checkpoint['logbook']
        logging.info('Restoring genetic algorithm on {} of {} generations'.format(start_gen, arg.ga_max_iter))
    else:
        hof = tools.HallOfFame(maxsize=10)

        logbook = tools.Logbook()
        logbook.header = 'gen', 'fitness', 'size'
        logbook.chapters['fitness'].header = 'min', 'avg', 'max', 'std'
        logbook.chapters['size'].header = 'min', 'avg', 'max'

        pop = toolbox.population(n=arg.ga_pop)
        logging.info('Starting genetic algorithm for {} generations at {}'.format(
            arg.ga_max_iter,
            time.strftime(_time_format, time.localtime())
        ))

    # Calculate fitnesses of initial population
    fitnesses = eval_population(pop, candidates, workers, show_progress=not arg.no_progress, fine_tune=arg.fine)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    record = stats.compile(pop)
    logbook.record(gen=0, spectrum=calc_spectrum(pop), **record)
    clogger.info('{}\t ETA: [... to be determined]'.format(logbook.stream))

    evolution_start_time = time.time()

    # Begin the evolution
    for g in range(start_gen + 1, arg.ga_max_iter):
        #  New Generation
        #  select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < arg.ga_cross_prob:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < arg.ga_mut_prob:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # calculate fitnesses of new individuals
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = eval_population(invalid_ind, candidates, workers, show_progress=not arg.no_progress, fine_tune=arg.fine)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        # New population from offspring
        pop[:] = offspring

        # Stats
        # hof.update(pop)  # not implemented yet, __deapcopy__ of the Individual should work first
        ETA = time.strftime(_time_format, time.localtime(evolution_start_time + (time.time() - evolution_start_time) * arg.ga_max_iter / g))
        record = stats.compile(pop)
        logbook.record(gen=g, spectrum=calc_spectrum(pop), **record)
        clogger.info('{}\t ETA: {}'.format(logbook.stream, ETA))

        # For every generation create lst file and ds9 reg file of best and point symlinks to last generation
        if result_dir:
            best_ind = tools.selBest(pop, 1)[0]
            best_stars = select_stars(candidates, best_ind)
            lst_file.next_file(g)
            reg_file.next_file(g)
            gen_file.next_file(g)
            sl.write_dao_file(best_stars, lst_file.file, sl.DAO.LST_FILE)
            sl.write_ds9_regions(best_stars, reg_file.file)
            for ind in pop:
                gen_file.file.write(ind.to01() + '\n')
            with open(os.path.join(result_dir, 'logbook.pkl'), 'wb') as f:
                pickle.dump(logbook, f)
            checkpoint = dict(population=pop, generation=g, halloffame=hof, logbook=logbook)
            with open(os.path.join(result_dir, 'checkpoint.chk'), 'wb') as f:
                pickle.dump(checkpoint, f)
        # end of evolution loop

    logging.info('Successful evolution finished at {} (elapsed time: {:s})'.format(
        time.strftime(_time_format, time.localtime()),
        timedelta(seconds=time.time() - start_time)
    ))

    best_ind = tools.selBest(pop, 1)[0]
    logging.info('Best individual is {}, {}'.format(best_ind, best_ind.fitness.values))

    best_stars = select_stars(candidates, best_ind)
    return best_stars


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description='Find best PSF stars using GA to minimize mean error 2nd version'
                    ' of PSF fit applied to all stars by allstar. Minimized function'
                    ' is the mean of allstar\'s chi value calculated on sigma-clipped '
                    ' (sigma=4.0) list of all stars. Results'
                    ' will be stored in --dir directory if provided. List of stars'
                    ' will be output to stdout until suppressed by -no_stdout')
    parser.add_argument('image', default=None, nargs='?',
                        help='FITS image file (default: astwro sample image for tests)')
    parser.add_argument('--all-stars-file', '-c', metavar='FILE', default=None,
                        help='all stars input file in one of daophot\'s formats (default: obtained by daophot FIND)')
    parser.add_argument('--psf-stars-file', '-l', metavar='FILE', default=None,
                        help='PSF candidates input file in one of daophot\'s formats, the result of algorithm is '
                             'a subset of those stars (default: obtained by daophot PICK)')
    parser.add_argument('--frames-av', metavar='n', type=int, default=1,
                        help='frames ave - parameter of daophot FIND when --all-stars-file not provided  (default: 1)')
    parser.add_argument('--frames-sum', metavar='n', type=int, default=1,
                        help='frames summed - parameter of daophot FIND when --all-stars-file not provided (default: 1)')
    parser.add_argument('--photo-opt', '-O', metavar='FILE', default=None,
                        help='photo.opt file for aperture photometry (default: none)')
    parser.add_argument('--photo-is', metavar='r', type=int, default=0,
                        help='PHOTOMETRY inner sky radius, overwrites photo.opt, (default: from --photo-opt or 35)')
    parser.add_argument('--photo-os', metavar='r', type=int, default=0,
                        help='PHOTOMETRY outher sky radius, overwrites photo.opt, (default: from --photo-opt or 50)')
    parser.add_argument('--photo-ap', metavar='r', type=int, default=[], nargs='+',
                        help='PHOTOMETRY apertures radius (up to 12), overwrites photo.opt, '
                             '(default: from --photo-opt or 8)')
    parser.add_argument('--stars-to-pick', '-P', metavar='n', type=int, default=100,
                        help='number of stars to PICK as candidates when --stars-to-pick not provided (default: 100)')
    parser.add_argument('--faintest-to-pick', metavar='MAG', type=int, default=20,
                        help='faintest magnitude to PICK as candidates when --stars-to-pick not provided (default: 20)')
    parser.add_argument('--fine', '-f', action='store_true',
                        help='fine tuned PSF calculation (3 iter) for crowded fields, without this option no neighbours'
                             'subtraction will be performed')
    parser.add_argument('--max-psf-err-mult', metavar='x', type=float, default=3.0,
                        help='threshold for PSF errors of candidates - multipler of average error; '
                             'candidates with PSF error greater than x*av_err will be rejected '
                             '(default 3.0)')
    parser.add_argument('--max-ph-err', metavar='x', type=float, default=0.1,
                        help='threshold for photometry error of stars for processing by allstar; '
                             'stars for which aperture photometry (daophot PHOTO) error is greater than x '
                             'will be excluded form allstar run and have no effect on quality measurment '
                             '(default 0.1)')
    parser.add_argument('--max-ph-mag', metavar='m', type=float, default=20,
                        help='threshold for photometry magnitude of stars for processing by allstar; '
                             'stars for which aperture photometry (daophot PHOTO) magnitude is greater than m '
                             '(fainter than m) will be excluded form allstar run and have no effect on quality '
                             'measurement (default 20)')
    parser.add_argument('--parallel', '-p', metavar='n', type=int, default=8,
                        help='how many parallel processes can be forked; '
                             'n=1 avoids parallelism (default: 8)')
    parser.add_argument('--out_dir', '-d', metavar='output_dir', type=str, default=None,
                        help='output directory; directory will be created and result files will be stored there;'
                             ' directory should not exist or --overwrite flag should be set'
                             ' (default: do not produce output files)')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='if directory specified by --out_dir parameter exists, '
                             'then ALL its content WILL BE DELETED')
    # parser.add_argument('--checkpoint', '-C', metavar='file.chk', type=str, default=None,
    #                     help='restore evaluation from checkpoint; algorithm saves checkpoint.chk file every generation,'
    #                          ' which allows resuming evolution, even with another parameters')
    parser.add_argument('--ga_init_prob', '-I', metavar='x', default=0.3, type=float,
                        help='what portion of candidates is used to initialize GA individuals;'
                             ' e.g. if there is 100 candidates, each of them will be '
                             ' chosen to initialize individual genome with probability x; '
                             ' in other words if x=0.3 first population in GA will contain'
                             ' individuals with around 30 stars each; try to make size of first population stars'
                             ' similar to expected number of resulting PDF stars (default: 0.3)')
    parser.add_argument('--ga_max_iter', '-i', metavar='n', default=50, type=int,
                        help='maximum number of iterations of generic algorithm - generations (default: 50)')
    parser.add_argument('--ga_pop', '-n', metavar='n', default=80, type=int,
                        help='population size of GA (default: 80)')
    parser.add_argument('--ga_cross_prob', metavar='x', default=0.5, type=float,
                        help='crossover probability of GA (default: 0.5)')
    parser.add_argument('--ga_mut_prob', metavar='x', default=0.2, type=float,
                        help='mutation probability of GA - probability to became a mutant (default: 0.2)')
    parser.add_argument('--ga_mut_str', metavar='x', default=0.05, type=float,
                        help='mutation strength of GA - probability of every bit flip in mutant (default: 0.05)')
    parser.add_argument('--loglevel', '-L', metavar='level', default='info',
                        help='logging level: debug, info, warning, error, critical (default: info)')
    parser.add_argument('--no_stdout', '-t', action='store_true',
                        help='suppress printing result (list of best choice of PSF stars) to stdout at finish')
    parser.add_argument('--no_progress', '-b',  action='store_true',
                        help='suppress showing progress bar')
    parser.add_argument('--version', '-v',  action='store_true',
                        help='show version and exit')

    return parser


def main(**kwargs):
    """Entry point for python script calls. Parameters identical to command line"""

    args = commons.bunch_kwargs(__arg_parser(), **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)



def info():
    """Prints commandline help message"""
    commons.info(__arg_parser())

def commandline_entry():
        # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    if __args.version:
        print ('astwro.tools '+astwro.tools.__version__)
        exit()
    __stars = __do(__args)  # call main routine - common form command line and python calls
    if __stars is None:
        return 1
    if not __args.no_stdout:
        print('\n'.join(map(str, __stars.index)))
    return 0

if __name__ == '__main__':
    code = commandline_entry()
    exit(code)