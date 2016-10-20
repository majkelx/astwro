#! /usr/bin/env python
# coding=utf-8
""" Find best PSF stars using GA to minimize mean error
"""
from __future__ import print_function, division
import random
import sys
import os
import time
import numpy
import pickle
from copy import deepcopy
from itertools import izip_longest

from bitarray import bitarray
from scipy.stats import sigmaclip

from deap import base
from deap import creator
from deap import tools

from astwro.pydaophot import daophot
from astwro.pydaophot import fname
from astwro.pydaophot import allstar
from astwro.starlist import read_dao_file
from astwro.starlist import write_dao_file
from astwro.starlist import write_ds9_regions
from astwro.starlist import DAO
from astwro.utils import cyclefile
from astwro.utils import progressbar
import __commons as commons


def __do(arg):
    """Main routine, common for command line, and python scripts call"""

    if arg.silent:
        def print_info(msg):
            pass
    else:
        def print_info(msg):
            print(msg, file=sys.stderr)

    # 1. At first we need all stars and pdf stars candidates
    # ------------

    # 1.1 do daophot aperture and psf photometry and FIND/PICK if needed

    if arg.image_file is None:
        from astwro.sampledata import fits_image

        arg.image_file = fits_image()  # sample image
    dp = daophot(image_file=arg.image_file)

    if arg.coo_file is None:
        dp.FInd(arg.frames_av, arg.frames_sum)
    else:
        dp.copy_to_working_dir(arg.coo_file, fname.COO_FILE)

    dp.PHotometry()

    if arg.lst_file is None:
        dp.PIck(arg.stars_to_pick)
    else:
        dp.copy_to_working_dir(arg.lst_file, fname.LST_FILE)

    dp.PSf()
    dp.run(wait=True)

    # 1.2 dp.dir should contain picked stars in LST file, read it, end reject stars with psf error above threshold

    candidates = dp.get_stars(fname.LST_FILE, add_psf_errors=True)
    all_cand_no = candidates.count()
    candidates = candidates[candidates.psf_err < arg.max_psf_err]

    print_info("{} good candidates "
               "({} rejected because psf error exceeded threshold of {})".format(
        candidates.count(),
        all_cand_no - candidates.count(),
        arg.max_psf_err))

    # 2. From picked candidates find best subset, where best means minimizing mean of errors form allstar
    # ------------
    # 'genome' - the individual's definition with subset of candidates stars, is represented by binary string
    # of length equal to number of candidate stars. '1' means that star is in subset.
    # such representation is also classic one for genetic algorithms.
    all_cand_no = candidates.count()

    # 2.1 Definition of routines used by algorithms: initializations, scoring

    def select_stars(starlist, genome):
        """
        Utility function to select stars according to genome
        :param StarList starlist:
        :param genome:
        :rtype: StarList
        """
        best_stars_idx = []
        for i, val in enumerate(genome):
            if val:
                best_stars_idx.append(i)
        return starlist.iloc[best_stars_idx]

    def pick_random_genome(ind_class, len, prob):
        """
        Create random genome of length `len` in which probability of '1' on any position
        is given by `prob`.
        """
        gen = ind_class(len)
        for i, _ in enumerate(gen):
            gen[i] = random.random() <= prob
        return gen

    def clone_indiv(individual):
        """Make a deepcopy-clone"""
        n = deepcopy(individual)
        n.fitness = deepcopy(individual.fitness)
        return n

    def calc_spectrum(pop):
        """calculates 'spectrogram' of population
        which is a statistic of stars occurrences in population individuals """
        spec = numpy.zeros(len(pop[0]))
        for ind in pop:
            spec += ind.tolist()
        return spec

    # create pool of workers TODO do not use global
    pool = []
    for i in range(arg.parallel):
        d = daophot(arg.image_file)  # TODO other params
        a = allstar(d.dir)
        d.copy_to_working_dir(dp.file_from_working_dir(fname.AP_FILE), fname.AP_FILE)
        pool.append({'daophot': d, 'allstar': a})

    def eval_population(population, show_progress):
        """
        Evaluates fitness for all individual in population.
        Use of one function for population (rather than for individuals)
        to implement parallel execution in workers pool.
        :param list population:
        :return: list fitnesses (1-element couples as deap likes)
        """
        if show_progress:
            progress = progressbar(total=len(population), step=arg.parallel)
            progress.print_progress(0)
        fitnesses = []
        f_max = 0.0
        # https://docs.python.org/3/library/itertools.html#itertools-recipes grouper()
        # grouping population into chunks of size `parallel`
        for chunk in izip_longest(*([iter(population)] * arg.parallel)):
            # start daophot PSF workers
            for individual, worker in zip(chunk, pool):
                if individual:
                    pdf_s = select_stars(candidates, individual)
                    write_dao_file(pdf_s, worker['daophot'].file_from_working_dir(fname.LST_FILE))
                    worker['daophot'].PSf()
                    worker['daophot'].run(wait=False)  # parallel
            # wait for PSF and start allstar for workers
            for individual, worker in zip(chunk, pool):
                if individual:
                    worker['daophot'].wait_for_results()
                    if worker['daophot'].PSf_result.converged:  # PSF is not always successful
                        worker['allstar'].run(wait=False)  # parallel
            # wait for allstar for workers and process results
            for individual, worker in zip(chunk, pool):
                if individual:
                    if worker['daophot'].PSf_result.converged:
                        worker['allstar'].wait_for_results()
                        all_s = read_dao_file(worker['allstar'].file_from_working_dir(fname.ALS_FILE))
                        f = sigmaclip(all_s.psf_chi)[0].mean()
                        fitnesses.append((f,))
                        if f > f_max: #  collect max
                            f_max = f
                    else:
                        fitnesses.append((0.0,)) # temporary 0.0
            # flatten fitnesses: make all 0.0 maximum of rest of population
            # this make those individuals bad, but do not affect statistics too much
            for i, f in enumerate(fitnesses):
                if f[0] == 0.0:
                    fitnesses[i] = (f_max,)
            if show_progress:
                progress.print_progress()
        return fitnesses

    # 2.2 Prepare output directory
    if arg.out_dir:
        from shutil import copytree, rmtree

        arg.out_dir = os.path.abspath(os.path.expanduser(arg.out_dir))
        if os.path.exists(arg.out_dir) and arg.overwrite:
            rmtree(arg.out_dir)
        copytree(str(dp.dir), arg.out_dir)
        # todo allstar.opt missing!
        path = arg.out_dir
        basename = 'gen'
        lst_file = cyclefile(path, basename, '.lst')
        reg_file = cyclefile(path, basename, '.reg')
        gen_file = cyclefile(path, basename, '.gen')

    # 2.3

    #  For details about setting up genetic algorithm with DEAP visit:
    #       http://deap.gel.ulaval.ca/doc/default/examples/ga_onemax.html

    creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
    creator.create("Individual", bitarray, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    # Structure initializes
    toolbox.register("individual", pick_random_genome, creator.Individual, all_cand_no, arg.ga_init_prob)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register('clone', clone_indiv)

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

    logbook = tools.Logbook()
    logbook.header = 'gen', 'fitness', 'size'
    logbook.chapters['fitness'].header = 'min', 'avg', 'max', 'std'
    logbook.chapters['size'].header = 'min', 'avg', 'max'

    pop = toolbox.population(n=arg.ga_pop)

    # Evaluate the entire population
    print_info('-- Initial Generation 0 of {} --'.format(arg.ga_max_iter))
    fitnesses = eval_population(pop, show_progress=not arg.no_progress)

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    record = stats.compile(pop)
    logbook.record(gen=0, spectrum=calc_spectrum(pop), **record)
    print_info (str(logbook.stream))

    start = time.time()
    # Begin the evolution
    for g in range(1, arg.ga_max_iter):
        # Select the next generation individuals
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
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = eval_population(invalid_ind, show_progress=not arg.no_progress)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        # New population from offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        ETA = time.asctime(time.localtime(start + (time.time() - start) * arg.ga_max_iter / g))
        record = stats.compile(pop)
        logbook.record(gen=g, spectrum=calc_spectrum(pop), **record)
        print_info(str(logbook.stream) + 'ETA: {}'.format(ETA))

        # for every generation create lst file and ds9 reg file of best and point symlinks to last generation
        if arg.out_dir:
            best_ind = tools.selBest(pop, 1)[0]
            best_stars = select_stars(candidates, best_ind)
            lst_file.next_file(g)
            reg_file.next_file(g)
            gen_file.next_file(g)
            write_dao_file(best_stars, lst_file.file, DAO.LST_FILE)
            write_ds9_regions(best_stars, reg_file.file)
            # sort_pop = sorted(pop, key=lambda x: x.fitness, reverse=True)
            for ind in pop:
                gen_file.file.write(ind.to01() + '\n')
            with open(os.path.join(arg.out_dir, 'logbook.pkl'), 'w') as f:
                pickle.dump(logbook, f)

    # 3. Winner?

    print_info('-- End of (successful) evolution')

    best_ind = tools.selBest(pop, 1)[0]
    print_info('Best individual is {}, {}'.format(best_ind, best_ind.fitness.values))

    best_stars = select_stars(candidates, best_ind)
    return best_stars



def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description='Find best PSF stars using GA to minimize mean error'
                    ' of PSF fit applied to all stars by allstar. Minimized function'
                    ' is the mean of allstar\'s chi value calculated on sigma-clipped '
                    ' (sigma=4.0) list of all stars. Results'
                    ' will be stored in --dir directory if provided. List of stars'
                    ' will be output to stdout until suppressed by -no_stdout')
    parser.add_argument(metavar='image_file', type=str, default=None, dest='image_file', nargs='?',
                        help='FITS image file (default: astwro sample image)')
    parser.add_argument('--coo_file', '-c', metavar='file', type=str, default=None, dest='coo_file',
                        help='all stars list: coo file (default: from daophot FIND)')
    parser.add_argument('--frames_av', metavar='n', type=int, default=1, dest='frames_av',
                        help='frames ave - parameter of daophot FIND (default: 1)')
    parser.add_argument('--frames_sum', metavar='n', type=int, default=1, dest='frames_sum',
                        help='frames summed - parameter of daophot FIND (default: 1)')
    parser.add_argument('--lst_file', metavar='file', type=str, default=None, dest='lst_file',
                        help='PSF candidates list: lst file (default: from daophot PICK)')
    parser.add_argument('--stars_to_pick', metavar='n', dest='stars_to_pick', default=100, type=int,
                        help='number of stars to PICK as all candidates (default: 100)')
    parser.add_argument('--max_psf_err', metavar='x', type=float, default=0.1, dest='max_psf_err',
                        help='threshold for PSF errors of candidates. '
                             'Stars for which error found be PSF command is greater than x will be rejected '
                             '(default 0.1)')
    parser.add_argument('--parallel', '-p', metavar='n', type=int, default=8, dest='parallel',
                        help='how many parallel processes can be forked, '
                             'n=1 avoids parallelism (default: 8)')
    parser.add_argument('--out_dir', '-d', metavar='output_dir', type=str, default=None, dest='out_dir',
                        help='output directory. Directory will be created and result files will be stored there.'
                             ' Directory should not exist or --overwrite flag should be set'
                             ' (default: do not produce output files)')
    parser.add_argument('--overwrite', '-o', action='store_true',
                        help='if directory specified by --out_dir parameter exists, then ALL its content WILL BE DELETED')
    parser.add_argument('--no_stdout', '-t', action='store_true',
                        help='suppress printing result (list of best choice of PSF stars) to stdout at finish')
    parser.add_argument('--silent', '-s', action='store_true',
                        help='suppress writing status & stat messages (once for every generation) to stderr')
    parser.add_argument('--no_progress', '-b',  action='store_true',
                        help='suppress showing progress bar')
    parser.add_argument('--ga_init_prob', metavar='x', dest='ga_init_prob', default=0.3, type=float,
                        help='what portion of candidates is used to initialize GA individuals.'
                             ' E.g. if there is 100 candidates, each of them will be '
                             ' chosen to initialize individual genome with probability x. '
                             ' In other words if x=0.3 first population in GA will contain'
                             ' individuals with around 30 stars each. Value should be close'
                             ' according to expected number of resulting PDF stars (default: 0.3)')
    parser.add_argument('--ga_max_iter', '-i', metavar='n', dest='ga_max_iter', default=100, type=int,
                        help='maximum number of iterations - generations (default: 100)')
    parser.add_argument('--ga_pop', '-n', metavar='n', dest='ga_pop', default=80, type=int,
                        help='population size of GA (default: 80)')
    parser.add_argument('--ga_cross_prob', metavar='x', dest='ga_cross_prob', default=0.5, type=float,
                        help='crossover probability of GA (default: 0.5)')
    parser.add_argument('--ga_mut_prob', metavar='x', dest='ga_mut_prob', default=0.2, type=float,
                        help='mutation probability of GA - probability to became mutant (default: 0.2)')
    parser.add_argument('--ga_mut_str', metavar='x', dest='ga_mut_str', default=0.05, type=float,
                        help='mutation strength of GA - probability of every bit flip in mutant (default: 0.05)')

    return parser


# Below: standard skeleton for astwro.tools

def main(**kwargs):
    """Entry point for python script calls. Parameters identical to command line"""
    # Extract default arguments from command line parser and apply kwargs parameters
    args = commons.bunch_kwargs(__arg_parser(), **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)


def info():
    commons.info(__arg_parser())


if __name__ == '__main__':
    # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    __stars = __do(__args)  # call main routine - common form command line and python calls
    if not __args.no_stdout:
        print('\n'.join(map(str, __stars.index)))

