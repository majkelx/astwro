# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os.path as path
import logging
import logging.handlers
import astropy.io.fits as fits
import astwro.pydaophot
import astwro.starlist


# Two loggers: log - stderr and runlog - file logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
log = logging.getLogger()
runlog = logging.getLogger('file_runlog')
runlog.propagate = False  # do not pass logrecord to stderr logger ater logging to file


def lstcorr(mult, err, psf, phase):
    averr = err.psf_err.mean()
    err = err[(err.psf_err < mult*averr) & (err.flag == ' ')]  # filter out big errors and * or ? marked stars
    if err.count() != psf.count():
        log.info('{} PSF stars discarded during {}, error threshold: {}'.format(
            psf.count() - err.count(), phase, mult * averr))
    return psf.loc[err.index]


def daophot_photometry(
        image,
        all_stars,
        psf_stars,
        IMGPATH = '.',
        logfile = 'run.log',
        INPUT = None,
        NPSFV=15,  # minimal nuber of stars for variable PSF
        NPSFC = 5,  # minimal nuber of stars for constant PSF
        ERRPSF1 = 3.0,  # limiting multiplicator for error threshold in calculation of PSF, first iteration
        ERRPSF2 = 2.7,  # limiting multiplicator for error threshold in calculation of PSF, next iterations
        LIMMAGE = 0.25                          	 # limiting magnitude error for output stars [mag]
):
    # setup file logger
    if logfile:
        hdlr = logging.handlers.WatchedFileHandler(logfile)
        frmt = logging.Formatter('%(message)s')
        hdlr.setFormatter(frmt)
        runlog.addHandler(hdlr)
    else:
        runlog.addHandler(logging.NullHandler)

    # check for FITS file existence
    image_filepath = path.join(IMGPATH, image)
    if not path.isfile(image_filepath):
        runlog.error('{}  does not exist', image)
        raise Exception('{} does not exist in directory {}'.format(image, IMGPATH))

    # read headers
    with fits.open(image_filepath) as f:
        f[0].verify('silentfix')
        hdr = f[0].header

    OBSERV = hdr.get('OBSERVAT')
    OBJECT = hdr.get('OBJECT')
    READ_MODE = hdr.get('GAIN')


    ## set vars here
    if READ_MODE == 2:
        DAOOPT_VAR = 'daophot-Bialkow-2_var.opt'        # name of file to be used as daophot.opt with variable PSF
        DAOOPT_CONST = 'daophot-Bialkow-2_const.opt'    # name of file to be used as daophot.opt with constant PSF
    elif READ_MODE == 16:
        DAOOPT_VAR = 'daophot-Bialkow-16_var.opt'       # name of file to be used as daophot.opt with variable PSF
        DAOOPT_CONST = 'daophot-Bialkow-16_const.opt'   # name of file to be used as daophot.opt with constant PSF
    else:
        raise Exception('Unrecognized read-out mode: {}'.format(READ_MODE))
    ALLOPT = 'allstar-Bialkow.opt'        	  # name of file to be useed as allstar.opt
    PHOOPT = 'photo-Bialkow.opt'                    # name of file to be used as photo.opt


    if not INPUT:
        INPUT = path.join(path.dirname(__file__), 'daophot_bialkow_input')

    log.info(
        '*************************************\n'
        ' pyDAOPHOT/ALLSTAR workflow for %s\n'
        ' file: %s\n'
        '********************************************\n',
        OBJECT, image
    )

    if not OBSERV:
        OBSERV = 'BIALKOW'     # temporary, OBSERV should be set

    if OBSERV != 'BIALKOW':
        raise Exception('The header keyword OBSERVAT has value: {}\n'
                        'Wrong observatory name, only BIALKOW permitted\n'.format(image, OBSERV))

    # registering file in run.log
    log.info(image)
    runlog.info(image)
    im_name, _ = path.splitext(image)

    daophot_opt = path.join(INPUT, DAOOPT_VAR)
    allstar_opt = path.join(INPUT, ALLOPT)
    photo_opt   = path.join(INPUT, PHOOPT)

    # Create daophot and allstar wrappers which uses shared temporary directory
    # and running in batch mode - execution of commands on run() method
    sdaophot = astwro.pydaophot.Daophot(image=image_filepath, daophotopt=daophot_opt)
    sallstar = astwro.pydaophot.Allstar(dir=sdaophot.dir, image=image_filepath, allstaropt=allstar_opt)

    # aperture photometry (tr-allps.par)
    sdaophot.PHotometry(photoopt=photo_opt, stars=all_stars)
    # sdaophot.PIck(80,20)
    #idxslst -b=${YSIZE},${XSIZE} -r=${PSFRAD} -e=0.1 i.ap ${im_name}.lst i.lst
    all_ap = sdaophot.PHotometry_result.photometry_starlist
    psf_idx = astwro.starlist.read_dao_file(psf_stars)
    psf_ap = all_ap.loc[psf_idx.index]                         # pandas style select from all_ap which in psf_idx
    psf_ap = psf_ap[(psf_ap.A1 > 1.0) & (psf_ap.A1_err < 0.1)] # minmag and maxerr filtering

    if psf_ap.count() < NPSFC:
        raise Exception('There are not enough stars for PSF estimation: {}'.format(psf_ap.count()))

    if psf_ap.count() > NPSFV:
        sdaophot.link_to_runner_dir(path.join(INPUT, DAOOPT_VAR), 'daophot.opt')
    else:
        sdaophot.link_to_runner_dir(path.join(INPUT, DAOOPT_CONST), 'daophot.opt')

    # preliminary estimation of PSF and selection of PSF stars:
    sdaophot.PSf(psf_stars=psf_ap)  # psf - i1.par
    # lstcorr -s ${ERRPSF1} i.err i.lst
    psf_ap = lstcorr(ERRPSF1, sdaophot.PSf_result.errors, psf_ap, 'preliminary estimation of PSF')

    if psf_ap.count() < NPSFC:
        raise Exception('There are not enough stars for PSF estimation: {}'.format(psf_ap.count()))

    if psf_ap.count() > NPSFV:
        log.info('Variable PSF model in use: ({})'.format(psf_ap.count()))
    else:
        log.info('Constant PSF model in use: ({})'.format(psf_ap.count()))
        sdaophot.link_to_runner_dir(path.join(INPUT, DAOOPT_CONST), 'daophot.opt')

    # first calculation of PSF
    sdaophot.PSf(psf_stars=psf_ap)  # (psf-i1.par)
    # lstcorr -s ${ERRPSF1} i.err i.lst
    psf_ap = lstcorr(ERRPSF1, sdaophot.PSf_result.errors, psf_ap, 'first calculation of PSF')
    # # PSF stars list will not change, so write it down instead of providing as parameter
    # sdaophot.write_starlist(psf_ap, 'i.lst')

    # if (-s i.psf) then
    sallstar.set_options('ma', 100) # psf-subn.par
    sallstar.ALlstar(stars='i.nei')

    # second iteration of PSF
    sdaophot.batch_mode = True  # batch mode allows queuing multiple commands executed together on run() method
    sdaophot.SUbstar(subtract='i.als', leave_in=psf_ap)  # psf-i2.par
    sdaophot.run() # PSf command will delete i.psf do run SUbstar before it happens
    sdaophot.ATtach('is')
    sdaophot.PSf(photometry='i.als', psf_stars=psf_ap)
    sdaophot.run()
    # lstcorr -s ${ERRPSF2} i.err i.lst
    psf_ap = lstcorr(ERRPSF2, sdaophot.PSf_result.errors, psf_ap, 'second iteration of PSF')
    # if (-s i.psf) then
    sallstar.ALlstar(stars='i.nei')  # psf-subn.par

    # third iteration of PSF, grouping
    sdaophot.SUbstar(subtract='i.als', leave_in=psf_ap)  # psf-i2.par
    sdaophot.run() # PSf command will delete i.psf do run SUbstar before it happens
    sdaophot.ATtach('is.fits')
    sdaophot.PSf(photometry='i.als', psf_stars=psf_ap)
    sdaophot.ATtach(image_filepath)
    sdaophot.GRoup(critical_overlap=0.1)
    sdaophot.run()
    hx, hy = sdaophot.PSf_result.hwhm_xy


    # rmsf 160 i.grp
    # if !(-e i.grp) cp i.ap i.grp

    # final fit
    sallstar.ALlstar(stars='i.grp')  #phot.par
    # idxecorr ${LIMMAGE} i.als i.tmp
    als = sallstar.ALlstars_result.als_stars
    als = als[als.mag_rel_psf_err < LIMMAGE]
    sdaophot.GRoup(photometry=als, critical_overlap=0.1)  # photgrp.par
    sdaophot.run()
    sallstar.ALlstar(stars='i.grp')  #phot.par
    #photsrt.par
    #rmsf 200 i.idx
    #if !(-e i.idx) then

    # copying results of PSF photometry
    pphot = sallstar.ALlstars_result.als_stars.sort_values('mag_rel_psf')
    astwro.starlist.write_dao_file(pphot, im_name+'.pphot')
    sdaophot.copy_from_runner_dir('i.psf', im_name+'.psf')
    sdaophot.copy_from_runner_dir('is.fits', im_name+'sub.fits')

    #  APERTURE PHOTOMETRY WITH NEDA (2.5 * SEEING)
    A1 = 2.5 * (hx+hy)
    sdaophot.NEda(IS=35, OS=55, apertures=[A1], psf_photometry=pphot, stars_id=pphot)   # neda1.par
    sdaophot.run()
    # if !(-e i.nap) then
    aphot = sdaophot.NEda_result.neda_starlist
    # idxecorr ${LIMMAGE} i.ap1 i.tmp
    aphot = aphot[aphot.A1_err < LIMMAGE]
    astwro.starlist.write_dao_file(aphot, im_name+'.aphot')

    return sdaophot, sallstar, pphot, aphot, psf_idx, psf_ap



if __name__ == '__main__':
    from astwro.sampledata import fits_image, coo_file, lst_file
    impath, image = path.split(fits_image())
    alls = coo_file()
    psfs = lst_file()

    try:
        r = daophot_photometry(image, all_stars=alls, psf_stars=psfs, IMGPATH=impath)
    except Exception as e:
        log.error('ERROR when processing file {}:\n{} '.format(image, e.message))
        raise


