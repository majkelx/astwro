import os
from logging import *
from .Runner import Runner
from .config import get_package_config_path
from .OutputProviders import *

class DPRunner(Runner):
    daophotopt = None
    photoopt = None
    # output processors
    opt_processor = None
    attach_processor = None

    def __init__(self, config = None, daophotopt=None, photoopt=None):
        Runner.__init__(self, config)
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(),'daophot.opt')
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(),'photo.opt')

        self.read_std_out = True

        self.run()
        info('Runner for executable: %s running', self.executable)
        self.opt_processor = DaophotOptOP()
        self.interact('\n', output_processor=self.opt_processor)

    def init_config_files(self, dir):
        Runner.init_config_files(self, dir)
        self.copy_to_working_dir(os.path.join(get_package_config_path(), 'daophot.opt'))

    # daophot commands
    def ATtach(self, image_file):
        self.link_to_working_dir(image_file, 'input.fits')
        self.attach_processor = DaophotAttachOP()
        self.interact('ATTACH\ninput.fits\n\n', output_processor=self.attach_processor)

    def OPtion(self, options, value=None):
        """Set pyraf option(s). options can be either:
                dictionary:             dp.OPtion({'GAIN': 9, 'FI': '6.0'})
                iterable of tuples:     dp.OPtion([('GA', 9.0), ('FITTING RADIUS', '6.0')])
                option key, followed by value in 'value' parameter:
                                        dp.OPtion('GA', 9.0)
                filename string of daophot.opt-formatted file:
                                        dp.OPtion('opts/newdaophot.opt')
                """
        if self.attach_processor is None:
            warning('daophot (at least some version) crashes on ATtach after OPtion. Expect crash on next ATtach.')
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
            commands += '\n\n'
        processor = DaophotOptOP()
        self.interact(commands, output_processor=processor)
        self.opt_processor = processor


    def find(self):
        pass

    # processors data access methods
    def get_pic_size(self):
        """returns tuple with (x,y) size of pic returned by 'attach' """
        return self.attach_processor.get_picture_size()

    def get_options(self):
        """returns dictionary of options: XX: 'nnn.dd'
           keys are two letter option names
           values are strings"""
        return self.opt_processor.get_options()

    def get_option(self, key):
        """returns pyraf option of key as float
           key will be truncated to 2 characters """
        return self.opt_processor.get_option(key)
