import os
from logging import *
from .Runner import Runner
from .config import get_package_config_path
from .OutputProviders import *


class fname:
    ''' filenames in temp work dir '''
    DAOPHOT_OPT = 'daophot.opt'
    PHOTO_OPT = 'photo.opt'
    APERTURES_FILE = PHOTO_OPT
    IMAGE_FILE = 'i.fits'
    STARS_FILE = 'i.coo'
    PHOTOMETRY_FILE = 'i.ap'
    PSF_STARS_FILE = 'i.lst'
    NEIGHBOURS_FILE = 'i.nei'
    PSF_FILE = 'i.psf'



class DPRunner(Runner):
    daophotopt = None
    photoopt = None
    # output processors
    OPtion_result = None
    ATtach_result = None
    FInd_result = None
    PHotometry_result = None
    PIck_result = None
    PSf_result = None


    def __init__(self, config = None, daophotopt=None, photoopt=None):
        Runner.__init__(self, config)
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(), fname.DAOPHOT_OPT)
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(), fname.PHOTO_OPT)

        self.OPtion_result = DPOP_OPtion()
        self.interact('', output_processor=self.OPtion_result)

    def on_exit(self):
        pass

    def init_config_files(self, dir):
        Runner.init_config_files(self, dir)
        self.copy_to_working_dir(os.path.join(get_package_config_path(), fname.DAOPHOT_OPT))
        self.copy_to_working_dir(os.path.join(get_package_config_path(), fname.PHOTO_OPT))

    # daophot files managegement
    def apertures_file_push(self, src_path):
        self.copy_to_working_dir(src_path, fname.PHOTO_OPT)

    def apertures_file_pull(self, dst_path = '.'):
        self.copy_from_working_dir(fname.PHOTO_OPT, dst_path)

    def apertures_file_create(self, apertures, IS, OS):
        """Creates photo.opt in daophot working dir
            :arg apertures -- list of apertures A1,A2... e.g. [6.0,8.0,12.0]
            :arg IS -- inner radius of sky annulus
            :arg OS -- outer radius of sky annulus
            """
        assert len(apertures) > 0 and len(apertures) < 13
        self.rm_from_working_dir(fname.PHOTO_OPT)
        with open(os.path.join(self.dir, fname.PHOTO_OPT), 'w') as f:
            f.write(''.join('A{:1X}={:.2f}\n'.format(n+1, v) for n,v in zip(range(len(apertures)), apertures)))
            f.write('IS={:.2f}'.format(IS))
            f.write('OS={:.2f}'.format(OS))

    # daophot commands
    def ATtach(self, image_file):
#        self.link_to_working_dir(image_file, 'i.fits')
        self.copy_to_working_dir(image_file, fname.IMAGE_FILE)
        processor = DPOP_ATtach()
        self.interact('ATTACH\ni.fits\n', output_processor=processor)
        self.ATtach_result = processor
        return processor

    def EXit(self):
        self.interact('EXIT\n', output_processor=DaophotCommandOutputProcessor())

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
        self.interact(commands, output_processor=processor)
        self.OPtion_result = processor
        return processor

    def FInd(self, frames_av = 1, frames_sum = 1, starlist_file=fname.STARS_FILE):
        if self.ATtach_result is None:
            raise Exception('No imput file attached, call ATttache first.')
        self.rm_from_working_dir(starlist_file)
        commands = 'FIND\n{},{}\n{}\nyes\n'.format(frames_av, frames_sum, starlist_file)
        processor = DpOp_FInd()
        self.interact(commands, output_processor=processor)
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
        self.interact(commands, output_processor=processor)
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
        self.interact(commands, output_processor=processor)
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
        self.interact(commands, output_processor=processor)
        self.PSf_result = processor
        return processor


