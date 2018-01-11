# coding=utf-8
from __future__ import absolute_import, division, print_function
import matplotlib.pyplot as plt



__metaclass__ = type

import numpy as np

from ..fnpeaks import FNpeaks

class TestFNpeaks:

    def setup_class(self):
        self.N = 10
        self.M = 1000
        self.lc = np.random.normal(10, 0.5, (self.N, self.M))
        self.lc_e = np.random.normal(0, 0.1, (self.N, self.M))
        self.hjd = 10000.0 + np.sort(np.random.uniform(0, 200, self.M))
        for i in range(self.N):
            self.lc[i] += (1.0 * i / self.N) * np.sin((self.hjd + i)/20.0)

        evens = np.array(np.arange(self.M) & 1, dtype=bool)
        self.filters = {
            'A': evens,
            'B': ~evens
        }

    def test_simple(self):
        runner = FNpeaks(self.hjd, self.lc)
        res = runner(5, periodogram=False)
        assert (res is not None)
        assert (len(res.peaks) == 10)
        assert (res.power is None)

    def test_with_periodogram(self):
        runner = FNpeaks(self.hjd, self.lc)
        res = runner(5, periodogram=True)
        assert (res is not None)
        assert (len(res.power) > 0)
        assert (len(res.peaks) == 10)

    def test_filters(self):
        runner = FNpeaks(self.hjd, self.lc, filtermasks=self.filters)
        res = runner(5, periodogram=False, filter='B')
        assert (isinstance(res, dict))
        assert (len(res['B'].peaks) == 10)
        assert (res['B'].power is None)

    def test_filters_errors_periodigrams_ids(self):
        runner = FNpeaks(self.hjd, self.lc, self.lc_e, filtermasks=self.filters, ids=np.arange(self.N)*10)
        res = runner(6, filter='B')
        assert (isinstance(res, dict))
        assert (len(res['B'].peaks) == 10)
        assert (res['B'].power is None)
