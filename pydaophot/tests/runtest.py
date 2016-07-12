from logging import *
from pydaophot import daophot, allstar, fname
import os
import time



# basicConfig(level=INFO)
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
    dphot2.copy_from_working_dir(fname.FOUNDSTARS_FILE, '/tmp/dupa.coo')
#    dphot.EXit(True)
    dphot1.close()
    dphot2.close()

## ONE
d = daophot()
d.ATtach(fits)
d.FInd(1, 1)
d.PHotometry()
d.PIck()

# Make copies to perform (parallel) PSF step with different parameters.
# Each gets another option of PSF RADIUS and PSF step
psf_radius = [14,16,18,20,22,24]
dphots = [d.clone() for _ in psf_radius]
for dp, ps in zip(dphots, psf_radius):
    dp.OPtion('PSF', ps)
    dp.PSf()


# Run all daophots
for dp in dphots:
    dp.run(wait=False)

# print result chi values:
for dp in dphots:
    print "PSF radius = {} gives chi = {}".format(dp.OPtion_result.get_option('PSF'), dp.PSf_result.get_chi())

# perform allstar in parallel
allstars = [allstar(dp.dir, create_subtracted_image=True) for dp in dphots]
for als in allstars:
    als.run(wait=False)
# copy subtracted files to current dir with names corresponding to PSF RADIUS parameter
for als, ps in zip(allstars, psf_radius):
    als.wait_for_results()  # file operations doesnt wait for completion (as ..._result.get_XXX do)
    als.link_from_working_dir(fname.SUBTRACTED_IMAGE_FILE, "i-psf-{}.sub.fits".format(ps))

# close them
for dp in dphots:
    dp.close()
for als in allstars:
    als.close()

#
# print 'PSF chi: {}'.format(dphot.PSf_result.get_chi())
# print 'Find: {}'.format(dphot.FInd_result.get_data())
# print 'Sky est: {} (from {} pixels)'.format(dphot.FInd_result.get_sky(), dphot.FInd_result.get_pixels())
# print 'PSF errors: {}'.format(dphot.PSf_result.get_errors())
#
# from copy import *
#
# dphot.copy_from_working_dir(fname.FOUNDSTARS_FILE)
# dphot.copy_from_working_dir(fname.PHOTOMETRY_FILE)
# dphot.copy_from_working_dir(fname.PSF_STARS_FILE)
# #dphot.copy_from_working_dir(fname.NEIGHBOURS_FILE)

# als = allstar(dir=dphot.dir, create_subtracted_image=True)
# als.run(wait=True)
# als.copy_from_working_dir(fname.SUBTRACTED_IMAGE_FILE)
# print "Stars Allstars: {}".format(als.result.get_stars_no())

# dphot.close()

elapsed_time = time.time() - start_time
print 'Test completed in {:.3f} seconds'.format(elapsed_time)