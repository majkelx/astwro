# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import shutil
from tempfile import mkdtemp
from copy import deepcopy


class TmpDir(object):
    """
    instances of TmpDir keeps track and lifetime of temporary directory
    """
    path = None
    dir_is_tmp = True
    _prefix = ''
    _base = None

    def __init__(self, use_existing=None, prefix='astwro_tmp_', base_dir=None):
        """
        :param str use_existing:    If provided, instance will point to that directory and not delete it on destruct
        :param str prefix:          Prefix for temporary dir
        :param str base_dir:        Where to crate tem dir, in None system default is used
        """
        self._prefix = prefix
        self._base = base_dir
        if use_existing is None:
            self.path = mkdtemp(prefix=prefix, dir=base_dir)
            self.dir_is_tmp = True
        else:
            self.path = use_existing
            self.dir_is_tmp = False

    def clone(self):
        return deepcopy(self)

    def __del__(self):
        self._rm_dir()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
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
            new.__init__(prefix=self._prefix, base_dir=self._base)
            shutil.rmtree(new.path)
            shutil.copytree(self.path, new.path, symlinks=True)
        else:
            new.__init__(use_existing=self.path)
        return new

    def _rm_dir(self):
        """Deletes working dir with all content."""
        if self.dir_is_tmp:
            try:
                shutil.rmtree(self.path)
            except OSError:
                pass
