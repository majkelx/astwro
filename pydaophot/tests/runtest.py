from logging import *
from pydaophot import daophot
import os

#basicConfig(level=DEBUG)

dphot = daophot()
fits = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'NGC6871.fits')
dphot.attach(fits)
print ("Image size: ", dphot.get_pic_size())
dphot.find()
dphot.close()

debug ("wrk dir: %s", dphot.dir)
debug ("process: %s", dphot.process)


