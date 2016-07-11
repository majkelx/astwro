import os
from .Runner import Runner

class fname:
    ''' filenames in temp work dir '''
    DAOPHOT_OPT = 'daophot.opt'
    PHOTO_OPT = 'photo.opt'
    ALLSTAR_OPT = APERTURES_FILE = 'allstar.opt'
    IMAGE_FILE = 'i.fits'
    FOUNDSTARS_FILE = COO_FILE = 'i.coo'
    PHOTOMETRY_FILE = AP_FILE = 'i.ap'
    PSF_STARS_FILE = LST_FILE ='i.lst'
    NEIGHBOURS_FILE = NEI_FILE = 'i.nei'
    PSF_FILE = 'i.psf'
    ALLSTARS_FILE = ALS_FILE = 'i.als'
    SUBTRACTED_IMAGE_FILE = SUB_FILE = 'i.sub.fits'



class DAORunner(Runner):
    """base for daophot package runners runner"""


    def __init__(self, config=None, dir=None):
        Runner.__init__(self, config=config, dir=dir)

    def __deepcopy__(self, memo):
        return Runner.__deepcopy__(self, memo)


    # dao files managegement
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

