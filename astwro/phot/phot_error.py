# coding=utf-8
from __future__ import absolute_import, division, print_function


#from scipy import bin
import numpy as np
from scipy.stats import sigmaclip
from scipy.optimize import curve_fit
from cached_property import cached_property



def err_poly_fit(mag, err):
    pe = PhotError(mag, err)
    return pe.fit


class PhotError(object):
    def __init__(self, mag, err, sigma_clip=3.0, bins='auto', fit_increasing_wing_only=True,
                 meanfn=np.mean, weighted_fit=True, fitting_order=6, fitplussigma=3.0):
        super(PhotError, self).__init__()
        self._mag = mag
        self._err = err
        self.sigma_clip = sigma_clip
        self.bins = bins
        self.fit_increasing_wing_only = fit_increasing_wing_only
        self.meanfn = meanfn
        self.weighted_fit = weighted_fit
        self.fitting_order = fitting_order
        self.fitplussigma = fitplussigma

    @cached_property
    def N(self):
        """Number of stars. Size of mag or err vector"""
        return len(self.mag)

    @cached_property
    def M(self):
        """Number of bins."""
        return len(self.mag_bin_counts)

    @cached_property
    def mag(self):
        return np.asanyarray(self._mag)

    @cached_property
    def err(self):
        return np.asanyarray(self._err)

    @cached_property
    def mag_idx_sorted(self):
        """Index sorting mag or err by mag. Size: N"""
        return np.argsort(self.mag)

    @cached_property
    def mag_sorted(self):
        """mag sorted. Size: N"""
        return self.mag[self.mag_idx_sorted]

    @cached_property
    def err_sorted(self):
        """err sorted by magnitude. Size: N"""
        return self.err[self.mag_idx_sorted]

    @cached_property
    def mag_histogram(self):
        """magnitude histogram: Pair: (values size M, edges size M+1)"""
        v, r = np.histogram(self.mag_sorted, bins=self.bins)
        return v, r

    @cached_property
    def mag_bin_counts(self):
        """Size: M"""
        return self.mag_histogram[0]

    @cached_property
    def mag_bin_edges(self):
        """Magnitudes of histogram bins edged. Size: M+1"""
        return self.mag_histogram[1]

    @cached_property
    def mag_bin_idx(self):
        """Indexes of magnitude histogram bins edged. Size: M+1"""
        divs = np.searchsorted(self.mag_sorted, self.mag_bin_edges[1:-1])
        return np.concatenate(([0], divs, [len(self.mag_sorted)]))

    @cached_property
    def mag_bin_idx_ranges(self):
        """Indexes ranges for bins of magnitude histogram. Size: M list of pairs"""
        #        return zip(self.mag_bin_idx, self.mag_bin_idx[1:])
        return list(zip(self.mag_bin_idx, self.mag_bin_idx[1:]))

    @cached_property
    def err_bin(self):
        return np.array([self.err_sorted[rlo:rhi] for rlo,rhi in self.mag_bin_idx_ranges])





    @cached_property
    def clipping(self):
        mask = np.ones_like(self.mag, dtype=bool)
        i = 0
        if self.sigma_clip:
            for rlo, rhi in self.mag_bin_idx_ranges:
                errors = self.err_sorted[rlo:rhi]
                if len(self.err_sorted[rlo:rhi]) > 2: # no sigmaclip for 0,1,2 element sets
                    _, elo, ehi = sigmaclip(self.err_sorted[rlo:rhi])
                    mask[rlo:rhi] = (elo <= self.err_sorted[rlo:rhi]) & (self.err_sorted[rlo:rhi] <= ehi)
#                    print(i, rlo, rhi, len(self.err_sorted[rlo:rhi]), mask[rlo:rhi].sum(), elo, ehi)
                i += 1
        return mask


    @cached_property
    def err_clipped(self):
        return np.array([self.err_sorted[rlo:rhi][self.clipping[rlo:rhi]] for rlo,rhi in self.mag_bin_idx_ranges])
    @cached_property

    def err_clipped_counts(self):
        return np.array([len(e) for e in self.err_clipped], dtype=int)

    @cached_property
    def mag_clipped(self):
#        for rlo,rhi in self.mag_bin_idx_ranges: #DEL
#            print(rlo, rhi, len(self.mag_sorted[rlo:rhi][self.clipping[rlo:rhi]]) )
        return np.array([self.mag_sorted[rlo:rhi][self.clipping[rlo:rhi]] for rlo,rhi in self.mag_bin_idx_ranges])

    @cached_property
    def err_means(self):
        ret = np.array([self.meanfn(e) for e in self.err_clipped])
        ret[self.err_clipped_counts == 0] = np.nan
        return ret

    @cached_property
    def err_means_stderr(self):
        return np.array([np.std(e,ddof=1) for e in self.err_clipped])

    @cached_property
    def mag_means(self):
        return np.array([np.mean(ms) for ms in self.mag_clipped])

    @cached_property
    def mean_mask(self):
        mask = np.isfinite(self.mag_means) \
               & np.isfinite(self.err_means_monotonized) \
               & np.isfinite(self.err_means_stderr)
        return mask

    @cached_property
    def err_means_monotonized(self):
        ret = self.err_means
        if self.fit_increasing_wing_only:
            ret = self.err_means.copy()
            leftcutout = np.nanargmin(self.err_means)
            ret [0:leftcutout] = self.err_means[leftcutout]
        return ret

    @cached_property
    def fit(self):
        return self._fit(self.err_means_monotonized[self.mean_mask])

    @cached_property
    def err_fitted(self):
        return self.evaluate_fit(self.mag_means)

    @cached_property
    def fit_plus_sigmas(self):
        return self._fit(self.err_means_monotonized[self.mean_mask]
                         + self.fitplussigma*np.nan_to_num(self.err_means_stderr[self.mean_mask]))

    @cached_property
    def err_fitted_plus_sigmas(self):
        return self.evaluate_fit_plus_sigmas(self.mag_means)

    @cached_property
    def outlayers_mask(self):
        limit = self.evaluate_fit_plus_sigmas(self.mag)
        return self.err > limit

    def evaluate_fit(self, x):
        return self._evaluate_fit(x, self.fit)

    def evaluate_fit_plus_sigmas(self, x):
        return self._evaluate_fit(x, self.fit_plus_sigmas)

    def _fit(self, y):
        x = self.mag_means[self.mean_mask]
        s = None
        if self.weighted_fit:
            s = (self.err_means_stderr[self.mean_mask])

        f = curve_fit(lambda t,a,b,c: a*np.exp(b*t)+c, x,y, sigma=s, absolute_sigma=True)
        return f

    def _evaluate_fit(self, x, fit):
        ret = np.zeros_like(x)
        return fit[0][0] * np.exp(fit[0][1] * x) + fit[0][2]

    # def _fit_poly(self, y):
    #     x = self.mag_means[self.mean_mask]
    #     w = None
    #     if self.weighted_fit:
    #         w = self.err_means_stderr[self.mean_mask] **-1.0  # for numpy polyfit ^-1 not ^-2 !!
    #         w[~np.isfinite(w)] = 0.0
    #     rank = min(len(x), 2)
    #     return np.polyfit(x,y, self.fitting_order, w=w)
    #
    # def _evaluate_fit_poly(self, x, fit):
    #     ret = np.zeros_like(x)
    #     for n, c in enumerate(fit[::-1]):
    #         ret += c * x**n
    #     return ret

    @cached_property
    def filtered_by_sigma_from_means(self):
        return self._filter(self.err_means)

    @cached_property
    def filtered_by_sigma_from_means(self):
        return self._filter(self.err_fitted)

    @cached_property
    def err_weighted_mean(self):
        """Weighted by flux mean of err, float"""
        w = 100 * (-self.mag / 5)
        return (self.err * w).sum() / w.sum()

    def _filter(self, err_bin_values):

        return