# coding=utf-8
from __future__ import absolute_import, division, print_function


#from scipy import bin
import numpy as np
from scipy.stats import sigmaclip
from cached_property import cached_property



def err_poly_fit(mag, err):
    pe = PhotError(mag, err)
    return pe.fit


class PhotError(object):
    def __init__(self, mag, err, sigma_clip=3.0, bins='auto', fit_increasing_wing_only=True,
                 meanfn=np.mean, weighted_fit=False, fitting_order=3):
        super(PhotError, self).__init__()
        self._mag = mag
        self._err = err
        self.sigma_clip = sigma_clip
        self.bins = bins
        self.fit_increasing_wing_only = fit_increasing_wing_only
        self.meanfn = meanfn
        self.weighted_fit = weighted_fit
        self.fitting_order = fitting_order

    @cached_property
    def mag(self):
        return np.asanyarray(self._mag)

    @cached_property
    def err(self):
        return np.asanyarray(self._err)

    @cached_property
    def sorted_idx(self):
        return np.argsort(self.mag)

    @cached_property
    def mag_sorted(self):
        return self.mag[self.sorted_idx]

    @cached_property
    def err_sorted(self):
        return self.err[self.sorted_idx]

    @cached_property
    def histogram(self):
        v, r = np.histogram(self.mag_sorted, bins=self.bins)
        return v, r

    @cached_property
    def hist_counts(self):
        return self.histogram[0]

    @cached_property
    def err_clipped_counts(self):
        return np.array([len(e) for e in self.err_clipped], dtype=int)

    @cached_property
    def hist_edges(self):
        return self.histogram[1]


    @cached_property
    def binning(self):
        divs = np.searchsorted(self.mag_sorted, self.hist_edges[1:-1])
        return np.concatenate(([0], divs, [len(self.mag_sorted)]))

    @cached_property
    def hist_idx_ranges(self):
#        return zip(self.binning, self.binning[1:])
        return list(zip(self.binning, self.binning[1:]))


    @cached_property
    def clipping(self):
        mask = np.ones_like(self.mag, dtype=bool)
        i = 0
        if self.sigma_clip:
            for rlo, rhi in self.hist_idx_ranges:
                errors = self.err_sorted[rlo:rhi]
                if len(self.err_sorted[rlo:rhi]) > 2: # no sigmaclip for 0,1,2 element sets
                    _, elo, ehi = sigmaclip(self.err_sorted[rlo:rhi])
                    mask[rlo:rhi] = (elo <= self.err_sorted[rlo:rhi]) & (self.err_sorted[rlo:rhi] <= ehi)
#                    print(i, rlo, rhi, len(self.err_sorted[rlo:rhi]), mask[rlo:rhi].sum(), elo, ehi)
                i += 1
        return mask

    @cached_property
    def err_binned(self):
        return np.array([self.err_sorted[rlo:rhi] for rlo,rhi in self.hist_idx_ranges])

    @cached_property
    def err_clipped(self):
        return np.array([self.err_sorted[rlo:rhi][self.clipping[rlo:rhi]] for rlo,rhi in self.hist_idx_ranges])

    @cached_property
    def mag_clipped(self):
#        for rlo,rhi in self.hist_idx_ranges: #DEL
#            print(rlo, rhi, len(self.mag_sorted[rlo:rhi][self.clipping[rlo:rhi]]) )
        return np.array([self.mag_sorted[rlo:rhi][self.clipping[rlo:rhi]] for rlo,rhi in self.hist_idx_ranges])

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
        mask = np.isfinite(self.mag_means) & np.isfinite(self.err_means_monotonized)
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
        x = self.mag_means[self.mean_mask]
        y = self.err_means_monotonized[self.mean_mask]
        w = None
        if self.weighted_fit:
            w = self.err_means_stderr[self.mean_mask] **-1.0  # for numpy polyfit ^-1 not ^-2 !!
            w[~np.isfinite(w)] = 0.0
        rank = min(len(x), 2)
        return np.polyfit(x,y, self.fitting_order, w=w)

    def evaluate_fit(self, x):
        ret = np.zeros_like(x)
        for n, c in enumerate(self.fit[::-1]):
            ret += c * x**n
        return ret

    @cached_property
    def err_fitted(self):
        return self.evaluate_fit(self.mag_means)
