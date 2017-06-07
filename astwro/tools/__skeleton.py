#! /usr/bin/env python
# coding=utf-8
"""Copy this skeleton to start new tool
"""
from __future__ import print_function, division
# GLOBAL IMPORTS HERE
import __commons as commons


def __do(arg):
    """Main routine, common for command line, and python scripts call"""

    # refer to args: arg.foo
    # IMPLEMENT HERE
    return arg.bar + arg.foo


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=commons.version_string(),
        description='Sums foo and bar')
    parser.add_argument('foo', type=int,
                        help='some foo')
    parser.add_argument('--bar', type=int,
                        help='some bar')
    return parser


# Below: standard skeleton for astwro.tools
# CUSTOMIZE:
#   1. customize postional - obligatory arguments
#   2. decide whether to print results (__do return)

def main(positional1, positional2, **kwargs):
    """Entry point for python script calls. Parameters identical to command line"""
    # Extract default arguments from command line parser and apply kwargs parameters
    args = commons.bunch_kwargs(__arg_parser(), positional=[positional1, positional2], **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)


def info():
    commons.info(__arg_parser())


def commandline_entry():
    # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    if __args.version:
        print ('astwro.tools '+astwro.tools.__version__)
        exit()
    result = __do(__args)  # call main routine - common form command line and python calls
    print(result)
    return 0

if __name__ == '__main__':
    code = commandline_entry()
    exit(code)