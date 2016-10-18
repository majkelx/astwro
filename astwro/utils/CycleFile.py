import os


class CycleFile(object):
    """
    Creates series of files with names containing counter, with symlink to newest one
    """
    counter = 0
    file = None
    filename_formatter = '{}{:03d}{}'
    symlink_formatter = '{}{}{}'
    file_mode = 'w'
    open_kwargs = None

    def __init__(self, path, basename, extension='', create_symlinks=True, symlink_suffix='_last', auto_close=True):
        """
        :param auto_close:
        :param str path: patch to the file, absolute or relative, can be empty string '' for current directory
        :param str basename: first part of file name before counter
        :param str extension:  part of filename after counter
        :param str create_symlinks: whether to create symlink to newest file
        :param str symlink_suffix:  part of suffix filename in place of counter value
        :param bool auto_close: close prev files on next_file nad destruction
        """
        self.path = path
        self.basename = basename
        self.extension = extension
        self.create_symlinks = create_symlinks
        self.symlink_suffix = symlink_suffix
        self.auto_close = auto_close
        pass

    def __del__(self):
        if self.auto_close and self.file is not None:
            self.file.close()

    def next_file(self, counter=None):
        if counter is None:
            counter = self.counter + 1
        self.counter = counter
        if self.auto_close and self.file is not None:
            self.file.close()
            self.file = None
        filename = self.filename_formatter.format(self.basename, counter, self.extension)
        filepath = os.path.join(self.path, filename)
        if self.open_kwargs is not None:
            self.file = open(filepath, self.file_mode, **self.open_kwargs)
        else:
            self.file = open(filepath, self.file_mode)
        if self.create_symlinks:
            symlname = self.symlink_formatter.format(self.basename, self.symlink_suffix, self.extension)
            symlpath = os.path.join(self.path, symlname)
            if os.path.exists(symlpath):
                os.remove(symlpath)
            os.symlink(filename, symlpath)
        return self.file
