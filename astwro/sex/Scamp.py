from __future__ import absolute_import, division, print_function

__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef
from os.path import join, basename, splitext
from astwro.exttools import Runner
from astwro.config import find_opt_file
from .Sextractor import SexResults


class ScampResults(object):

    def __init__(self, dir, results_filename):
        super(ScampResults, self).__init__()
        self.dir = dir
        self.header_file = results_filename
        self._header = None

    @property
    def fits_header(self):
        if self._header is None:
            import astropy.io.fits as pyfits
            self._header = pyfits.Header.fromtextfile(self.header_file, endcard=True)
        return self._header


class Scamp(Runner):
    """ Emmanuel BERTIN `scamp` runner

    Object of this class maintains single process of `scamp` and it's working directory.

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

    def __init__(self, dir=None, conf=None):
        # base implementation of __init__ calls `_reset` also
        super(Scamp, self).__init__(dir=dir, batch=False)
        self.conf_file = conf
        self.SCAMPresults = None
        self._update_executable('scamp')

    def _reset(self):
        super(Scamp, self)._reset()

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = super(Scamp, self).__deepcopy__(memo)

        return new

    def _pre_run(self, wait):
        super(Scamp, self)._pre_run(wait=wait)



    def _init_workdir_files(self, dir):
        super(Scamp, self)._init_workdir_files(dir)

    def __call__(self, src):
        """ Run scamp on crc catalog

        Parameters
        ----------
        src : str or SexResults
            Source catalog. Filename or SexResults

        Returns
        -------
        ScampResults object
        """
        if isinstance(src, SexResults):
            src = join(src.dir, src.stars_file)
        if self.conf_file is None:
            conf_file = find_opt_file('scamp.conf', package='sex')
        else:
            conf_file = self.conf_file

        out_file = splitext(basename(src))[0] # 'output1'


        self._prepare_input_file(conf_file, preservefilename = True)
        self._prepare_input_file(src, preservefilename=True)

        self.SCAMPresults = ScampResults(dir=self.dir.path,  results_filename=out_file)
        self.arguments = [basename(src), '-c', basename(conf_file)]
        self.run()
        return self.SCAMPresults



