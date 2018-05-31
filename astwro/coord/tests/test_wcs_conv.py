# coding=utf-8
from astwro.sampledata import  fits_image
from astwro.coord import xy2sky, skycoo2xy, skyradec2xy
import astropy.units as u


def test_xy2sky():
    coo1 = xy2sky(100,121,fits_image())
    coo2 = xy2sky([100,100], [120,121], fits_image())

    assert coo1.ra == coo2[1].ra
    assert coo1.ra > 301*u.deg


def test_sky2xy():
    coo1 = xy2sky(100,100, transformer=fits_image())
    coo2 = xy2sky([100,100, 99], [120,121,12.8], transformer=fits_image())
    xy1 = skycoo2xy(coo1, transformer=fits_image())
    xy2 = skycoo2xy(coo2, transformer=fits_image())

    assert xy2[1,2] < 13.0 and xy2[1,2] > 12.0


def test_long_tmp():
    ra = [10, 10, 9]
    dec = [12, 21, 12.8]
    packed = skyradec2xy(ra, dec, unit=(u.deg, u.deg), transformer=fits_image())
    s = packed.shape
    x, y = packed
