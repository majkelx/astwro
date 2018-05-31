from __future__ import absolute_import, division, print_function

__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef
from os.path import join, basename
from astwro.exttools import Runner
from astwro.config import find_opt_file

#TODO: suport for configuration and conf files (xommon with scamp)


class SexResults(object):

    def __init__(self, dir, results_filename):
        super(SexResults, self).__init__()
        self.dir = dir
        self.stars_file = results_filename
        self._stars = None

    @property
    def stars(self):
        if self._stars is None:
            import astropy.io.fits as pyfits
            self._stars = pyfits.getdata(join(self.dir, self.stars_file),2)
        return self._stars


class Sextractor(Runner):
    """ Emmanuel BERTIN `sextractor` runner

    Object of this class maintains single process of `extractor` and it's working directory.

    Note
    ----
    Very `alpha` stage, very limited


    Parameters
    ----------
    dir : str, TmpDir, optional
        Working directory for sextractor process
        Default - new TmpDir will be created and destroyed with Sextractor object
    conf : str, optional
        Patch to sextractor's configuration file, Default: package default file
    param : str, optional
        Patch to sextractor's parameters file (specified in conf), Default: package default file
    conv : str, optional
        Patch to sextractor's convolution file (specified in conf), Default: package default file
    """

    def __init__(self, dir=None, conf=None, param=None, conv=None, output=None):
        # base implementation of __init__ calls `_reset` also
        super(Sextractor, self).__init__(dir=dir, batch=False)
        self.conf_file = conf
        self.param_file = param
        self.conv_file = conv
        self.output_file = output
        self.SEXresults = None
        self._update_executable('sextractor')

    def _reset(self):
        super(Sextractor, self)._reset()

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = super(Sextractor, self).__deepcopy__(memo)

        return new

    def _pre_run(self, wait):
        super(Sextractor, self)._pre_run(wait=wait)



    def _init_workdir_files(self, dir):
        super(Sextractor, self)._init_workdir_files(dir)

    def __call__(self, image):
        """ Run sextractor on image

        Parameters
        ----------
        image : str
            Path of the FITS image

        Returns
        -------
        SexResults object
        """
        if self.conf_file is None:
            conf_file = find_opt_file('sextractor.conf', package='sex')
            out_file = 'output1.fits'
            self._prepare_input_file(find_opt_file('sextractor.param', package='sex'), preservefilename=True)
            self._prepare_input_file(find_opt_file('sextractor.conv', package='sex'), preservefilename=True)
        else:
            out_file  = self.output_file
            conf_file = self.conf_file
            if self.param_file is not None:
                self._prepare_input_file(self.param_file, preservefilename=True)
            if self.conv_file is not None:
                self._prepare_input_file(self.conv_file, preservefilename=True)
        self._prepare_input_file(conf_file, preservefilename = True)
        self._prepare_input_file(image, preservefilename=True)

        self.SEXresults = SexResults(dir=self.dir.path,  results_filename=out_file)
        self.arguments = [basename(image), '-c', basename(conf_file)]
        self.run()
        return self.SEXresults



