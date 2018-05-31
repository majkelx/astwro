# coding=utf-8
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest
from astwro.sex import Sextractor
from astwro.sex import Scamp
from astwro.sampledata import fits_image

# TODO: switch to pytest

class TestRunners(unittest.TestCase):

    def test_sextractor_run(self):
        sex = Sextractor()
        sex.run()

        # self.assertAlmostEqual(f.sky, s.sky)
        # self.assertAlmostEqual(f.skydev, s.skydev)
        # self.assertAlmostEqual(f.mean, s.mean)
        # self.assertAlmostEqual(f.median, s.median)
        # self.assertAlmostEqual(f.pixels, s.pixels)


    def test_astometry(self):
        sex = Sextractor()
        scamp = Scamp()
        sexresult = sex(fits_image())
        self.assertGreater(len(sexresult.stars), 0)
        scampresult = scamp(sexresult)





suite = unittest.TestLoader().loadTestsFromTestCase(TestRunners)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)