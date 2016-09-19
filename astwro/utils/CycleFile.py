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

    def __init__(self, base_path, extension='', create_symlinks=True, symlink_suffix='_last', auto_close=True):
        """
        :param auto_close:
        :param str base_path: patch and part of file name before counter
        :param str extension:  part of filename after counter
        :param str create_symlinks: whether to create symlink to newest file
        :param str symlink_suffix:  part of suffix filename in place of counter value
        :param bool auto_close: close prev files on next_file nad destruction
        """
        self.base_path = base_path
        self.extension = extension
        self.create_symlinks = create_symlinks
        self.symlink_suffix = symlink_suffix
        self.auto_close = auto_close
        pass

    def __del__(self):
        if self.auto_close and file is not None:
            self.file.close()

    def next_file(self, counter=None):
        if counter is None:
            counter = self.counter + 1
        self.counter = counter
        if self.auto_close and self.file is not None:
            self.file.close()
            self.file = None
        filename = self.filename_formatter.format(self.base_path, counter, self.extension)
        if self.open_kwargs is not None:
            self.file = open(filename, self.file_mode, **self.open_kwargs)
        else:
            self.file = open(filename, self.file_mode)
        if self.create_symlinks:
            syml_name = self.symlink_formatter.format(self.base_path, self.symlink_suffix, self.extension)
            if os.path.exists(syml_name):
                os.remove(syml_name)
            os.symlink(filename, syml_name)
        return self.file
