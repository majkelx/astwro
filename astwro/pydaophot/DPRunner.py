import os
from .DAORunner import DAORunner, fname
from .config import get_package_config_path
from .OutputProviders import *




class DPRunner(DAORunner):
    """daophot runner"""
    daophotopt = None
    photoopt = None
    # output processors
    OPtion_result = None
    ATtach_result = None
    FInd_result = None
    PHotometry_result = None
    PIck_result = None
    PSf_result = None

    def __init__(self, config=None, dir=None, daophotopt=None, photoopt=None, image=None):
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(), fname.DAOPHOT_OPT)
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(), fname.PHOTO_OPT)
        DAORunner.__init__(self, config=config, dir=dir)
        self.OPtion_result = DPOP_OPtion()
        self._insert_processing_step('', output_processor=self.OPtion_result)
        if image:
            self.ATtach(image)

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = DAORunner.__deepcopy__(self, memo)
        new.daophotopt = deepcopy(self.daophotopt, memo)
        new.photoopt = deepcopy(self.photoopt, memo)
        new.OPtion_result = deepcopy(self.OPtion_result, memo)
        new.ATtach_result = deepcopy(self.ATtach_result, memo)
        new.FInd_result = deepcopy(self.FInd_result, memo)
        new.PHotometry_result = deepcopy(self.PHotometry_result, memo)
        new.PIck_result = deepcopy(self.PIck_result, memo)
        new.PSf_result = deepcopy(self.PSf_result, memo)
        return new

    def _on_exit(self):
        pass

    def reset(self):
        DAORunner.reset(self)
        self.ATtach_result = None
        self.FInd_result = None
        self.PHotometry_result = None
        self.PIck_result = None
        self.PSf_result = None
        self.OPtion_result = DPOP_OPtion()
        self._insert_processing_step('', output_processor=self.OPtion_result)

    def _init_workdir_files(self, dir):
        DAORunner._init_workdir_files(self, dir)
        self.copy_to_working_dir(self.daophotopt)
        self.copy_to_working_dir(self.photoopt)

    # daophot commands
    def ATtach(self, image_file):
        self.link_to_working_dir(image_file, 'i.fits')
        # self.copy_to_working_dir(image_file, fname.IMAGE_FILE)
        processor = DPOP_ATtach()
        self._insert_processing_step('ATTACH\ni.fits\n', output_processor=processor)
        self.ATtach_result = processor
        return processor

    def EXit(self):
        self._insert_processing_step('EXIT\n', output_processor=DaophotCommandOutputProcessor())

    def OPtion(self, options, value=None):
        """Set daophot option(s). options can be either:
                dictionary:             dp.OPtion({'GAIN': 9, 'FI': '6.0'})
                iterable of tuples:     dp.OPtion([('GA', 9.0), ('FITTING RADIUS', '6.0')])
                option key, followed by value in 'value' parameter:
                                        dp.OPtion('GA', 9.0)
                filename string of daophot.opt-formatted file:
                                        dp.OPtion('opts/newdaophot.opt')
                """
        # if self.ATtach_result is None:
        #     warning('daophot (at least some version) crashes on ATtach after OPtion. Expect crash on next ATtach.')
        commands = 'OPT\n'
        if isinstance(options, str) and value is None:  # filename
            # daophot operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self.link_to_working_dir(options, 'tmp.opt')
            commands += 'tmp.opt\n\n'
        else:
            commands += '\n'  # answer for filename
            if value is not None:
                options = [(options,value)]
            elif isinstance(options, dict):
                options = options.items()
            commands += ''.join('%s=%.2f\n' % (k,float(v)) for k,v in options)
            commands += '\n'
        processor = DPOP_OPtion()
        self._insert_processing_step(commands, output_processor=processor)
        self.OPtion_result = processor
        return processor

    def FInd(self, frames_av = 1, frames_sum = 1, starlist_file=fname.FOUNDSTARS_FILE):
        if self.ATtach_result is None:
            raise Exception('No imput file attached, call ATttache first.')
        self.rm_from_working_dir(starlist_file)
        commands = 'FIND\n{},{}\n{}\nyes\n'.format(frames_av, frames_sum, starlist_file)
        processor = DpOp_FInd()
        self._insert_processing_step(commands, output_processor=processor)
        self.FInd_result = processor
        return processor

    def PHotometry(self, photoopt=None, stars_file=None, photometry_file=None):
        if photometry_file is None:
            self.rm_from_working_dir(fname.PHOTOMETRY_FILE)
        photoopt   = self.expand_default_file_path(photoopt)
        stars_file = self.expand_default_file_path(stars_file)
        photometry_file = self.expand_default_file_path(photometry_file)
        commands='PHOT\n{}\n\n{}\n{}\n'.format(photoopt, stars_file, photometry_file)
        processor = DpOp_PHotometry()
        self._insert_processing_step(commands, output_processor=processor)
        self.PHotometry_result = processor
        return processor

    def PIck(self, number_of_stars_to_pick=50, faintest_mag=20, photometry_file=None, psf_stars_file=None):
        if photometry_file is None:
            self.rm_from_working_dir(fname.PSF_STARS_FILE)
        photometry_file = self.expand_default_file_path(photometry_file)
        psf_stars_file = self.expand_default_file_path(psf_stars_file)
        commands = 'PICK\n{}\n{:d},{:d}\n{}\n'.format(
            photometry_file,
            number_of_stars_to_pick,
            faintest_mag,
            psf_stars_file
        )
        processor = DpOp_PIck()
        self._insert_processing_step(commands, output_processor=processor)
        self.PIck_result = processor
        return processor

    def PSf(self, photometry_file=None, psf_stars_file=None, psf_file=None):
        if psf_file is None:
            self.rm_from_working_dir(fname.PSF_FILE)
        photometry_file = self.expand_default_file_path(photometry_file)
        psf_stars_file = self.expand_default_file_path(psf_stars_file)
        psf_file = self.expand_default_file_path(psf_file)
        commands = 'PSF\n{}\n{}\n{}\n'.format(
            photometry_file,
            psf_stars_file,
            psf_file
        )
        processor = DpOp_PSf()
        self._insert_processing_step(commands, output_processor=processor)
        self.PSf_result = processor
        return processor


