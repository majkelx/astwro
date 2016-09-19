from .TmpDir import TmpDir
from .CycleFile import CycleFile


def tmpdir(use_exiting=None, prefix='astwro_tmp_', base_dir=None):
    """
    Creates instance of TmpDir which creates and keeps lifetime of temporary directory
    :param str use_existing:    If provided, instance will point to that directory and not delete it on destruct
    :param str prefix:          Prefix for temporary dir
    :param str base_dir:        Where to crate tem dir, in None system default is used
    :rtype: TmpDir
    """
    return TmpDir(use_exiting, prefix, base_dir)


def cyclefile(base_path, extension='', create_symlinks=True, symlink_suffix='_last', auto_close = True):
    """
    Creates CycleFile which can create series of files with names containing counter,
    with symlink to newest one
    :param str base_path: patch and part of file name before counter
    :param str extension:  part of filename after counter
    :param str create_symlinks: whether to create symlink to newest file
    :param str symlink_suffix:  part of suffix filename in place of counter value
    :param bool auto_close: close prev files on next_file nad destruction
    :rtype: CycleFile
    """
    return CycleFile(base_path=base_path, extension=extension, create_symlinks=create_symlinks,
                     symlink_suffix=symlink_suffix, auto_close=auto_close)
