import os
import sys
import shutil
from copy import deepcopy
try:
    # noinspection PyCompatibility
    from StringIO import StringIO  # python2
except ImportError:
    from io import StringIO  # python3
import subprocess as sp
try:
    # noinspection PyUnresolvedReferences
    from subprocess import TimeoutExpired  # python 3 only
except ImportError:
    pass
from logging import *
from .OutputProviders import StreamKeeper, OutputProvider
from astwro.utils import tmpdir, TmpDir


class Runner(object):

    executable = None
    dir = None
    output = None
    stderr = None
    __cfg = None
    __commands = ''
    __process = None
    # chain of 'lazy' output processors
    __output_processor_chain = None
    __stream_keeper = None

    def __init__(self, config=None, dir=None):
        """
        :param config:ConfigParser
        :param dir: path name or TmpDir object, in not provided new temp dir will be used
        """
        self.__cfg = config
        self.__stream_keeper = StreamKeeper(runner=self)
        self.__output_processor_chain = self.__stream_keeper
        self._prepare_dir(dir)

    def _reset(self):
        """Resets runner without cleaning/changing working dir
           allows execution of new sequence in same dir and files"""
        self.__process = None
        self.__stream_keeper.stream = None
        self.output = None
        self.stderr = None
        self.__commands = ''
        self.__output_processor_chain = self.__stream_keeper

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        new.executable = self.executable
        new.__cfg = self.__cfg
        new.output = self.output
        new.stderr = self.stderr
        new.__commands = self.__commands
        new.dir = deepcopy(self.dir, memo)
        new.__output_processor_chain = deepcopy(self.__output_processor_chain, memo)
        new.__stream_keeper = memo[id(self.__stream_keeper)]
        return new

    def clone(self):
        """Clones runner (before or after run).
        If 'self' have created working dir itself,  all clones will have own working dirs
         copied from 'self'. """
        return deepcopy(self)

    def close(self):
        """Cleans things up."""
        self._on_exit()
        self.dir = None

    def _init_workdir_files(self, dir):
        pass

    def _prepare_dir(self, dir=None, init_files=True):
        if dir is None:
            dir = tmpdir(prefix='pydaophot_tmp')
            info('Using temp dir %s', dir)
        elif isinstance(dir, str):
            dir = tmpdir(use_exiting=dir)
        elif not isinstance(dir, TmpDir):
            raise TypeError('dir must be either: TmpDir, str, None')
        self.dir = dir
        if init_files:
            self._init_workdir_files(dir)

    def copy_to_working_dir(self, source, filename=None):
        """Copies source file to runner's working dir under name filename or the same
        as original if filename is None. Overwrites existing file."""
        dst = self.dir.path if filename is None else os.path.join(self.dir.path, filename)
        shutil.copy(source, dst)

    def link_to_working_dir(self, source, link_filename=None):
        """Creates symlink in runner's working dir under name filename or the same
        as original if filename is None. Overwrites existing file."""
        source = self.expand_default_file_path(source)
        if not os.path.isfile(source):
            raise IOError('Source file {} not found'.format(source))
        if link_filename is None:
            link_filename = os.path.basename(source)
        dest = os.path.join(self.dir.path, link_filename)
        try:
            os.remove(dest)
        except OSError:
            pass
        os.symlink(source, dest)

    def copy_from_working_dir(self, filename, dest='./'):
        """Copies file: filename from runner's working dir. Overwrites existing file."""
        shutil.copy(os.path.join(self.dir.path, filename), dest)

    def link_from_working_dir(self, filename, dest='./'):
        """Creates symlink in dest of file from runner's working dir.
        dest can be either file path for new symlink or directory.
        In second case name of symlink will be filename. Overwrites existing file."""
        if os.path.basename(dest) == '':
            dest = os.path.join(dest, filename)
        try:
            os.remove(dest)
        except OSError:
            pass
        os.symlink(os.path.join(self.dir.path, filename), dest)

    def file_from_working_dir(self, filename):
        """Simply adds working dir path into filename"""
        return os.path.join(self.dir.path, filename)

    def exists_in_working_dir(self, filename):
        """Checks for filename existence in runner's working dir"""
        return os.path.exists(os.path.join(self.dir.path, filename))

    def rm_from_working_dir(self, filename):
        """Removes (if exists) file filename from runner's working dir"""
        try:
            os.remove(os.path.join(self.dir.path, filename))
        except OSError:
            pass

    @staticmethod
    def expand_default_file_path(path):
        """Expand user ~ directory and finds absolute path. Utility not
        very useful externally..."""
        if path is None:
            path = ''
        else:
            path = os.path.abspath(os.path.expanduser(path))
        return path

    def _pre_run(self, wait):
        pass

    def run(self, wait=True):
        self._pre_run(wait)
        try:
            self.__process = sp.Popen([self.executable],
                                      stdin=sp.PIPE,
                                      stdout=sp.PIPE,
                                      stderr=sp.PIPE,
                                      cwd=self.dir.path)
        except OSError as e:
            error('Check if executable: %s is in PATH, modify executable name/path in pydaophot.cfg', self.executable)
            raise e
        info('STDIN:\n' + self.__commands)
        if wait:
            self.__communicate(self.__commands)
        else:
            if sys.version_info[0] > 2:  # python 3 has timeout in communicate
                try:
                    self.__communicate(self.__commands, timeout=0.01)
                except TimeoutExpired:
                    pass
            else:  # python 2 - write directly to stdin
                self.__process.stdin.write(self.__commands)

    def is_ready_to_run(self):
        """
        Returns True if there are some commands waiting for run but process was not started yet
        :return: bool
        """
        return self.__commands and self.__process is None

    def is_running(self):
        """
        Returns if runner is running: executable was started in async mode, and no output collected yet.
         Note, that even if executable has finished, output will not be collected and is_running will
          return True until user asks for results or call wait_for_results()
        :return: bool
        """
        return self.__process is not None and self.output is None

    def is_after_run(self):
        """
        Returns True if process has finished and output is available
        :return: bool
        """
        return self.output is not None

    def wait_for_results(self):
        if self.is_running():
            self.__communicate()
        if self.is_ready_to_run():
            self.run(wait=True)

    def __communicate(self, inpt=None, timeout=None):
        i = inpt.encode(encoding='ascii') if inpt else None
        o, e = self.__process.communicate(i, timeout=timeout) if timeout else self.__process.communicate(i)
        self.output = o.decode('ascii')
        self.stderr = e.decode('ascii')
        info('STDOUT:\n' + self.output)
        self.__stream_keeper.stream = StringIO(self.output)

    def _get_ready_for_commands(self):
        if self.is_running():
            self.wait_for_results()
        if self.is_after_run():
            self._reset()

    def _insert_processing_step(self, std_in, output_processor=None):
        self._get_ready_for_commands()

        self.__commands += std_in
        if output_processor is not None:
            if not isinstance(output_processor, OutputProvider):
                raise TypeError('output_processor must OutputProvider subclass')
            output_processor._prev_in_chain = self.__output_processor_chain
            self.__output_processor_chain = output_processor
        return output_processor

    def _on_exit(self):
        pass
