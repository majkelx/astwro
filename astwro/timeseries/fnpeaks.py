# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef

from os.path import join
import numpy as np
from astropy.table import Table

from astwro.utils import TmpDir
from astwro.pydaophot.Runner import Runner
from astwro.phot.io import write_lc, write_lc_filters


class Peak(object):
    """
    Peak description.

    Parameters
    ----------
    freq : float
    period : float
    power : float
    sn : float
        Signal to noise of peak
    """
    def __init__(self, freq, period, power, sn):
        self.freq = freq
        self.period = period
        self.power = power
        self.sn = sn


class FNpeaksResult(object):
    """
    Results of fnpeak call.

    Returned by `~astwro.timeseries.FNpeaks`.

    Attributes
    ----------
    power : `~numpy.ndarray`
        Power of signal in frequencies, use `~astwro.timeseries.FNpeaks.freq` method for i-th frequency
    peaks : list of `~astwro.timeseries.Peak`
        List of most prominent peaks returned by fnpeaks (*.max file)
        notes).

    """
    def __init__(self):
        self.power = None
        self.peaks = None
        self.lc = None
        self.lc_e = None
        self.hjd = None
        self.freq_range = (0.0, 0.0)
        self.freq_step = 0.0

    @property
    def frequencies(self):
        return np.arange(self.freq_range[0], self.freq_range[1], self.freq_step)

    @property
    def periods(self):
        return 1.0 / np.arange(self.freq_range[0], self.freq_range[1], self.freq_step)


class FNpeaks(Runner):
    """
    `fnpeaks` runner

    Object of this class maintains single process of `fnpeaks` and it's working directory.

    Parameters
    ----------
    hjd : `~numpy.ndarray`
        Heliocentric julian days for observations (second dimension of lc)
    lc : `~numpy.ndarray`
        2D NxM array-like with light curves. N stars, M observations
    lc_e : `~numpy.ndarray`, optional
        Standart deviations of `lc`
    filtermasks : dict, optional
        Keys are filters, values are boolean masks for second dimension of `lc` with masks of filter
    start_freq : float
        Start frequency to scan (1/day)
    end_freq : float
        End frequency to scan (1/day)
    step_freq : float
        Frequency step
    ids : array-like:
        1D N element array with numerical ids of stars for filenames generation
    dir : str, optional
        Path of directory used for fnpeaks input output. If not provided temporary dir will be used
        and deleted on destructor.
    """

    def __init__(self, hjd, lc, lc_e=None, filtermasks=None,
                 start_freq=0.0001, end_freq=40.0001, step_freq=0.0001,
                 ids=None, dir=None):
        super(FNpeaks, self).__init__(dir=dir)
        self.hjd = hjd
        if lc.ndim == 1:
            self.lc = lc.reshape((1, lc.size))
        else:
            self.lc = lc
        if lc_e is not None and lc_e.ndim == 1:
            self.lc_e = lc_e.reshape((1, lc_e.size))
        else:
            self.lc_e = lc_e
        self.filtermasks = filtermasks
        self.start_freq = start_freq
        self.end_freq = end_freq
        self.step_freq = step_freq
        self.start_freq = start_freq
        self.ids = ids
        self._update_executable('fnpeaks')

    def __call__(self, star, filter=None, periodogram=False):
        """
        Runs fnpeaks for specified star(s)

        Parameters
        ----------
        star : long or array-like
            Stars(s) to process, position index in `~astwro.timeseries.FNpeaks.lc`
        filter : list of str
           If `~astwro.timeseries.FNpeaks.filtermasks` specified, selects filters. None means: all filters.
        periodogram : bool
            Whether to generate power spectral density estimates
        """
        # TODO reuse saved files
        if isinstance(star, int):
            star = [star]
        lc = self.lc[star]
        lc_e = None
        if self.lc_e is not None:
            lc_e = self.lc_e[star]
        ids = None
        if self.ids is not None:
            ids = self.ids[star]
        else:
            ids = star

        if self.filtermasks is None:
            write_lc(self.hjd, lc, lc_e, ids, 0.0,
                     prefix=join(self.dir.path, 'lc_'), suffix='.diff')
        else:
            if filter is None:
                filter = [f for f in self.filtermasks]
            write_lc_filters(self.filtermasks, filter, self.hjd, lc, lc_e, ids, 0.0,
                             prefix=join(self.dir.path, 'lc_'), suffix='.diff')
        ret = []
        for s in star:
            r = None
            if self.filtermasks is None:
                r = self._runfnpeaks(s, None, periodogram)
            else:
                r = {}
                for f in filter:
                    r[f] = self._runfnpeaks(s, f, periodogram)
            ret.append(r)
        if len(ret) == 1:
            ret = ret[0]
        return ret

    def freq(self, i):
        """
        Returns i-th frequency(ies)
        """
        return self.start_freq + i * self.step_freq

    def period(self, i):
        """
        Returns i-th period(s)
        """
        return 1.0 / self.freq(i)

    def _runfnpeaks(self, star_pos, filter, periodogram):
        if self.ids is not None:
            star = np.array(self.ids)[star_pos]
        else:
            star = star_pos
        if filter is None:
            fname = 'lc_{:05d}'.format(star)
        else:
            fname = 'lc_{:05d}_{}'.format(star, filter)
        if periodogram:
            self.arguments = ['-f']
        else:
            self.arguments = []
        self.arguments += [fname+'.diff']
        self.arguments += ['{:f}'.format(x) for x in [self.start_freq, self.end_freq, self.step_freq]]
        self.run(wait=True)

        ret = FNpeaksResult()
        with open(join(self.dir.path, fname)+'.max', 'r') as f:
            lines = f.readlines()
        peaks = Table(names=['no', 'freq', 'period', 'amplitude', 'sn'])
        for i, l in enumerate(lines[9:]):
            if len(l) > 2:
                peaks.add_row([float(s) for s in l.split()])
        ret.peaks = peaks
        ret.freq_range = (self.start_freq, self.end_freq)
        ret.freq_step = self.step_freq
        ret.lc   = self.lc  [star_pos]  #TODO cache lc[:,filter] in internal dict via @property _fmask_lc(f)
        ret.lc_e = self.lc_e[star_pos] if self.lc_e is not None else None
        ret.hjd  = self.hjd
        if filter is not None and self.filtermasks is not None:
            ret.lc   = ret.lc  [self.filtermasks[filter]]
            ret.lc_e = ret.lc_e[self.filtermasks[filter]] if ret.lc_e is not None else None
            ret.hjd  = ret.hjd [self.filtermasks[filter]]
        if periodogram:
            ret.power = np.fromfile(join(self.dir.path, fname)+'.trf', sep=' ')[1::2] # only freq column
        return ret



