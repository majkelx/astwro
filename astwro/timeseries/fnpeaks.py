# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type
# see https://wiki.python.org/moin/PortingToPy3k/BilingualQuickRef

from os.path import join
import numpy as np
from astropy.table import Table
from astropy.modeling import models, fitting
from astropy.stats import sigma_clipped_stats, sigma_clip

from astwro.exttools import Runner
from astwro.phot.lc_io import write_lc, write_lc_filters

class LCFitter(object):
    """
    Abstract Light Curve Fitter

    Base class for light curve fitters used by `FNpeaksResult.makefit`

    Parameters
    ----------
    clipping_sigma: float
        Sigma clipping to this of light curve before fitting
    """
    def __init__(self, clipping_sigma=None):
        self.clipping_sigma = clipping_sigma
        self.fit = None


    def __call__(self, *args, **kwargs):
        """
        Call underlying model
        """
        return self.fit(*args, **kwargs)

    def dofit(self, freq, hjd, lc, lc_e=None):
        """
        Performs model fit to light curve

        Dummy abstract method to be overridden

        Parameters
        ----------
        freq: float
            Frequency found by FNpeaks, fixed model parameter.
        hjd : array-like
            N-element time axis
        lc : array-like
            N-element measurements on points on `hjd` time moments
        lc_e : array-like
            N-element optional errors of measurements `lc`

        Returns
        -------
        Touple clipped_hjd, fitted_model
        """
        raise NotImplementedError('Abstract LCFitter.fit method called')
        return None, self


class SineFitter(LCFitter):
    """A sin(2pi*f + phi)"""
    def __init__(self, clipping_sigma=None):
        super(SineFitter, self).__init__(clipping_sigma)
        self.fit = None
        self.frequency = None
        self.amplitude = None
        self.phase = None


    def dofit(self, freq, hjd, lc, lc_e=None):
        fitter = fitting.FittingWithOutlierRemoval(fitting.LevMarLSQFitter(), sigma_clip, sigma=self.clipping_sigma)
        model = models.Sine1D(frequency=freq)
        model.frequency.fixed = True
        clipped, fit = fitter(model, hjd, lc - sigma_clipped_stats(lc)[0])
        self.fit = fit
        self.frequency = fit.frequency
        self.amplitude = fit.amplitude
        self.phase = fit.phase
        return clipped, self

class SineFitterC(LCFitter):
    """A sin(2pi*f + phi) + mag"""
    def __init__(self, clipping_sigma=None):
        super(SineFitterC, self).__init__(clipping_sigma)
        self.fit = None
        self.frequency = None
        self.amplitude = None
        self.phase = None
        self.mag = None

    def dofit(self, freq, hjd, lc, lc_e=None):
        fitter = fitting.FittingWithOutlierRemoval(fitting.LevMarLSQFitter(), sigma_clip, sigma=self.clipping_sigma)
        model = models.Sine1D(frequency=freq) + models.Const1D(0)
        model.frequency_0.fixed = True
        clipped, fit = fitter(model, hjd, lc)
        self.fit = fit
        self.frequency = fit.frequency_0
        self.amplitude = fit.amplitude_0
        self.phase = fit.phase_0
        self.mag = fit.amplitude_1
        return clipped, self


class SineHarmonicFitterC(LCFitter):
    """A SUM_i sin(2pi*f*i + phi) + mag"""
    def __init__(self, clipping_sigma=None, minn=1, maxn=6):
        super(SineHarmonicFitterC, self).__init__(clipping_sigma)
        self.fit = None
        self.frequency = None
        self.amplitude = None
        self.phase = None
        self.mag = None
        self.minn = minn
        self.maxn = maxn

    def dofit(self, freq, hjd, lc, lc_e=None):
        inner_fitter = fitting.LevMarLSQFitter()
        fitter = fitting.FittingWithOutlierRemoval(inner_fitter, sigma_clip, sigma=self.clipping_sigma)
        ret_clipped = None
        for n in range(self.minn, self.maxn+1):
            model = models.Const1D(0)
            for i in range(1, n+1): # add i harmonics to model
                model_s = models.Sine1D(frequency=freq*i, amplitude=0)
                model_s.frequency.fixed = True
                model = model + model_s
            clipped, fit = fitter(model, hjd, lc)
            if ret_clipped is None:
                ret_clipped = clipped  # return first clipping not harmonics clipping
            chi = np.ma.std(clipped - fit(hjd))
            print(chi)
        self.fit = fit
        self.frequency = fit.frequency_1
        self.amplitude = fit.amplitude_1
        self.phase = fit.phase_1
        self.mag = fit.amplitude_0
        return ret_clipped, self

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
        self.fit = None
        self.lc_clipped = None

    @property
    def frequencies(self):
        return np.arange(self.freq_range[0], self.freq_range[1], self.freq_step)

    @property
    def periods(self):
        return 1.0 / np.arange(self.freq_range[0], self.freq_range[1], self.freq_step)

    @property
    def lc_reduced(self):
        if self.fit is None:
            self.makefit()
        return self.lc_clipped - self.fit(self.hjd)

    def makefit(self, freq=None, peak=0, clipping_sigma=3.0, fitter_class=SineHarmonicFitterC, **kwargs):
        if freq is None:
            freq = self.peaks[peak]['freq']
        fitter = fitter_class(clipping_sigma, **kwargs)
        self.lc_clipped, self.fit = fitter.dofit(freq, self.hjd, self.lc,self.lc_e)
        return self.fit

    # def makefit(self, freq=None, peak=0, clipping_sigma=3.0):
    #     if freq is None:
    #         freq = self.peaks[peak]['freq']
    #     fitter = fitting.FittingWithOutlierRemoval(fitting.LevMarLSQFitter(), sigma_clip, sigma=clipping_sigma)
    #     model = models.Sine1D(frequency=freq)
    #     model.frequency.fixed = True
    #     self.lc_clipped, self.fit = fitter(model, self.hjd, self.lc - sigma_clipped_stats(self.lc)[0])
    #     return self.fit



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

    def __call__(self, star, filter=None, periodogram=False, error_max=None, sigmaclip=None):
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

        mask = np.ones_like(lc, dtype=bool)
        if error_max is not None and lc_e is not None:
            mask = lc_e < error_max
            lc = np.ma.MaskedArray(lc)
            lc.mask = lc.mask | ~(lc_e < error_max)
        if sigmaclip is not None:
            lc = sigma_clip(lc, sigma=sigmaclip)

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



