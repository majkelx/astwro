# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import shutil
import hashlib
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

#from . import logger as module_logger
from .logger import logger as module_logger
from .OutputProviders import StreamKeeper, OutputProvider
from .config import dao_config
from astwro.utils import tmpdir, TmpDir


class Runner(object):
    """ Base class for specyfic runners. Maintains underlying process lifetime, 
    communication with process (streams, output processors chain), runner dir etc... """

    class RunnerException(Exception):
        """Exceptions raised by `Runner` nad subclasses"""
        pass

    class ExitError(RunnerException):
        """Exceptions raised when underlying process returns error code on exit"""
        def __init__(self, message, code):
            super(Runner.ExitError, self).__init__(message)
            self.code = code

    class RunnerValueError(ValueError, RunnerException):
        pass

    class RunnerTypeError(TypeError, RunnerException):
        pass

    raise_on_nonzero_exitcode = True
    preserve_process = False  # not implemented

    def __init__(self, dir=None, batch=False):
        """
        :param dir: path name or TmpDir object, in not provided new temp dir will be used
        :param bool batch:      whether Daophot have to work in batch mode.         
        """
        self.logger = module_logger.getChild(type(self).__name__)
        self.executable = None
        self.batch_mode = batch
        self.__stream_keeper = None

        self._prepare_dir(dir)
        self._reset()

    def _reset(self):
        """Resets runner without cleaning/changing runner dir
           allows execution of new sequence in same dir and files"""
        self.output = None
        self.stderr = None
        self.returncode = None
        self.__process = None
        self.__commands = ''
        self.ext_output_files = set()

        if self.__stream_keeper is not None:
            self.__stream_keeper.stream = None # new chain containing only old StreamKeeper
        else:
            self.__stream_keeper = StreamKeeper(runner=self)   # new chain containing new StreamKeeper
        self.__processors_chain_last = self.__stream_keeper
        self.__processors_chain_first = None

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new

        new.__stream_keeper = None
        new._reset()
        new.logger = self.logger
        new.executable = self.executable
        # new.output = self.output
        # new.stderr = self.stderr
        # new.returncode = self.returncode
        new.batch_mode = self.batch_mode
        # new.__process = None
        # new.__commands = self.__commands
        # new.ext_output_files = set()

        # new.__processors_chain_last  = deepcopy(self.__processors_chain_last, memo) # copy chain
        # new.__processors_chain_first = memo[id(self.__processors_chain_first)]  # find StreamKeeper in copied chain
        # new.__stream_keeper          = memo[id(self.__stream_keeper)]  # find StreamKeeper in copied chain

        new.dir = deepcopy(self.dir, memo)
        return new

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def clone(self):
        """Clones runner (before or after run).
        If 'self' have created runner dir itself,  all clones will have own runner dirs
         copied from 'self'. """
        return deepcopy(self)

    def close(self):
        """Cleans things up."""
        self._on_exit()
        self.dir = None

    @property
    def mode(self):
        """Either "normal" or "batch". In batch mode, commands are not executed but collected
        on execution queue, then run together, in single process, one by one, 
        triggered by :py:meth:`~Runner.run()` method"""
        return 'batch' if self.batch_mode else  'normal'

    @mode.setter
    def mode(self, m):
        if m.lowercase() == 'batch':
            self.batch_mode = True
        elif m.lowercase() == 'normal':
            self.batch_mode = False
        else:
            raise Runner.RunnerValueError('mode have to be either "normal" or "batch"')

    def _init_workdir_files(self, dir):
        pass

    def _update_executable(self, exe):
        """Find exe key in configuration and set as Runner executable"""
        if self.executable is None:
            self.executable = os.path.expanduser(dao_config().get('executables', exe))


    def _prepare_dir(self, dir=None, init_files=True):
        if dir is None:
            dir = tmpdir(prefix='pydaophot_tmp')
        elif isinstance(dir, str):
            dir = tmpdir(use_existing=dir)
        elif not isinstance(dir, TmpDir):
            raise Runner.RunnerTypeError('dir must be either: TmpDir object, str, None')
        self.dir = dir
        if init_files:
            self._init_workdir_files(dir)

    def copy_to_runner_dir(self, source, filename=None):
        """Copies source file to  runner dir under name filename or the same
        as original if filename is None. Overwrites existing file."""
        dst = self.dir.path if filename is None else os.path.join(self.dir.path, filename)
        shutil.copy(source, dst)

    def link_to_runner_dir(self, source, link_filename=None):
        # type: (str, str) -> None
        """Creates symlink in  runner dir under name filename or the same
        as original if filename is None. Overwrites existing link.
        :param source: file patch  
        :param link_filename: worker dir link name, default: same as filename part of source"""
        source = self.expand_path(source)
        # if not os.path.isfile(source):
        #     raise IOError('Source file {} not found'.format(source))
        if link_filename is None:
            link_filename = os.path.basename(source)
        dest = os.path.join(self.dir.path, link_filename)
        try:
            os.remove(dest)
        except OSError:
            pass
        os.symlink(source, dest)

    def copy_from_runner_dir(self, filename, dest='./'):
        """Copies file: filename from runner dir. Overwrites existing file."""
        shutil.copy(os.path.join(self.dir.path, filename), dest)

    def link_from_runner_dir(self, filename, dest='./'):
        """Creates symlink in dest of file from runner dir.
        dest can be either file path for new symlink or directory.
        In second case name of symlink will be filename. Overwrites existing file."""
        if os.path.basename(dest) == '':
            dest = os.path.join(dest, filename)
        try:
            os.remove(dest)
        except OSError:
            pass
        os.symlink(os.path.join(self.dir.path, filename), dest)

    def file_from_runner_dir(self, filename):
        """Simply adds runner dir path into filename"""
        return os.path.join(self.dir.path, filename)

    def exists_in_runner_dir(self, filename):
        """Checks for filename existence in runner dir"""
        return os.path.exists(os.path.join(self.dir.path, filename))

    def rm_from_runner_dir(self, filename):
        """Removes (if exists) file filename from runner dir"""
        try:
            os.remove(os.path.join(self.dir.path, filename))
        except OSError:
            pass

    @staticmethod
    def expand_path(path):
        """Expand user ~ directory and finds absolute path."""
        if path is None:
            path = ''
        else:
            path = os.path.abspath(os.path.expanduser(path))
        return path

    def absolute_path(self, path):
        """Returns absolute path for filepath parameter, if :arg:path contain filename only, runner dir is added"""
        if os.path.basename(path) != path:  # not in runner directory
            absolute = self.expand_path(path)
        else:
            absolute = os.path.join(self.dir.path, path)
        return absolute


    @staticmethod
    def _runner_dir_file_name(filepath='', prefix='', suffix='', signature=None):
        # type: (str, str, str, str) -> str
        """Generates name used in Runner local dir for filepath

        Files processed by underlying process are always in it's working directory
          (runner directory). For files from other location in filesystem, copies
          or links in runner directory are maintained. Names of that files are prefixed
          with hash (shortened) of filepath to avoid collisions.
        """
        if signature is None:
            signature = filepath

        return prefix + str(hashlib.md5(str(signature)).hexdigest())[:6] + '_' + os.path.basename(filepath) + suffix

    def _prepare_output_file(self, data):
        # type: (str) -> (str, str)
        return self._prepare_io_file(data, output=True)

    def _prepare_input_file(self, path):
        # type: ([str,) -> (str, str)
        return self._prepare_io_file(path, output=False)

    def _prepare_io_file(self, path, output):
        # type: (str, bool) -> (str, str)
        """ make link for non-local input files in runner dir, gen runner dir filename """
        if not path:
            return '',''
        if os.path.dirname(os.path.abspath(path)) == self.dir.path: # path to runner dir provided, cut it
            path = os.path.basename(path)
        if os.path.basename(path) != path:  # not in runner directory
            absolute = self.expand_path(path)
            local = self._runner_dir_file_name(absolute)
            if output:
                # add to list of files to update after run
                self.ext_output_files.add(absolute)
            elif absolute not in self.ext_output_files:
                self.link_to_runner_dir(absolute, local)
                self.logger.debug("Linking input file into runner directory: {} <- {}".format(local, absolute))
        else:
            absolute = os.path.join(self.dir.path, path)
            local = path
        if output:
            # remove runner dir file if exist
            self.rm_from_runner_dir(local)

        return local, absolute

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
            self.logger.error(
                'Executable: %s is expected in PATH, configure executable name/path in ~/pydaophot.cfg e.g.',
                self.executable)
            raise e
        self.logger.debug('STDIN:\n' + self.__commands)
        if wait:
            self.__communicate(self.__commands)
        else:
            if sys.version_info[0] > 2:  # python 3 has timeout in communicate
                try:
                    self.__communicate(self.__commands, timeout=0.01)
                except TimeoutExpired:
                    pass
            else:  # python 2 - write directly to stdin and close it to flush end generate EOF
                self.__process.stdin.write(self.__commands)
                self.__process.stdin.close()
                self.__process.stdin = None

    def is_ready_to_run(self):
        """
        Returns True if there are some commands waiting for run but process was not started yet
        :return: bool
        """
        return self.__commands and self.__process is None

    @property
    def running(self):
        """
        Returns if runner is running: executable was started in async mode, and no output collected yet.
         Note, that even if executable has finished, output will not be collected and is_running will
          return True until user asks for results or call wait_for_results()
        :return: bool
        """
        return self.__process is not None and self.output is None

    def has_finished_run(self):
        """
        Returns True if process has finished and output is available
        :return: bool
        """
        return self.output is not None

    def wait_for_results(self):
        if self.running:
            self.__communicate()
        if self.is_ready_to_run():
            self.run(wait=True)

    def __communicate(self, inpt=None, timeout=None):
        i = inpt.encode(encoding='ascii') if inpt else None
        o, e = self.__process.communicate(i, timeout=timeout) if timeout else self.__process.communicate(i)
        self.output = o.decode('ascii')
        self.stderr = e.decode('ascii')
        self.logger.debug('STDOUT:\n' + self.output)
        self.__stream_keeper.stream = StringIO(self.output)
        self.returncode = self.__process.returncode
        if self.returncode < 0:
            self.logger.warning('{} process finished with error code {}'.format(self.executable, self.returncode))
            if self.raise_on_nonzero_exitcode:
                raise Runner.ExitError('Execution failed, exit code {}'.format(self.returncode), self.returncode)
        # copy results - output files from runners directory to user specified path
        for f in self.ext_output_files:
            self.copy_from_runner_dir(self._runner_dir_file_name(f), f)


    def _get_ready_for_commands(self):
        if self.running:
            self.wait_for_results()  # if running wait
        if self.has_finished_run():  # if was running reset and get ready for new process
            self._reset()

    def _insert_processing_step(self, std_in, output_processor=None, on_beginning=False):
        if on_beginning:
            self.__commands = std_in + self.__commands
        else:
            self.__commands += std_in
        if output_processor is not None:
            if not isinstance(output_processor, OutputProvider):
                raise Runner.RunnerTypeError('output_processor must OutputProvider subclass')
            output_processor.logger = self.logger
            #  chain organisation:
            # [stream_keeper]<-[processors_chain_first]<-[]<-[]<-[processors_chain_last]
            if on_beginning:
                output_processor._prev_in_chain = self.__stream_keeper
                if self.__processors_chain_first is not None:
                    self.__processors_chain_first._prev_in_chain = output_processor
                self.__processors_chain_first = output_processor
            else:
                output_processor._prev_in_chain = self.__processors_chain_last
                self.__processors_chain_last = output_processor
                if self.__processors_chain_first is None:
                    self.__processors_chain_first = output_processor
        return output_processor

    def _on_exit(self):
        pass
