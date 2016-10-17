#! /usr/bin/env python
# coding=utf-8
""" Find best PSF stars using GA to minimize mean error
"""
from __future__ import print_function, division
import random
import sys
import os
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
               "({} rejected because psf error exceeded threshold of {}) of mag {} to {}".format(
        candidates.count(),
        all_cand_no - candidates.count(),
        arg.max_psf_err,
        candidates.mag1.max(),
        candidates.mag1.min()))

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

    eval_count = 0

    # Evaluate individual function - most important one - function which is minimized here
    # First one is fst but is here only for testing purpose (algorithm with that one is equivalent
    # of sorting candidates stars be psf_err)
    # Second uses allstar to calculate psf for all stars in field and checks mean error. Slow like a hell

    def evaluate_fast_test(candidates, min_stars, dir, individual):
        """
        Fast version FOR TESTING ONLY - prefers low mean PSF error from errors returned by daophot's PSF.
        And at least max_stars  stars
        :param StarList candidates:
        :param int min_stars:
        :param bitarray individual:
        :param TmpDir dir: directory with daophot results (not used in this version)
        :rtype: float
        """
        global eval_count
        eval_count += 1
        stars = individual.count(True)
        sum_err = 0.0
        if stars < min_stars:
            return 1.0,  # high - bad score
        else:
            for i, v in enumerate(individual):
                if v:
                    sum_err += candidates.iloc[i]['psf_err']
        return sum_err / stars,

    # create pool of workers TODO do not use global
    pool = []
    for i in range(arg.parallel):
        d = daophot(arg.image_file)  # TODO other params
        a = allstar(d.dir)
        d.copy_to_working_dir(dp.file_from_working_dir(fname.AP_FILE), fname.AP_FILE)
        pool.append({'daophot': d, 'allstar': a})

    def eval_population(population):
        """
        Evaluates fitness for all individual in population.
        Use of one function for population (rather than for individuals)
        to implement parallel execution in workers pool.
        :param list population:
        :return: list fitnesses (1-element couples as deap likes)
        """
        fitnesses = []
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
                    worker['allstar'].run(wait=False)  # parallel
            # wait for allstar for workers and process results
            for individual, worker in zip(chunk, pool):
                if individual:
                    worker['allstar'].wait_for_results()
                    try:  # TODO temporary catch - clean it up
                        all_s = read_dao_file(worker['allstar'].file_from_working_dir(fname.ALS_FILE))
                        fitnesses.append((sigmaclip(all_s.psf_chi)[0].mean(),))
                    except Exception as e:
                        print_info(e)  # Failed to converge from daophot usually.
                        print_info(worker['daophot'].output)
                        print_info(worker['daophot'].stderr)
                        print_info(worker['allstar'].output)
                        print_info(worker['allstar'].stderr)
                        fitnesses.append((2.0,))
        return fitnesses

    def evaluate_allstar(candidates, min_stars, dir, individual):
        """
        Proper version - uses allstar to calculate psf for all stars in field and checks mean error.
        :param StarList candidates:
        :param int min_stars: (not used here, let errors tell how many stars needed)
        :param bitarray individual:
        :param TmpDir dir: directory with daophot results
        :rtype: float
        """
        # obtain StarList from current genome
        pdf_s = select_stars(candidates, individual)
        # create new daophot runner
        dp = daophot(os.path.join(str(dir), 'i.fits'))  # TODO pass daophot runner instead of dir
        # create PSF stars file .lst TODO: proper DAO headers in write!
        write_dao_file(pdf_s, dp.file_from_working_dir(fname.LST_FILE))
        # copy .ap file from previously calculated by daophot
        dp.copy_to_working_dir(os.path.join(str(dir), 'i.ap'), fname.AP_FILE)
        # TODO provide opt files!
        # caluclate PSF
        dp.PSf()
        dp.run()
        # create new allstar runner sharing working dir with daophot
        al = allstar(dp.dir)
        # calculate psf for all stars
        al.run()
        # read result .als file
        all_s = read_dao_file(al.file_from_working_dir(fname.ALS_FILE))
        # calculate and return mean error
        return all_s.psf_chi.mean()

    def pmap(function, iterable):
        if arg.parallel == 1:
            return map(function, iterable)
        else:
            if pmap.pool is None:
                from multiprocessing import Pool
                pmap.pool = Pool(arg.parallel)
            return pmap.pool.map(function, iterable)

    pmap.pool = None

    # 2.2 Prepare output directory
    if arg.out_dir:
        from shutil import copytree, rmtree

        arg.out_dir = os.path.abspath(os.path.expanduser(arg.out_dir))
        if os.path.exists(arg.out_dir) and arg.overwrite:
            rmtree(arg.out_dir)
        copytree(str(dp.dir), arg.out_dir)
        # todo allstar.opt missing!
        basename = os.path.join(arg.out_dir, 'gen')
        lst_file = cyclefile(basename, '.lst')
        reg_file = cyclefile(basename, '.reg')
        gen_file = cyclefile(basename, '.gen')

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
    toolbox.register("evaluate", evaluate_allstar, candidates, all_cand_no * arg.ga_init_prob / 2, dp.dir)
    # toolbox.register("evaluate", evaluate_fast_test, candidates, all_cand_no * arg.ga_init_prob / 2, dp.dir)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutFlipBit, indpb=arg.ga_mut_str)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=arg.ga_pop)

    # Evaluate the entire population
    fitnesses = eval_population(pop)
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # Begin the evolution
    for g in range(arg.ga_max_iter):
        print_info('-- Generation {:d} --'.format(g))
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
        fitnesses = eval_population(invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        # New population from offspring
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x * x for x in fits)
        std = abs(sum2 / length - mean ** 2) ** 0.5

        print_info('Gen: {:3d}  Min {:.4f} Max {:.4f} Avg {:.4f} Std {:.4f} '.format(
            g, min(fits), max(fits), mean, std))
        # best from generation:
        best_ind = tools.selBest(pop, 1)[0]
        best_stars = select_stars(candidates, best_ind)
        print_info('  best in generation contains {:d} stars'.format(best_stars.count()))

        # for every generation create lst file and ds9 reg file of best and point symlinks to last generation
        if arg.out_dir:
            lst_file.next_file(g)
            reg_file.next_file(g)
            gen_file.next_file(g)
            write_dao_file(best_stars, lst_file.file, DAO.LST_FILE)
            write_ds9_regions(best_stars, reg_file.file)
            sort_pop = sorted(pop, key=lambda x: x.fitness, reverse=True)
            for ind in pop:
                gen_file.file.write(ind.to01() + '\n')

    # 3. Winner?

    print_info('-- End of (successful) evolution, fitness evaluated {} times --'.format(eval_count))

    best_ind = tools.selBest(pop, 1)[0]
    print_info('Best individual is {}, {}'.format(best_ind, best_ind.fitness.values))

    best_stars = select_stars(candidates, best_ind)
    if not arg.no_stdout:
        print('\n'.join(map(str, best_stars.index)))

        # write_ds9_regions(best_stars, 'best_for_psf.reg')


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
    parser.add_argument('--coo_file', metavar='file', type=str, default=None, dest='coo_file',
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
                             'Stars for which error found be PSF command is greater than x will be rejected')
    parser.add_argument('--parallel', metavar='n', type=int, default=8, dest='parallel',
                        help='how many parallel processes can be forked, '
                             'n=1 avoids parallelism (default: 8)')
    parser.add_argument('--out_dir', metavar='output_dir', type=str, default=None, dest='out_dir',
                        help='output directory. Directory will be created and result files will be stored there.'
                             ' Directory should not exist or --overwrite flag should be set'
                             ' (default: do not produce output files)')
    parser.add_argument('--overwrite', action='store_true',
                        help='if directory specified by --dir parameter exists, then ALL its content WILL BE DELETED')
    parser.add_argument('--no_stdout', action='store_true',
                        help='suppress printing result (list of best choice of PSF stars) to stdout at finish')
    parser.add_argument('--silent', action='store_true',
                        help='suppress writing progress messages (once for every generation) to stderr')
    parser.add_argument('--ga_init_prob', metavar='x', dest='ga_init_prob', default=0.3, type=float,
                        help='what portion of candidates is used to initialize GA individuals.'
                             ' E.g. if there is 100 candidates, each of them will be '
                             ' chosen to initialize individual genome with probability x. '
                             ' In other words if x=0.3 first population in GA will contain'
                             ' individuals with around 30 stars each. Value should be close'
                             ' according to expected number of resulting PDF stars (default: 0.3)')
    parser.add_argument('--ga_max_iter', metavar='n', dest='ga_max_iter', default=100, type=int,
                        help='maximum number of iterations - generations (default: 100)')
    parser.add_argument('--ga_pop', metavar='n', dest='ga_pop', default=80, type=int,
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
    __do(__args)  # call main routine - common form command line and python calls