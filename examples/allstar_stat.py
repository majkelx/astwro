#! /usr/bin/env python
# coding=utf-8

from __future__ import print_function, division

from scipy.stats import sigmaclip

from astwro.pydaophot import Daophot
from astwro.pydaophot import Allstar
from astwro.starlist import read_dao_file
from astwro.starlist import write_ds9_regions

# TODO: expand this script to (optionally) leave result files - make: it allstar runner

# image = args.image
# coo = args.coo
# lst = args.lst


def main(**kwargs):
    # 1 do daophot aperture and psf photometry and run allstar

    dp = Daophot(image=kwargs.image)
    dp.PHotometry(stars=kwargs.coo)
    dp.PSf(psf_stars=kwargs.lst)
    al = Allstar(dir=dp.dir)
    al.ALlstar()
    all_s = al.ALlstars_result
    print(sigmaclip(all_s.chi)[0].mean())
    all_s.hist('chi')

    # 2 write regions
    # if args.regions:
    #
    #     write_ds9_regions(coo_file+'.reg', )


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(
        description='Run daophot photometry and allstar. Find mean chi of allstar stars. '
                    '(chi is calculated by allstar for every star as '
                    '"the observed pixel-to-pixel scatter from the model image profile '
                    'DIVIDED BY the expected pixel-to-pixel scatter from the image profile"). '
                    'The same mean chi is used as function to be minimized by genetic '
                    'algorithm in genetic_psf_str.py. This script allows quick comparison '
                    'between different PSF stars sets.')
    parser.add_argument('image', type=str,
                        help='FITS image file')
    parser.add_argument('coo', type=str,
                        help='all stars list: coo file')
    parser.add_argument('lst', type=str,
                        help='PSF stars list: lst file')
    parser.add_argument('--reg', action='store_true',
                        help='create ds9 region files <name>.coo.reg and <name>.lst.reg')

    args = parser.parse_args()

    main(**args.__dict__)