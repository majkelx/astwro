import os
import shutil
from tempfile import mkdtemp
from subprocess32 import Popen, PIPE, STDOUT
# from fcntl import fcntl, F_GETFL, F_SETFL
from logging import *
from .OutputProviders import StreamKeeper, OutputProvider

MAX_BUF = 1000


class Runner(object):

    executable = None
    process = None
    dir = None
    dir_is_tmp = False
    cfg = None
    # whether output from executable is captured
    read_std_out = False
    read_std_err = False
    # pipes file descriptors
    fd_stdin  = None
    fd_stdout = None
    # chain of 'lazy' output processors
    output_processor_chain = None

    def __init__(self, config=None):
        self.cfg = config

    def close(self):
        if self.process is not None:
            self.process.terminate()
        if self.dir_is_tmp:
            shutil.rmtree(self.dir)
        self.process = None
        self.dir = None
        self.dir_is_tmp = False

    def init_config_files(self, dir):
        pass

    def prepare_dir(self, dir=None, preserve_dir=False):
        if dir is None:
            dir = mkdtemp(prefix='pydaophot_tmp')
            if not preserve_dir:
                self.dir_is_tmp = True
        self.dir = dir
        self.init_config_files(dir)

    def copy_to_working_dir(self, source):
        shutil.copy(source, self.dir)

    def link_to_working_dir(self, source, link_filename=None):
        if link_filename is None:
            link_filename = os.path.basename(source)
        os.symlink(source, os.path.join(self.dir, link_filename))

    def copy_from_working_dir(self, filename, dest='.'):
        shutil.copy(os.path.join(self.dir, filename), dest)

    def run(self):
        if self.dir is None:
            self.prepare_dir()
        self.process = Popen([self.executable],
                             stdin=PIPE,
                             stdout=PIPE if self.read_std_out else None,
                             stderr=STDOUT if self.read_std_err else None,
                             cwd=self.dir)
        self.fd_stdin  = self.process.stdin.fileno()
        if self.read_std_out:
            self.output_processor_chain = StreamKeeper(self.process.stdout)
        # setting output pipes as nonblocking
        # for pipe in [self.process.stdout, self.process.stderr]:
        #     fd = pipe.fileno()
        #     flags = fcntl(fd, F_GETFL)
        #     fcntl(fd, F_SETFL, flags | os.O_NONBLOCK)

    def interact(self, std_in=None, output_processor=None):
        if std_in is not None:
            os.write(self.fd_stdin, std_in)
            debug('IN:\n%s', std_in)
        if self.read_std_out:  # add output processor into chain
            assert output_processor is not None
            assert isinstance(output_processor, OutputProvider)
            output_processor.prev_in_chain = self.output_processor_chain
            self.output_processor_chain = output_processor
        return output_processor
        # try:
        #     std_outs = self.process.communicate(std_in, 1000)
        # except TimeoutExpired as e:
        #     std_outs = e.output, ''
        #     pass


    @staticmethod
    def _try_read_pipe(fd):
        try:
            return os.read(fd, MAX_BUF)
        except OSError:
            return ''

