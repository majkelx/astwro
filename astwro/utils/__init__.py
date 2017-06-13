from .TmpDir import TmpDir
from .CycleFile import CycleFile
from .ProgressBar import ProgressBar


def tmpdir(use_existing=None, prefix='astwro_tmp_', base_dir=None):
    """
    Creates instance of TmpDir which creates and keeps lifetime of temporary directory
    :param str use_existing:    If provided, instance will point to that directory and not delete it on destruct
    :param str prefix:          Prefix for temporary dir
    :param str base_dir:        Where to crate tem dir, in None system default is used
    :rtype: TmpDir
    """
    return TmpDir(use_existing, prefix, base_dir)


def cyclefile(path, basename, extension='', create_symlinks=True, symlink_suffix='_last', auto_close=True):
    """
    Creates CycleFile which can create series of files with names containing counter,
    with symlink to newest one
    :param str path: patch to the file, absolute or relative, can be empty string '' for current directory
    :param str basename: first part of file name before counter
    :param str extension:  part of filename after counter
    :param str create_symlinks: whether to create symlink to newest file
    :param str symlink_suffix:  part of suffix filename in place of counter value
    :param bool auto_close: close prev files on next_file nad destruction
    :rtype: CycleFile
    """
    return CycleFile(path=path, basename=basename, extension=extension, create_symlinks=create_symlinks,
                     symlink_suffix=symlink_suffix, auto_close=auto_close)


def progressbar(total=100, prefix='', suffix='', decimals=1, bar_length=20, step=0):
    """
    Creates Text console progress bar object, print progress using print_progress() method
    :param int total: total iterations (Int)
    :param str prefix: prefix string (Str)
    :param str suffix: suffix string (Str)
    :param int decimals: positive number of decimals in percent complete (Int)
    :param int bar_length: character length of bar (Int)
    :param int step: allows automatic progress increasing on parameter-less print_progress call
    :rtype:ProgressBar
    """
    return ProgressBar(total=total, prefix=prefix, suffix=suffix, decimals=decimals, bar_length=bar_length, step=step)
