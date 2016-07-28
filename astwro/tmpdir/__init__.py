from .TmpDir import TmpDir


def tmpdir(use_exiting=None, prefix='astwro_tmp_', base_dir=None):
    """
    Creates instance of TmpDir which creates and keeps lifetime of temporary directory
    :param str use_existing:    If provided, instance will point to that directory and not delete it on destruct
    :param str prefix:          Prefix for temporary dir
    :param str base_dir:        Where to crate tem dir, in None system default is used
    """
    return TmpDir(use_exiting, prefix, base_dir)
