# coding=utf-8
from __future__ import absolute_import, division, print_function
import astropy.io.fits as fits
import astropy.visualization as vis
from astropy.wcs import WCS
import matplotlib.pyplot as plt
from .coord_tools import fix_scamp_wcs
import astwro.sampledata

__metaclass__ = type

def plot_coords(fig=None, ax=None, fits_file=astwro.sampledata.fits_image(), gal=True, img_alpha=1.0, cmap=None,
                grid_c='gray', grid_alpha=0.5, grid_ls='solid', keep_scale=True, img=True,
                ):
    if ax is None or  isinstance(ax, int):
        if fig is None:
            fig = plt.figure(figsize=(6, 6))
            fig.tight_layout()
        if ax is None: ax = 111
        hdu = fits.open(fits_file)[0]
        fix_scamp_wcs(hdu)
        wcs = WCS(hdu.header)
        ax = fig.add_subplot(ax, projection=wcs)
    if img:
        vmin, vmax =  120, 90
        norm = vis.ImageNormalize(vmin=vmin, vmax=vmax, stretch=vis.SqrtStretch())
        ax.imshow(hdu.data, origin='lower', norm=norm, alpha=img_alpha, cmap=cmap)

    ax.coords.grid(True, color=grid_c, ls=grid_ls, alpha=grid_alpha)
    ax.coords[0].set_axislabel('ra')
    ax.coords[1].set_axislabel('dec')
    ax.coords['ra'].set_major_formatter('hh:mm:ss')
    if keep_scale:
        ax.set_autoscale_on(False)
    if gal:
        overlay = ax.get_coords_overlay('galactic')
        overlay.grid(color=grid_c, ls=grid_ls, alpha=grid_alpha)
        overlay[0].set_axislabel('$l$')
        overlay[1].set_axislabel('$b$')
    return ax