#! /usr/bin/env python
# coding=utf-8

from __future__ import print_function, division

import astropy.io.fits as pyfits
import re
from os.path import isfile
from sys import exit
from sys import stdout

import __commons as commons


def headers(filenames):
    for fname in filenames:
        if isfile(fname):
            huds = pyfits.open(fname)
            huds[0].verify('silentfix')
            h = huds[0].header
            huds.close()
            yield h

def grep(pattern, filenames, output=stdout):
    regexp = re.compile(pattern, flags=re.IGNORECASE)
    matched = 0
    for h in headers(filenames):
        rep = repr(h).strip()
        for line in rep.splitlines():
            if regexp.search(line):
                matched += 1
                print(line, file=output)
    return matched

def __do(arg):
    return  grep(arg.pattern, arg.file)


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


def main(pattern, file, **kwargs):
    """Entry point for python script calls. Parameters identical to command line"""
    # Extract default arguments from command line parser and apply kwargs parameters
    args = commons.bunch_kwargs(__arg_parser(), positional=[pattern, file], **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)


def info():
    commons.info(__arg_parser())


def commandline_entry():
    # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    n = __do(__args)  # call main routine - common form command line and python calls
    return  0 if n > 0 else 1

if __name__ == '__main__':
    code = commandline_entry()
    exit(code)
