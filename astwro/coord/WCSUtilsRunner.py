# coding=utf-8
from __future__ import absolute_import, division, print_function
from astwro.exttools import Runner

class WCSUtilsRunner(Runner):
    def __init__(self, translator=None):
        # base implementation of __init__ calls `_reset` also
        self.translator = translator
        super(WCSUtilsRunner, self).__init__()
    pass