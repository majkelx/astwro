import os
from logging import *
from .Runner import Runner
from .config import get_package_config_path
from .OutputProviders import *

class DPRunner(Runner):
    daophotopt = None
    photoopt = None
    # output processors
    init_processor = None
    attach_processor = None

    def __init__(self, config = None, daophotopt=None, photoopt=None):
        Runner.__init__(self, config)
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(),'daophot.opt')
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(),'photo.opt')

        self.read_std_out = True

        self.run()
        info('Runner for executable: %s running', self.executable)
        self.init_processor = DaophotCommandOutputProcessor()
        self.interact(output_processor=self.init_processor)


    def init_config_files(self, dir):
        Runner.init_config_files(self, dir)
        self.copy_to_working_dir(os.path.join(get_package_config_path(), 'daophot.opt'))

    def attach(self, image_file):
        filename = self.link_to_working_dir(image_file, 'input.fits')
        self.attach_processor = DaophotAttachOP()
        self.interact('attach\ninput.fits\n\n', output_processor=self.attach_processor)

    def find(self):
        pass

    def get_pic_size(self):
        return self.attach_processor.get_picture_size()
