import os
from logging import *
from .Runner import Runner
from .config import get_package_config_path
from .OutputProviders import *

class DPRunner(Runner):
    daophotopt = None
    photoopt = None
    # output processors
    OPtion_result = None
    ATtach_result = None
    FInd_result = None

    def __init__(self, config = None, daophotopt=None, photoopt=None):
        Runner.__init__(self, config)
        self.executable = os.path.expanduser(config.get('executables', 'daophot'))
        self.daophotopt = daophotopt if daophotopt is not None else os.path.join(get_package_config_path(),'daophot.opt')
        self.photoopt   = photoopt   if photoopt   is not None else os.path.join(get_package_config_path(),'photo.opt')

        self.OPtion_result = DPOP_OPtion()
        self.interact('', output_processor=self.OPtion_result)

    def on_exit(self):
        pass

    def init_config_files(self, dir):
        Runner.init_config_files(self, dir)
        self.copy_to_working_dir(os.path.join(get_package_config_path(), 'daophot.opt'))
        self.copy_to_working_dir(os.path.join(get_package_config_path(), 'photo.opt'))

    def create_apertures_file(self, apertures, IS, OS):
        """Creates photo.opt in daophot working dir
            :arg apertures -- list of apertures A1,A2... e.g. [6.0,8.0,12.0]
            :arg IS -- inner radius of sky annulus
            :arg OS -- outer radius of sky annulus
            """
        assert len(apertures) > 0 and len(apertures) < 13
        self.rm_from_working_dir('photo.opt')
        with open(os.path.join(self.dir,'photo.opt'), 'w') as f:
            f.write(''.join('A{:1X}={:.2f}\n'.format(n+1, v) for n,v in zip(range(len(apertures)), apertures)))
            f.write('IS={:.2f}'.format(IS))
            f.write('OS={:.2f}'.format(OS))

    # daophot commands
    def ATtach(self, image_file):
#        self.link_to_working_dir(image_file, 'i.fits')
        self.copy_to_working_dir(image_file, 'i.fits')
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

    def FInd(self, frames_av = 1, frames_sum = 1, positions_file='i.coo'):
        if self.ATtach_result is None:
            raise Exception('No imput file attached, call ATttache first.')
        self.rm_from_working_dir(positions_file)
        commands = 'FIND\n{},{}\n{}\nyes\n'.format(frames_av, frames_sum, positions_file)
        processor = DpOp_FInd()
        self.interact(commands, output_processor=processor)
        self.FInd_result = processor
        return processor

    # # processors data access methods
    # def get_pic_size(self):
    #     """returns tuple with (x,y) size of pic returned by 'attach' """
    #     return self.attach_processor.get_picture_size()
    #
    # def get_options(self):
    #     """returns dictionary of options: XX: 'nnn.dd'
    #        keys are two letter option names
    #        values are strings"""
    #     return self.opt_processor.get_options()
    #
    # def get_option(self, key):
    #     """returns pyraf option of key as float
    #        key will be truncated to 2 characters """
    #     return self.opt_processor.get_option(key)
