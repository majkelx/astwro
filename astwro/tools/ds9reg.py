#! /usr/bin/env python
# coding=utf-8
""" Grep-like tool for FITS headers

    Call commandline: ``grepfitshdr --help`` for parameters info.
"""
from __future__ import print_function, division

from sys import stdout, stdin

import astwro.starlist as sl
import astwro.tools.__commons as commons



def __do(arg):
    s = sl.read_dao_file(stdin)
    sl.write_ds9_regions(s, stdout, color=arg.color, width=arg.width, size=arg.size)


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='creates ds9 region out of stars list\n'
                    'star list on stdin, region file on stdout')
    parser.add_argument('-c', '--color', type=str, default='green',
                        help='color in format accepted by ds9, default: green')
    parser.add_argument('-r', '--size', type=float, default=8.0,
                        help='radius of object circle, default: 8')
    parser.add_argument('-w', '--width', type=int, default=1,
                        help='line width, default 1')
    parser.add_argument('-i', '--id-col', type=int, default=1,
                        help='number of column in star list containing object id, default: 1')
    parser.add_argument('-x', '--x-col', type=int, default=2,
                        help='number of column in star list containing x coordinate, default: 2')
    parser.add_argument('-y', '--y-col', type=int, default=3,
                        help='number of column in star list containing y coordinate, default: 3')
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
    return  0

if __name__ == '__main__':
    code = commandline_entry()
    exit(code)
