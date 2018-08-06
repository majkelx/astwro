#! /usr/bin/env python
# coding=utf-8
""" Calculates differential photometry.

    Uses Honeycutt 1992PASP..104..435H. approach
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

#from functools import partial
import numpy as np
from astropy.stats import SigmaClip
from cached_property import cached_property


class DiffPhot(object):
    def __init__(self, data, err, comp_stars_mask=None, lazy=True):
        super(DiffPhot, self).__init__()
        self._data = data
        self._err = err
        self._mask_stars_comp = comp_stars_mask
        if not lazy: # force evaluate solution
            _ = self.solution

    @property
    def N(self):
        """Number of stars. Size of mag or err vector"""
        return self.data.shape[0]

    @property
    def M(self):
        """Number of bins."""
        return self.data.shape[1]

    @cached_property
    def data(self):
        return np.ma.asanyarray(self._data)

    @cached_property
    def err(self):
        return np.ma.asanyarray(self._err)

    @cached_property
    def weights(self):
        w = self.err ** -2
        return self.err ** -2

    @cached_property
    def lc(self):
        return self.solution[1]

    @cached_property
    def lc_residuals(self):
        """NxM residuals: $r_{ij} = l_{ij} - m_i$ where $l$ is light curve point, and $m$ is resulting star magnitude"""
        return self.lc - self.mag[:, np.newaxis]

    @cached_property
    def lc_e(self):
        """NxM sqrt( err^2 + obs_deltas^2 )"""
        return np.sqrt(self.err**2 + self.obs_deltas_stddev**2)

    @cached_property
    def obs_deltas(self):
        return self.solution[2]

    @cached_property
    def obs_deltas_stddev(self):
        """std dev of observations deltas from residuals, weighted by err^-2"""
        r2w = self.lc_residuals**2 * self.weights
        sig2o = r2w.sum(axis=0) / self.weights.sum(axis=0) * r2w.count(axis=0) / (r2w.count(axis=0) - 1.0)
        return np.ma.sqrt(sig2o)

    @cached_property
    def mag(self):
        return self.solution[0]

    @cached_property
    def mag_v2(self):
        WnClc = self.lc * self.weights
        return WnClc.sum(axis=1) / self.weights.sum(axis=1)

    @cached_property
    def mag_e(self):
        return (self.err ** -2).sum(axis=1) ** -0.5

    @cached_property
    def mag_chi(self):
        return self._notimplemented

    @cached_property
    def mask_stars_comp(self):
        if self._mask_stars_comp is None:
            return np.ones(self.N, dtype=bool)
        else:
            return np.asanyarray(self._mask_stars_comp, dtype=bool)

    @cached_property
    def mask_stars_empty(self):
        try:
            return np.ma.getmask(self.data).all(axis=1)
        except:  # nomask
            return np.zeros(self.N, dtype=bool)

    @cached_property
    def mask_obs_empty(self):
        try:
            return np.ma.getmask(self.data).all(axis=0)
        except:  # nomask
            return np.zeros(self.M, dtype=bool)

    @cached_property
    def mask_obs_compempty(self):
        try:
            m = np.ma.getmask(self.data).copy()
            m[~self.mask_stars_comp] = True  # mask all data for noncomparision stars
            return m.all(axis=0)
        except:  # nomask
            return np.zeros(self.M, dtype=bool)

    @cached_property
    def solution(self):
        data = self.data[:, ~self.mask_obs_compempty]
        data_e = self.err[:, ~self.mask_obs_compempty]
        weights = self.weights[:, ~self.mask_obs_compempty]
        comp_stars_mask = self.mask_stars_comp & ~self.mask_stars_empty
        # construct equations from comparision stars
        K = data.shape[1]  # number of (nonempty) obs
        D = data[comp_stars_mask]
        W = weights[comp_stars_mask]
        W.unshare_mask()
        W[W.mask] = 0.0  # no more mask for bad values, just zero-weights
        A00 = np.diag(W.sum(axis=0)[1:])
        A11 = np.diag(W.sum(axis=1))
        A10 = W[:, 1:]
        A01 = A10.T
        A = np.block([[A00, A01], [A10, A11]])
        assert not (A00.diagonal() == 0.0).any(), "Bad obs: {}".format(np.argwhere(A00.diagonal() == 0.0))
        assert not (A11.diagonal() == 0.0).any(), "Bad star: {}".format(np.argwhere(A11.diagonal() == 0.0))
        WD = W * D.filled(0)
        B1 = WD.sum(axis=0, keepdims=True).T[1:]
        B2 = WD.sum(axis=1, keepdims=True)
        B = np.block([[B1], [B2]])
        X = np.vstack([np.zeros((1, 1)), np.linalg.solve(A, B)])  # obs[0] set to 0, excluded from equations
        O = X.squeeze()[:K]
        C = X.squeeze()[K:]
        # light curves calculation
        lc = data - O

        # add non-comparision (nC) stars
        S = np.ma.masked_all(self.N)
        S[comp_stars_mask] = C
        nC_mask = ~self.mask_stars_comp & ~self.mask_stars_empty
        WnC = weights[nC_mask]
        WnClc = lc[nC_mask] * WnC
        S[nC_mask] = WnClc.sum(axis=1) / WnC.sum(axis=1)

        # recreate masked fields (columns) for empty obs (observations without comaprision stars) in O and lc
        if self.mask_obs_compempty.any():
            nO = np.ma.masked_all(self.M)
            nO[~self.mask_obs_compempty] = O
            O = nO
            nlc = np.ma.masked_all(shape=(self.N, self.M))
            nlc[:, ~self.mask_obs_compempty] = lc
            lc = nlc
        return S, lc, O

    @property
    def _notimplemented(self):
        raise NotImplementedError('Not implemented yet')


def dphot(data, stddevs, comp_stars_mask=None):
    """
    Calculates differential photometry as in Honeycutt 1992PASP..104..435H.

    Parameters
    ----------
    :param data:    NxK array of N **comparision data** magnitudes in K observations
    :type  data:    np.ndarray or np.ma.MaskedArray
    :param stddevs: NxK array of N comparision data stddevs in K observations,
                    e.g. one can use Poisson noise: np.ma.sqrt(data)
    :type  stddevs: np.ndarray or np.ma.MaskedArray
    :param comp_stars_mask: stars which variance will be minimized, default: all
    :type  comp_stars_mask: None or array-like(bool)
    :returns:       tuple(S, L, O, sigS, sigL, sigO)
                        N-element array of stars diff photometry
                        NxK-element array of light curves
                        K-element array of corrections for observations,
                    and standard deviations for that,
                    elements for observations without stars and stars without
                    observations are masked out
    :rtype:         (np.ma.MaskedArray, np.ma.MaskedArray, np.ma.MaskedArray,
                     np.ma.MaskedArray, np.ma.MaskedArray, np.ma.MaskedArray)

    Notes
    -----
    Elements for observations without stars and stars without
    observations are masked out.
    If data and stddevs are provided and are masked arrays, masks should be identical.

    Examples
    --------
    >>> s = np.array([12.0, 12.6, 13.0, 13.2, 14.1]).reshape(5,1) # 5 stars magnitudes
    >>> o = np.array([1.0, 1.08, 0.9, 1.3]).reshape(1,4) # 4 observations deviations
    >>> x = s.dot(o) + np.random.normal(scale=0.1, size=[5,4])  # 5x4 noisy observations simulated
    >>> x
    array([[  6.77523649,  -2.78321445,   0.84035323,  15.88001531],
       [  4.56942913,  -2.11396852,   0.31539753,  16.33408252],
       [  3.10018787,  -3.87499686,  -0.5951147 ,  16.25294246],
       [  4.4895964 ,  -2.27193403,   0.40524158,  16.81285796],
       [  6.69650016,  -0.89424425,   0.60376388,  17.43194032]])

    >>> d = dphot(x, np.sqrt(x))
    >>> d
    masked_array(data = [ 0.          0.98206477 -1.29619307  3.88027423],
             mask = False,
       fill_value = 1e+20)
    >>> diff_phot = x - d   # differential photometry for x
    >>> diff_phot
    masked_array(data =
     [[ 11.83835643  11.91950781  12.18217253  11.72821846]
     [ 12.77376351  12.58305526  12.68857425  12.5437627 ]
     [ 13.12730035  13.04171745  12.86315952  12.93030926]
     [ 13.1704      13.10646413  13.14529582  13.31344976]
     [ 14.11213373  14.38888686  14.11465464  14.55691934]],
                 mask =
     False,
    >>> diff_phot.mean(axis=1) # mean magnitude
    masked_array(data = [ 11.91706381  12.64728893  12.99062164  13.18390243  14.29314864],
             mask = False,
       fill_value = 1e+20)
    """

    if comp_stars_mask is None:  # all stars equal
        comp_stars_mask = np.ones(data.shape[0], dtype=bool)
    else:
        comp_stars_mask = np.array(comp_stars_mask, dtype=bool)
    if not isinstance(stddevs, np.ma.MaskedArray):
        stddevs = np.ma.masked_values(stddevs, 0)
    empty_str = np.zeros(data.shape[1], dtype=bool)
    empty_obs = np.zeros(data.shape[1], dtype=bool)
    if not isinstance(data, np.ma.MaskedArray):
        data = np.ma.masked_array(data, mask=stddevs.mask)
    else:
        m = np.ma.getmask(data)
        assert np.array_equal(m, stddevs.mask), "data and stddev masks must be the same"
        if m is not np.ma.nomask:  # masked data provided, search for empty obs and stars
            empty_obs = m.all(axis=0)
            empty_str = m.all(axis=1)
            data = data[:, ~empty_obs]
            stddevs = stddevs[:, ~empty_obs]
            comp_stars_mask &= ~empty_str
    # construct equations from comparision stars
    K = data.shape[1]  # number of (nonempty) obs
    D = data[comp_stars_mask]
    Wall = stddevs ** -2
    W = Wall[comp_stars_mask]
    W.unshare_mask()
    W[W.mask] = 0.0  # no more mask for bad values, just zero-weights
    A00 = np.diag(W.sum(axis=0)[1:])
    A11 = np.diag(W.sum(axis=1))
    A10 = W[:, 1:]
    A01 = A10.T
    A = np.block([[A00, A01], [A10, A11]])
    assert not (A00.diagonal() == 0.0).any(), "Bad obs: {}".format(np.argwhere(A00.diagonal() == 0.0))
    assert not (A11.diagonal() == 0.0).any(), "Bad star: {}".format(np.argwhere(A11.diagonal() == 0.0))
    WD = W * D.filled(0)
    B1 = WD.sum(axis=0, keepdims=True).T[1:]
    B2 = WD.sum(axis=1, keepdims=True)
    B = np.block([[B1], [B2]])
    X = np.vstack([np.zeros((1, 1)), np.linalg.solve(A, B)])  # obs[0] set to 0, excluded from equations
    O = X.squeeze()[:K]
    C = X.squeeze()[K:]
    # light curves calculation
    lc = data - O

    # add non-comparision stars
    S = np.ma.masked_all(empty_str.size)
    S[comp_stars_mask] = C
    nC_mask = ~comp_stars_mask & ~empty_str
    WnC = Wall[nC_mask]
    WnClc = lc[nC_mask] * WnC
    S[nC_mask] = WnClc.sum(axis=1) / WnC.sum(axis=1)

    # weighted variance calculation
    resid = lc - S.reshape(S.size, 1)
    r2w = resid ** 2 * Wall
    # sig2(obs) from comparision only
    sig2o = r2w[comp_stars_mask].sum(axis=0) / W.sum(axis=0) * C.size / (C.size - 1.0)
    # sig2(stars) for all (nonempty)
    sig2s = r2w.sum(axis=1) / Wall.sum(axis=1) * O.size / (O.size - 1.0)
    # sig2(lc)
    sig2mean = sig2o / data.mask.sum(axis=0)  # sig2(obs) / num of stars in obs
    sig2lc = stddevs ** 2 + sig2mean

    if empty_obs is not None:  # recreate masked fields (columns) for empty obs
        nO = np.ma.masked_all(empty_obs.size)
        nO[~empty_obs] = O
        O = nO
        nsig2o = np.ma.masked_all(empty_obs.size)
        nsig2o[~empty_obs] = sig2o
        sig2o = nsig2o
        nlc = np.ma.masked_all((empty_str.size, empty_obs.size))
        nlc[:, ~empty_obs] = lc
        lc = nlc
        nsig2lc = np.ma.masked_all((empty_str.size, empty_obs.size))
        nsig2lc[:, ~empty_obs] = sig2lc
        sig2lc = sig2lc

    return S, lc, O, np.ma.sqrt(sig2s), np.ma.sqrt(sig2lc), np.ma.sqrt(sig2o)


def dphot_filters(data, stddevs, filters_masks, comp_stars_mask=None):
    """ Calculates differential photometry as in Honeycutt 1992PASP..104..435H, for sets of observations
     The ``filters_masks`` parameter should be a list of boolean masks choosing subsets of K observations
     e.g. for different filters. Differential photometry will be calculated for each set independently by
     ``dphot`` routine.
    :param data:            NxK array of N **comparision stars** magnitudes in K observations
    :type  data:            np.ndarray or np.ma.MaskedArray
    :param stddevs:         NxK array of N comparision data stddevs in K observations,
                                e.g. one can use Poisson noise: np.ma.sqrt(data)
    :type  stddevs:         np.ndarray or np.ma.MaskedArray
    :param filters_masks:   list-like of 1D K-element or 2D (FxK) array boolean masks selecting subset of observations
                                to be processed (e.g. filter for F filters)
    :type  filters_masks:   list(np.ndarray) or list(list(bool)) or array-like
    :param comp_stars_mask: stars which variance will be minimized, default: all. Can be 1D N-element boolean array
                                which indicates common set for all filters, or 2D FxN array-like with masks
                                for each filter.
    :type  comp_stars_mask: None or array-like(bool) or list(array-like(bool)
    :returns:               tuple(S, L, O, sigS, sigL, sigO):
                                list of N-element arrays of stars diff photometry in filters,
                                NxK-element array of light curves
                                K-element array of corrections for observations,
                            and standard deviations for that,
                            elements for observations without stars and stars without
                            observations are masked out
    :rtype:                 (list(np.ma.MaskedArray), np.ma.MaskedArray, np.ma.MaskedArray,
                             list(np.ma.MaskedArray), np.ma.MaskedArray, np.ma.MaskedArray)

    """
    filters_masks = np.array(filters_masks, dtype=bool)
    if comp_stars_mask is not None:
        comp_stars_mask = np.array(comp_stars_mask, dtype=bool)
    if comp_stars_mask is not None and comp_stars_mask.ndim == 2:
        cmasks = comp_stars_mask
    else:
        cmasks = [comp_stars_mask] * filters_masks.shape[0]

    O = np.ma.masked_all(data.shape[1])
    sigO = np.ma.masked_all(data.shape[1])
    S = []
    sigS = []
    L = np.ma.masked_all(data.shape)
    sigL = np.ma.masked_all(data.shape)

    for i, mask in enumerate(filters_masks):
        vS, lc, vO, sS, slc, sO = dphot(data[:, mask], stddevs[:, mask], cmasks[i])
        O[mask] = vO
        sigO[mask] = sO
        S.append(vS)
        sigS.append(sS)
        L[:, mask] = lc
        sigL[:, mask] = slc
    return np.ma.array(S), L, O, np.ma.array(sigS), sigL, sigO


def mean_phot(lc, lc_stddev, lc_clip_sigma=1.0, stdev_clip_sigma=1.7, lc_clip_iters=2, stdev_clip_iter=2):
    """ Calculates stars mean magnitude and error from light curves

     Calculates stars mean magnitude with standard deviation from light curves using:
     - weights from data points erros $w=e^{-2}$
     - one-side sigma clipping on errors
     - sigma clipping on data points
    :param lc:            NxK array of N  star magnitudes in K observations
    :param lc_stddev:     NxK array of  lc stddevs
    """
    p = np.ma.array(lc, copy=True)
    pe = np.ma.array(lc_stddev, copy=True)

    lc_clip = SigmaClip(sigma=lc_clip_sigma, iters=lc_clip_iters)  # , cenfunc=partial(np.ma.average, weights=pe**-1))
    err_clip = SigmaClip(sigma_lower=10.0, sigma_upper=stdev_clip_sigma, iters=stdev_clip_iter)
    pmask1 = err_clip(pe, axis=1, copy=False).mask
    pmask2 = pmask1 | lc_clip(p, axis=1, copy=False).mask
    #    print(f, p.mask.sum(), pmask1.sum(), pmask2.sum())
    #    mean, median, stddev = sigma_clipped_stats(lc[:,m], mask=mask1, axis=1, sigma=2.0)
    p.mask = pe.mask = p.mask | pmask2
    pw = pe ** -2
    mean = np.ma.average(p, axis=1, weights=pw)
    resid = lc - mean[:, np.newaxis]
    stddev = np.ma.sqrt(np.ma.average(resid ** 2, axis=1))  # , weights=pw)
    return mean, stddev
