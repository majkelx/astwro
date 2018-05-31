import unittest
from astwro.pydaophot import Daophot, Allstar

# TODO: rewrite tests for v 0.4+ and switch to pytest

class TestRunners(unittest.TestCase):

    @property
    def image(self):
        from astwro.sampledata import fits_image
        return fits_image()

    def test_sample_img_access(self):
        import os
        self.assertTrue(os.path.isfile(self.image))

    def test_execution_daophot(self):
        d = Daophot(image=self.image)
        d.run()
        x,y = d.ATtach_result.picture_size
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)

    def test_image_substitution_and_find(self):
        d = Daophot()
        d.image = self.image
        r = d.FInd()
        print(d.output)
        self.assertGreater(r.stars, 1)

    def test_exception_in_PHotometry(self):
        d = Daophot(image=self.image, batch=True)
        d.FInd()
        with self.assertRaises(d.RunnerException):
            d.PHotometry(IS=0, OS=0, apertures=[8])

    #@unittest.skip('long run, un-skip to test allstar')
    def test_execution_allstar_pipeline(self):
        d = Daophot(batch=True)
        d.ATtach(self.image)
        d.FInd(1, 1)
        d.PHotometry(IS=35, OS=50, apertures=[8])
        d.PIck()
        d.PSf()
        d.run()
        a = Allstar(dir=d.dir, image=self.image)
        a.ALlstar(stars='i.nei')
        self.assertTrue(a.ALlstars_result.success)

    def test_execution_psf_pipeline(self):
        d = Daophot(image=self.image, batch=True)
        d.FInd(1, 1)
        d.PHotometry(IS=35, OS=50, apertures=[8])
        d.PIck()
        d.PSf()
        d.run()
        self.assertGreater(d.PSf_result.chi, 0)

    def test_sky_and_find(self):
        d = Daophot(image=self.image)
        s = d.SKy()
        f = d.FInd()
        self.assertAlmostEqual(f.sky, s.sky)
        self.assertAlmostEqual(f.skydev, s.skydev)
        self.assertAlmostEqual(f.mean, s.mean)
        self.assertAlmostEqual(f.median, s.median)
        self.assertAlmostEqual(f.pixels, s.pixels)


suite = unittest.TestLoader().loadTestsFromTestCase(TestRunners)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)