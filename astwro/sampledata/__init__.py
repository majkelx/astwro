"""
Module contains sample FITS file and other daophot files for testing
"""
def fits_image():
    """path of FITS image of NGC6871"""
    return __sampledata('NGC6871.fits')

def coo_file():
    """path of `coo` file for :py:func:`fits_image()`"""
    return __sampledata('NGC6871.coo')

def lst_file():
    """path of `lst` file for :py:func:`fits_image()` """
    return __sampledata('NGC6871.lst')

def ap_file():
    """path of `ap` file for :py:func:`fits_image()`"""
    return __sampledata('NGC6871.ap')

def psf_file():
    """path of `psf` file for :py:func:`fits_image()`"""
    return __sampledata('NGC6871.psf')

def als_file():
    """path of `als` file for :py:func:`fits_image()`"""
    return __sampledata('NGC6871.als')

def nei_file():
    """path of `nei` file for :py:func:`fits_image()`"""
    return __sampledata('NGC6871.nei')

def err_file():
    return __sampledata('i.err')

def __sampledata(filename):
    import os
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
