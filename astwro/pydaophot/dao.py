from .DPRunner import DPRunner
from .ASRunner import ASRunner
from . import config


daophot_cfg = config.parse_config_files()

def daophot(dir=None,
            daophotopt=None,
            photoopt=None,
            image_file=None):
    """
    creates instance of daophot runner DPRunner
    :param dir:         pathname or TmpDir object - working directory for daophot,
                        if None temp dir will be used and deleted on DPRunner.close()
    :param daophotopt:  daophot.opt file, if None build in default file will be used, can be added later
                        by DPRunner.copy_to_working_dir(file, fname.DAOPHOT_OPT)
    :param photoopt:    photo.opt file, if None build in default file will be used, can be added later
                        by DPRunner.copy_to_working_dir(file, fname.PHOTO_OPT)
    :param image_file   if provided this file will be automatically attached (AT) as first daophot command
    :return: DPRunner instance
    """
    return DPRunner(daophot_cfg, dir=dir, daophotopt=daophotopt, photoopt=photoopt, image=image_file)


def allstar(dir=None,
            allstaropt=None,
            image_file=None,
            psf_file=None,
            photometry_file=None,
            create_subtracted_image=False):
    """
    creates instance of allstar runner ASRunner
    :param dir:         pathname or TmpDir object - working directory for allstar,
                        if None temp dir will be used and deleted on DPRunner.close()
                        daophot runner dir can be used: allstar(dir = dp.dir)
    :param allstaropt:  allstar.opt file, if None build in default file will be used, can be added later
                        by DPRunner.copy_to_working_dir(file, fname.ALLSTAR_OPT)
    :param image_file:  image file: input of allstar. if not provided allstar will look for i.fits in work dir
    :param psf_file:    daophot PSF file: if not provided allstar will look for i.psf in work dir
    :param photometry_file: daophot AP file: if not provided allstar will look for i.ap in work dir
    :param create_subtracted_image: if True, allstar will be instructed to generated subtracted image i.sub.fits
    :return: instance of ASRunner
    """
    return ASRunner(daophot_cfg, dir, allstaropt, image_file, psf_file, photometry_file, create_subtracted_image)
