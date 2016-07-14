from .TmpDir import TmpDir


def tmpdir(path=None, prefix='astwro_tmp_'):
    """
    Creates instance of TmpDir which creates and keeps livetime of temporary directory
    :param path:   If provided, instance will point to that directory and not delete it on destruct
    :param prefix: Prefix for temporary dir
    :return: instance of TmpDir
    """
    return TmpDir(path, prefix)
