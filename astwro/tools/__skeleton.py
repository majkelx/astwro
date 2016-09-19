#! /usr/bin/env python
# coding=utf-8
"""Copy this skeleton to start new tool
"""
from __future__ import print_function, division
# GLOBAL IMPORTS HERE
import __commons as commons


def main(**kwargs):
    arg = commons.bunch_kwargs(**kwargs)

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


def info():
    commons.info(__arg_parser())


if __name__ == '__main__':

    args = __arg_parser().parse_args()
    print (main(**args.__dict__))
