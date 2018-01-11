# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import logging
import numpy as np


def write_lc(hjd, lc, lc_e=None, ids=None, min_obs=1, prefix='lc_', suffix='.obs'):
    if ids is None:
        ids = range(lc.shape[0])
    masked = isinstance(lc, np.ma.MaskedArray)
    if masked:
        smask = lc.count(axis=1) >= min_obs
    else:
        smask = np.ones(lc.shape[0], dtype=bool)
    logging.info('Number of stars to save: {}'.format(np.count_nonzero(smask)))
    for i in smask.nonzero()[0]:
        fname = '{:s}{:05d}{:s}'.format(prefix, ids[i], suffix)
        logging.info('Processing star id: ',i)
        d = lc[i]
        if masked:
            m = ~d.mask
            t = hjd[m]
            e = lc_e[i][m] if lc_e is not None else None
            d = d.compressed()
        else:
            t = hjd
            e = lc_e[i] if lc_e is not None else None
        if lc_e is None:
            out = np.array([t, d]).T
        else:
            out = np.array([t, d, e]).T
        np.savetxt(fname, out, fmt='%15f')


def write_lc_filters(filters_masks, filternames, hjd, lc, lc_e=None, ids=None, min_obs=1, prefix='lc_', suffix='.obs'):
    if isinstance(filters_masks, dict):
        filters_masks = [filters_masks[f] for f in filternames]
    filters_masks = np.array(filters_masks, dtype=bool)

    for i, mask in enumerate(filters_masks):
        logging.info('Writing lc for Filter: {}'.format(filternames[i]))
        s = '_' + filternames[i] + suffix
        mhjd = hjd[mask]
        mlc = lc[:, mask]
        if lc_e is not None:
            mlc_e = lc_e[:, mask]
        else:
            mlc_e = None
        write_lc(mhjd, mlc, mlc_e, ids, min_obs, prefix, s)


# def write_lc(hjd, lc, lc_e=None, ids=None, min_obs=1, prefix='lc_', suffix='.obs'):
#     if ids is None:
#         ids = range(lc.shape[0])
#     smask = lc.count(axis=1) >= min_obs
#     logging.info('Number of stars to save: {}'.format(np.count_nonzero(smask)))
#     for i in smask.nonzero()[0]:
#         fname = '{:s}{:05d}{:s}'.format(prefix, ids[i], suffix)
#         logging.info('Processing star id: ',i)
#         with open(join(fname), 'w') as f:
#             for t, m in zip(hjd, lc[i]):
#                 if m is not np.ma.masked:
#                     print (t, m, file=f)
