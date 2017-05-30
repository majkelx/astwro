# coding=utf-8
"""Greenstick's code form http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
encapsulated into class
"""

import sys


class ProgressBar(object):
    def __init__(self, total=100, prefix='', suffix='', decimals=1, bar_length=20, step=0, cleanup=True):
        """
        Create terminal progress bar 
        :param int total: total iterations (Int)
        :param str prefix: prefix string (Str)
        :param str suffix: suffix string (Str)
        :param int decimals: positive number of decimals in percent complete (Int)
        :param int bar_length: character length of bar (Int)
        :param int step: allows automatic progress increasing on parameter-less print_progress call
        :param bool cleanup: if true (default) erase progressbar when completed 
        """
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.bar_length = bar_length
        self.step = step
        self.iteration = 0
        self.cleanup = cleanup

    def print_progress(self, iteration=None):
        """
        Call in a loop to print terminal progress bar
        @params:
            iteration 
        """
        if iteration is None:
            iteration = self.iteration + self.step
        if iteration > self.total:
            iteration = self.total
        format_str = "{0:." + str(self.decimals) + "f}"
        percents = format_str.format(100 * (iteration / float(self.total)))
        filled_length = int(round(self.bar_length * iteration / float(self.total)))
        bar = '■' * filled_length + '·' * (self.bar_length - filled_length)
        stream = sys.stderr
        stream.flush()
        stream.write('\r%s [%s] %s%s %s' % (self.prefix, bar, percents, '%', self.suffix)),
        if iteration == self.total:
            if self.cleanup:
                self.clean_progress()
            else:
                stream.write('\n')
            stream.flush()
        self.iteration = iteration

    def clean_progress(self):
        n = len(self.prefix) + len(self.suffix) + self.bar_length + self.decimals + 10
        stream = sys.stderr
        stream.flush()
        stream.write('\r' + ' '*n + '\r'),
