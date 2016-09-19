#! /usr/bin/env python
# coding=utf-8

from __future__ import print_function, division

import astropy.io.fits as pyfits
import re
from os.path import isfile
from sys import exit

import __commons as commons


def headers(filenames):
    for fname in filenames:
        if isfile(fname):
            huds = pyfits.open(fname)
            huds[0].verify('silentfix')
            h = huds[0].header
            huds.close()
            yield h


def main(**kwargs):
    arg = commons.bunch_kwargs(**kwargs)
    regexp = re.compile(arg.pattern, flags=re.IGNORECASE)
    matched = 0
    for h in headers(arg.file):
        rep = repr(h).strip()
        for line in rep.splitlines():
            if regexp.search(line):
                matched += 1
                print(line)
    return matched


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        epilog='exit code:\n'
               '  0 if any header matched pattern\n'
               '  1 if no match found\n\n' + commons.version_string(),
        description='grep-like utility for fits (main) headers')
    parser.add_argument('pattern', type=str,
                        help='reg-exp, use single dot . to dump all header fields')
    parser.add_argument('file', type=str, nargs='+',
                        help='FITS file(s), catalog file containing file names prefixed by @ can be provided')
    return parser


def info():
    commons.info(__arg_parser())


if __name__ == '__main__':

    args = __arg_parser().parse_args()
    n = main(**args.__dict__)
    exit(0 if n > 0 else 1)
