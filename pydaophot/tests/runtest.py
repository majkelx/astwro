from logging import *
from pydaophot import daophot
import os

basicConfig(level=DEBUG)
fits = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'NGC6871.fits')

#dphot = daophot()
#dphot.ATtach(fits)
#dphot.OPtion('FI', 12)
#op =  dphot.get_options()
#for op in op.items():
#    print op
#print ("Image size: ", dphot.ATtach_result.get_picture_size())
#dphot.FInd()
#print (dphot.FInd_result.get_data())
#print (dphot.OPtion_result.get_options())
#print (dphot.OPtion_result.get_option('FITTING RADIUS'))

## find:
#dphot.create_apertures_file([8.0], 35, 50)

#dphot.close()

for i in range(100):
    print i,
    dphot = daophot()
    dphot.ATtach(fits)
    dphot.close()