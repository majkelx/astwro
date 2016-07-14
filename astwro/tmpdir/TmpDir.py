import shutil
from tempfile import mkdtemp


class TmpDir(object):
    """
    instances of TmpDir keeps track and lifetime of temporary directory
    """
    path = None
    dir_is_tmp = True
    _prefix = ''

    def __init__(self, path=None, prefix='astwro_tmp_'):
        """
        :param path:   If provided, instance will point to that directory and not delete it on destruct
        :param prefix: Prefix for temporary dir
        """
        self._prefix = prefix
        if path is None:
            self.path = mkdtemp(prefix=prefix)
            self.dir_is_tmp = True
        else:
            self.path = path
            self.dir_is_tmp = False


    def __del__(self):
        self._rm_dir()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._rm_dir()

    def __repr__(self):
        return ('Tmp dir:' if self.dir_is_tmp else 'Ext dir:') + (self.path if self.path else 'none')

    def __str__(self):
        return self.path

    def __deepcopy__(self, memo):
        cls = self.__class__
        new = cls.__new__(cls)
        memo[id(self)] = new
        if self.dir_is_tmp:
            new.__init__(prefix=self._prefix)
            shutil.rmtree(new.path)
            shutil.copytree(self.path, new.path, symlinks=True)
        else:
            new.__init__(path=self.path)
        return new

    def _rm_dir(self):
        """Deletes working dir with all content."""
        if self.dir_is_tmp:
            try:
                shutil.rmtree(self.path)
            except OSError as ex:
                pass
