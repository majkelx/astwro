import unittest
from astwro.pydaophot import daophot, allstar


class TestRunners(unittest.TestCase):

    @property
    def image(self):
        from astwro.sampledata import fits_image
        return fits_image()

    def test_sample_img_access(self):
        import os
        self.assertTrue(os.path.isfile(self.image))

    def test_execution_daophot(self):
        d = daophot(image_file=self.image)
        x,y = d.ATtach_result.picture_size
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)

    @unittest.skip('long run, un-skip to test allstar')
    def test_execution_allstar_pipeline(self):
        d = daophot()
        d.ATtach(self.image)
        d.FInd(1, 1)
        d.PHotometry()
        d.PIck()
        d.PSf()
        d.wait_for_results()
        a = allstar(d.dir)
        self.assertGreater(a.result.stars_no, 0)

    def test_execution_psf_pipeline(self):
        d = daophot()
        d.ATtach(self.image)
        d.FInd(1, 1)
        d.PHotometry()
        d.PIck()
        d.PSf()
        self.assertGreater(d.PSf_result.chi, 0)

    def test_auto_attach_find_expl_run(self):
        d = daophot(self.image)
        d.FInd(1, 1)
        self.assertGreater(d.FInd_result.stars, 0)

    def test_implicit_reset(self):
        d = daophot(image_file=self.image)
        self.assertGreater(d.ATtach_result.picture_size[0], 0) # implicit run 1
        d.FInd(1,1)  # implicit reset
        self.assertGreater(d.FInd_result.stars, 0)  # implicit run 2


suite = unittest.TestLoader().loadTestsFromTestCase(TestRunners)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)