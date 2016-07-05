import os
import io
import shutil
from tempfile import mkdtemp
from subprocess import call
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
    commands = ''
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

    def close(self, exit_nicely = True):
        if exit_nicely:
            self.on_exit()
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
        if self.dir is None:
            self.prepare_dir()
        self.commands += 'EXIT\n'
        try:

            self.process = Popen([self.executable],
                                 stdin=PIPE,
                                 stdout=PIPE if self.read_std_out else None,
                                 stderr=STDOUT if self.read_std_err else None,
                                 cwd=self.dir
                                 )
        except OSError as e:
            error('Check if executable: %s is in PATH, modify executable name/path in pydaophot.cfg', self.executable)
            raise e

        self.fd_stdin = self.process.stdin.fileno()
        if self.read_std_out:
            stdoutsream = self.process.stdout
            if (isinstance(stdoutsream, file)):  # switch to modern io
                stdoutsream = io.open(stdoutsream.fileno())
            self.output_processor_chain = StreamKeeper(stdoutsream)
        # setting output pipes as nonblocking
        # for pipe in [self.process.stdout, self.process.stderr]:
        #     fd = pipe.fileno()
        #     flags = fcntl(fd, F_GETFL)
        #     fcntl(fd, F_SETFL, flags | os.O_NONBLOCK)

    def interact(self, std_in, output_processor=None):
        self.commands += std_in
        if self.read_std_out:  # add output processor into chain
            assert isinstance(output_processor, OutputProvider)
            output_processor.prev_in_chain = self.output_processor_chain
            self.output_processor_chain = output_processor
        return output_processor

    def on_exit(self):
        pass

