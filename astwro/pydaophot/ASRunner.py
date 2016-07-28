import os
from .DAORunner import DAORunner, fname
from .config import get_package_config_path
from .OutputProviders import *




class ASRunner(DAORunner):
    """allstar runner"""
    allstaropt = None
    image_file = None
    psf_file = None
    photometry_file = None
    create_subtracted_image = False
    # output processors
    options = None
    result = None
    __option_commands = ''

    def __init__(self, config=None, dir=None,
                 allstaropt=None,
                 image_file=None,
                 psf_file=None,
                 photometry_file=None,
                 create_subtracted_image=False
                 ):
        self.executable = os.path.expanduser(config.get('executables', 'allstar'))
        self.allstaropt = allstaropt if allstaropt is not None else os.path.join(get_package_config_path(), fname.ALLSTAR_OPT)
        self.image_file = image_file
        self.psf_file = psf_file
        self.photometry_file = photometry_file
        self.create_subtracted_image = create_subtracted_image
        DAORunner.__init__(self, config=config, dir=dir)
        self.options = AsOp_opt()
        self._insert_processing_step('WA=0\n', output_processor=self.options)

    def __deepcopy__(self, memo):
        from copy import deepcopy
        new = DAORunner.__deepcopy__(self, memo)
        new.allstaropt = deepcopy(self.allstaropt, memo)
        new.image_file = deepcopy(self.image_file, memo)
        new.psf_file = deepcopy(self.psf_file, memo)
        new.photometry_file = deepcopy(self.photometry_file, memo)
        new.create_subtracted_image = deepcopy(self.create_subtracted_image, memo)
        new.options = deepcopy(self.options, memo)
        new.result = deepcopy(self.result, memo)
        new.__option_commands = deepcopy(self.__option_commands, memo)
        return new

    def _on_exit(self):
        pass

    def _reset(self):
        DAORunner._reset(self)
        self.options = AsOp_opt()
        self._insert_processing_step('WA=0\n', output_processor=self.options)
        result = None

    def _init_workdir_files(self, dir):
        DAORunner._init_workdir_files(self, dir)
        files_to_copy = [
            (self.allstaropt, fname.ALLSTAR_OPT),
            (self.psf_file, fname.PSF_FILE),
            (self.photometry_file, fname.PHOTOMETRY_FILE)
        ]
        for file, dest in files_to_copy:
            if file is not None:
                self.copy_to_working_dir(self.expand_default_file_path(file), dest)
        if self.image_file is not None:
            self.link_to_working_dir(self.expand_default_file_path(self.image_file), fname.IMAGE_FILE)

    def set_options(self, options, value=None):
        """set option(s) before run. options can be either:
                dictionary:             dp.OPtion({'GAIN': 9, 'FI': '6.0'})
                iterable of tuples:     dp.OPtion([('GA', 9.0), ('FITTING RADIUS', '6.0')])
                option key, followed by value in 'value' parameter:
                                        dp.OPtion('GA', 9.0)
                filename string of allstar.opt-formatted file (file will be symlinked as allstar.opt):
                                        dp.OPtion('opts/newallstar.opt')
                """
        if isinstance(options, str) and value is None:  # filename
            # daophot operates in his tmp dir and has limited buffer for file path
            # so symlink file to its working dir
            self.link_to_working_dir(options, fname.ALLSTAR_OPT)
        else:
            commands = ''
            if value is not None:
                options = [(options,value)]
            elif isinstance(options, dict):
                options = options.items()
            commands += ''.join('%s=%.2f\n' % (k,float(v)) for k,v in options)
            self._insert_processing_step(commands)

    def _pre_run(self, wait):
        commands = '\n{}\n\n\n\n{}\n'.format(
            fname.IMAGE_FILE,
            fname.SUBTRACTED_IMAGE_FILE if self.create_subtracted_image else ''
        )
        self.rm_from_working_dir(fname.ALLSTARS_FILE)
        if self.create_subtracted_image:
            self.rm_from_working_dir(fname.SUBTRACTED_IMAGE_FILE)
        self.result = AsOp_result()
        self._insert_processing_step(commands, output_processor=self.result)

