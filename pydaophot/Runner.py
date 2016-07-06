import os
import shutil
from tempfile import mkdtemp
try:
    from StringIO import StringIO  # python2
except ImportError:
    from io import StringIO # python3
import subprocess as sp
from logging import *
from .OutputProviders import StreamKeeper, OutputProvider


class Runner(object):

    executable = None
    dir = None
    dir_is_tmp = False
    cfg = None
    commands = ''
    output = None
    # chain of 'lazy' output processors
    output_processor_chain = None
    stream_keeper = None

    def __init__(self, config=None):
        self.cfg = config
        self.stream_keeper = StreamKeeper()
        self.output_processor_chain = self.stream_keeper
        self.prepare_dir()


    def close(self):
        self.on_exit()

    def init_config_files(self, dir):
        pass

    def prepare_dir(self, dir=None, preserve_dir=False):
        if dir is None:
            dir = mkdtemp(prefix='pydaophot_tmp')
            debug('Using temp dir %s', dir)
            if not preserve_dir:
                self.dir_is_tmp = True
        self.dir = dir
        self.init_config_files(dir)

    def copy_to_working_dir(self, source, filename=None):
        dst = self.dir if filename is None else os.path.join(self.dir, filename)
        shutil.copy(source, dst)

    def link_to_working_dir(self, source, link_filename=None):
        if link_filename is None:
            link_filename = os.path.basename(source)
        os.symlink(source, os.path.join(self.dir, link_filename))

    def copy_from_working_dir(self, filename, dest='.'):
        shutil.copy(os.path.join(self.dir, filename), dest)

    def exist_in_working_dir(self, filename):
        return os.path.exists(os.path.join(self.dir, filename))

    def rm_from_working_dir(self, filename):
        try:
            os.remove(os.path.join(self.dir, filename))
        except OSError:
            pass

    def run(self):
        try:
            process = sp.Popen([self.executable],
                                    stdin=sp.PIPE,
                                    stdout=sp.PIPE,
                                    cwd=self.dir)
            info('STDIN:\n' + self.commands)
            self.output = process.communicate(self.commands)[0]
        except OSError as e:
            error('Check if executable: %s is in PATH, modify executable name/path in pydaophot.cfg', self.executable)
            raise e
        info('STDOUT:\n' + self.output)
        self.stream_keeper.stream = StringIO(self.output)

    def interact(self, std_in, output_processor=None):
        self.commands += std_in
        if not isinstance(output_processor, OutputProvider):
            raise TypeError('output_processor must OutputProvider subclass')
        output_processor.prev_in_chain = self.output_processor_chain
        self.output_processor_chain = output_processor
        return output_processor

    def on_exit(self):
        pass

