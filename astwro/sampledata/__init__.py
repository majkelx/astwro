
def fits_image():
    return __sampledata('NGC6871.fits')


def coo_file():
    return __sampledata('NGC6871.coo')


def lst_file():
    return __sampledata('NGC6871.lst')


def ap_file():
    return __sampledata('NGC6871.ap')


def psf_file():
    return __sampledata('NGC6871.psf')


def als_file():
    return __sampledata('NGC6871.als')


def __sampledata(filename):
    import os
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
