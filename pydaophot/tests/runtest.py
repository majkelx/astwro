from logging import *
from pydaophot import daophot
import os

basicConfig(level=DEBUG)
fits = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'NGC6871.fits')

dphot = daophot()
#dphot.get_options()
dphot.OPtion('RE', 1.77)
dphot.ATtach(fits)
dphot.OPtion('FI', 12)
#op =  dphot.get_options()
#for op in op.items():
#    print op
print ("Image size: ", dphot.get_pic_size())
dphot.find()
dphot.close()
print (dphot.get_options())
print (dphot.get_option('FITTING RADIUS'))

