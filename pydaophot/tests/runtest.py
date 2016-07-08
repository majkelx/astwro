from logging import *
from pydaophot import daophot, fname
import os
import time



basicConfig(level=INFO)
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

start_time = time.time()

dphot1 = daophot()

for i in range(0):
    info('###ITERATION %d' % i)
    dphot1.reset()
    dphot2 = daophot()
    dphot1.ATtach(fits)
    dphot2.ATtach(fits)
    dphot2.OPtion('FITTING', 5.5)
    dphot1.FInd(1,1)
    dphot2.FInd(1,1)
    dphot1.PHotometry()
    dphot1.PIck()
    dphot1.PSf()
    dphot2.PHotometry()
    dphot2.PIck()
    dphot2.PSf()
    dphot1.run(wait=False)
    dphot2.run(wait=False)
#    print dphot1.FInd_result.get_stras(), dphot1.PHotometry_result.get_mag_limit()
#    print 'Pick found: {} stars'.format(dphot1.PIck_result.get_stars())
    dphot2.FInd_result.get_data()
    dphot2.copy_from_working_dir(fname.STARS_FILE, '/tmp/dupa.coo')
#    dphot.EXit(True)
    dphot1.close()
    dphot2.close()

## ONE
dphot = daophot()
dphot.ATtach(fits)
dphot.FInd(1,1)
dphot.PHotometry()
dphot.PIck()
dphot.PSf()

dphot.run(wait=False)


print 'PSF chi: {}'.format(dphot.PSf_result.get_chi())
print 'Find: {}'.format(dphot.FInd_result.get_data())
print 'Sky est: {} (from {} pixels)'.format(dphot.FInd_result.get_sky(), dphot.FInd_result.get_pixels())
print 'PSF errors: {}'.format(dphot.PSf_result.get_errors())

dphot.copy_from_working_dir(fname.STARS_FILE)
dphot.copy_from_working_dir(fname.PHOTOMETRY_FILE)
dphot.copy_from_working_dir(fname.PSF_STARS_FILE)
#dphot.copy_from_working_dir(fname.NEIGHBOURS_FILE)

#dphot.close()

elapsed_time = time.time() - start_time
print 'Test completed in {:.3f} seconds'.format(elapsed_time)