import glob
from os.path import join, basename
import numpy as np
import astropy.io.fits as fits
from astropy.table import Table
from astropy.stats import SigmaClip


def make_fits_table(directory='.', recursive=False, filename_pattern='*.fits', hud_no=0, fields=None,
                    stats=3.0):
    """
    Returns table with FITS files information

    :param directory: directory to search for FITS files
    :type directory: str, path-like
    :param recursive: **not implemented**
    :type recursive: bool
    :param filename_pattern: glob pattern for fits files
    :type filename_pattern: str
    :param hud_no: Which HUD of FITS file should be scanned for header fields and stats
    :type hud_no: int
    :param fields: list of FITS header fields to be extract to columns
    :type fields: List[str]
    :param stats:   If `not False`, columns with mean, median and std will be added. If numerical, it will be
                    sigma-clipped stats (slower - iterative) with number value indicates value of sigma for clipping.
    :type stats: bool, float
    :rtype Table
    """

    if recursive:
        raise NotImplementedError('recursive search not implemented, ask Mikolaj to implement')
    fits_list = glob.glob(join(directory, filename_pattern))
    if fields is None:
        fields = []
    col_pathn = []
    col_names = []
    cols_fields = [[] for _ in fields]
    cols_stats = [[], [], []] if stats else []
    # cols_stats_names = ['mean', 'median', 'std', 'min', 'max'] if stats else []
    cols_stats_names = ['median', 'min', 'max'] if stats else []
    if isinstance(stats, float):
        clipper = SigmaClip(stats)
    for f in fits_list:
        col_pathn.append(f)
        col_names.append(basename(f))
        if fields or stats:
            with fits.open(f) as hud:
                h = hud[hud_no].header
                for fld, col in zip(fields, cols_fields):
                    try:
                        col.append(h[fld])
                    except LookupError:
                        col.append(None)
                if stats:
                    d = hud[hud_no].data
                    if isinstance(stats, float):
                        clipped, minv, maxv = clipper(d, return_bounds=True)
                        # s = np.nanmean(clipped), np.nanmedian(clipped), np.nanstd(clipped), minv, maxv
                        s = np.nanmedian(clipped), minv, maxv
                    else:
                        # s = np.mean(d), np.median(d), np.std(d), np.min(d), np.max(d)
                        s = np.median(d), np.min(d), np.max(d)
                    for c, v in zip(cols_stats, s):
                        c.append(v)

    return Table([col_pathn, col_names] + cols_stats + cols_fields,
                 names=['pathname', 'filename']+ cols_stats_names + fields)


