from __future__ import print_function
from astwro.pydaophot import daophot, allstar, fname
from astwro.starlist import read_dao_file
from astwro.utils import tmpdir
import os
import sys
import numpy as np

basefilename = 'i'
results_path = None
pick_candidates = 80
pick_mag_limit = 20
run_parallel = 8

#fits = basefilename + '.fits'
fits = 'NGC6871.fits'
coo = basefilename + '.coo'
ap = basefilename + '.ap'
lst = basefilename + '.lst'
als = basefilename + '.als'

dopt = 'daophot.opt'
popt = 'photo.opt'
aopt = 'allstar.opt'

if not os.path.isfile(dopt):
    dopt = None
if not os.path.isfile(popt):
    popt = None
if not os.path.isfile(aopt):
    aopt = None

results_dir = tmpdir(use_exiting=results_path, prefix='psf_red_', base_dir=os.getcwd())
results_dir.dir_is_tmp = False
print ('Expect results in: {!s}'.format(results_dir),file=sys.stderr)

dp = daophot(image_file=fits, daophotopt=dopt, photoopt=popt, dir=results_dir)

# 1. Make sure that we are ready to PSF photometry, collect all needed files in dp.dir
# --

# FI needed?
if not os.path.isfile(coo):
    dp.FInd(1,1)
    assert (not os.path.isfile(ap) and not os.path.isfile(lst))
else:
    dp.copy_to_runner_dir(coo, fname.COO_FILE)

# PH needed?
if not os.path.isfile(ap):
    dp.PHotometry()
    assert (not os.path.isfile(lst))
else:
    dp.copy_to_runner_dir(ap, fname.AP_FILE)

# PI needed?
if not os.path.isfile(lst):
    dp.PIck(pick_candidates, faintest_mag=pick_mag_limit)
else:
    dp.copy_to_runner_dir(lst, fname.LST_FILE)

# run tasks list
dp.run(wait=True)

# 2. Now th game begins. our population has one runner, no PSF performed so we not call it the best
# ---
# runner runs only once, create new with old one's directory
population = [daophot(dir=dp.dir)]
prev_winner = winner = None
prev_winner_score = 1001
winner_score = 1000
log = []
counter = 0

# score function - best score wins in population
score_function = lambda (result): result['als_chi']

while winner_score < prev_winner_score:
    prev_winner = winner
    prev_winner_score = winner_score
    # population ready for psf photometry
    # because image file was not provided in constructor, AT must be called explicitly
    for d in population:
        d.ATtach()
        d.PSf()
    # run them in parallel, but not at once
    for n in range(0, len(population), run_parallel):
        for d in population[n:n+run_parallel]:  # run group
            d.run(wait=False)
        for d in population[n:n+run_parallel]:  # wait for group
            d.wait_for_results()
            # print (d.output)
    # time for allstar
    population_alls = [allstar(dir=d.dir, allstaropt=aopt, create_subtracted_image=False) for d in population]
    # run them same way
    for n in range(0, len(population_alls), run_parallel):
        for d in population_alls[n:n + run_parallel]:  # run group
            d.run(wait=False)
        for d in population_alls[n:n + run_parallel]:  # wait for group
            d.wait_for_results()
            print (d.output)
    # measure results and chose the best
    scores = np.zeros_like(population)
    for i, d in enumerate(population):
        conv_stars = read_dao_file(d.file_from_runner_dir(fname.ALS_FILE))
        psf_stars = read_dao_file(d.file_from_runner_dir(fname.LST_FILE))
        result = {
            'n': len(log),
            'conv_stars': len(conv_stars), # converged by allstar
            'psf_stars': len(psf_stars),   # pdf stars
            'als_chi': conv_stars['chi'].mean(),  # mean of chi form ALS
            'psf_chi': d.PSf_result.chi,    # chi from daophot PS
            'removed_star': 0
        }
        scores[i] = score_function(result)
        log.append(result)
        if counter % 8 == 0:
            print ('Done:{:5d}'.format(counter))
        counter += 1
    # and the winner is....
    max_scored = scores.argmax()
    winner_score = scores[max_scored]
    winner = population[max_scored]
    print ('Round winner scored {:f} after {:d} calculations')

    winner.copy_from_runner_dir(fname.LST_FILE, os.path.join(results_dir, 'round'))
    winning_psf_stars = read_dao_file(winner.file_from_runner_dir(fname.LST_FILE))

    # now prepare next population
#    population = [daophot(dir=winner.dir.clone()) for _ in ]

    ## calculate score for population:
    # define score function

    ## TODO metadane sesji - individual, population, round

    break ## TODO: temporary break
