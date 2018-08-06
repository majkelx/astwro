#! /usr/bin/env python
# coding=utf-8
""" Grep-like tool for FITS headers

    Call commandline: ``grepfitshdr --help`` for parameters info.
"""
from __future__ import print_function, division

import astropy.io.fits as pyfits
import re
from os.path import isfile
from sys import exit
from sys import stdout
from glob import glob

import astwro.tools.__commons as commons


def headers(filenames):
    for fname in filenames:
        if isfile(fname):
            huds = pyfits.open(fname)
            huds[0].verify('silentfix')
            h = huds[0].header
            huds.close()
            yield h, fname

def printmatch(output, filename, line, withfile, fileonly):
    if not fileonly:
        if withfile:
            print (filename + ': ', end='', file=output)
        print (line, file=output)

def iter_fields(hdr, onlyvalues=False, fields=None):
    """ splits header into lines
        if onlyvalues does not return field names
        if fields returns only specified fields (forces onlyvalues)"""
    if fields:
        for key in hdr:
            if key in fields:
                yield hdr[key]
    elif onlyvalues:
        for val in hdr.values():
            if val:
                yield str(val)
    else:
        for line in repr(hdr).strip().splitlines():
            yield line



def grep(pattern, filenames, output=stdout, invert=False, withfile=False, fileonly=False,
         fields=None, onlyvalues=False, ignorecase=True):
    if fields is not None and fields[0] == '*':
        fields = None
        onlyvalues = True

    if isinstance(filenames, str):
        filenames = glob(filenames)
    regexp = re.compile(pattern, flags=re.IGNORECASE if ignorecase else  0)
    globmatched = 0
    for h, f in headers(filenames):
        matched = scanned = 0
        # rep = repr(h).strip()
        # for line in rep.splitlines():
        for line in iter_fields(h, onlyvalues=onlyvalues, fields=fields):
            match = regexp.search(str(line))
            if invert:
                match = not match
            scanned += 1
            if match:
                matched += 1
                printmatch(output, f, line, withfile, fileonly)
                if fileonly and not invert:
                    break
        globmatched += matched
        if fileonly:
            if (not invert and matched > 0) or (invert and matched == scanned):
                print (f, file=output)
    return globmatched

def __do(arg):
    return  grep(arg.pattern, arg.file, invert=arg.v, withfile=arg.H,
                 fileonly=arg.l, fields=arg.f, ignorecase=arg.i)


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        fromfile_prefix_chars='@',
        epilog='exit code:\n'
               '  0 if any header matched pattern\n'
               '  1 if no match found\n\n' + commons.version_string(),
        description='grep-like utility for fits (main) headers\n '
                    'until -f specified, searches in keys, values and comments')
    parser.add_argument('pattern', type=str,
                        help='reg-exp, use single dot . to dump all header fields')
    parser.add_argument('file', type=str, nargs='+',
                        help='FITS file(s), catalog file containing file names prefixed by @ can be provided')
    parser.add_argument('-i', action='store_true',
                        help='ignore case')
    parser.add_argument('-v', action='store_true',
                        help='invert match')
    parser.add_argument('-H', action='store_true',
                        help='add filename to each found line')
    parser.add_argument('-l', action='store_true',
                        help='print filenames with matches only')
    parser.add_argument('-f', action='append', metavar='FIELD',
                        help='matches only specified FIELD\'s value; can be provided multiple '
                             'times to match several fields; -f* limits search to values but searches '
                             'in all fields')
    return parser


def main(pattern, file, **kwargs):
    """Entry point for python script calls. Parameters identical to command line"""
    # Extract default arguments from command line parser and apply kwargs parameters
    args = commons.bunch_kwargs(__arg_parser(), positional=[pattern, file], **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)


def info():
    """Prints commandline help message"""
    commons.info(__arg_parser())


def commandline_entry():
    # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    n = __do(__args)  # call main routine - common form command line and python calls
    return  0 if n > 0 else 1

if __name__ == '__main__':
    code = commandline_entry()
    exit(code)
