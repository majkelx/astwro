#! /usr/bin/env python
# coding=utf-8
"""Copy this skeleton to start new tool
"""
from __future__ import print_function, division
# GLOBAL IMPORTS HERE
import __commons as commons
import astwro.starlist as sl
from sys import stdin, stdout, stderr


def __do(arg):
    # TODO: __do arguments - in/out files/streams
    i = stdin
    o = stdout

    # http://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
    from signal import signal, SIGPIPE, SIG_DFL
    signal(SIGPIPE, SIG_DFL)

    if arg.input_format:
        arg.input_format = arg.input_format.upper()
    if arg.output_format:
        arg.output_format = arg.output_format.upper()

    if arg.input_format == 'DS9':
        s = sl.read_ds9_regions(i)
    else:
        daotype = None
        if arg.input_format == 'COO':
            daotype = sl.DAO.COO_FILE
        elif arg.input_format == 'SHORT':
            daotype = sl.DAO.SHORT_FILE
        s = sl.read_dao_file(i, dao_type=daotype)

    if arg.verbose:
        print ('Columns of input file: {}'.format(s.columns), file=stderr)

    if arg.sort is not None:
        s.sort_values(s.columns[arg.sort], ascending=not arg.descending, inplace=True)
        if arg.verbose:
            print ('Sorting by {}'.format(s.columns[arg.sort]), file=stderr)

    if arg.output_format == 'DS9':
        sl.write_ds9_regions(s, o)
    else:
        daotype = sl.DAO.UNKNOWN_FILE
        if arg.output_format == 'COO':
            daotype = sl.DAO.COO_FILE
        elif arg.output_format == 'SHORT':
            daotype = sl.DAO.SHORT_FILE
        sl.write_dao_file(s, o, dao_type=daotype)

    return sl


def __arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=commons.version_string(),
        description='Star List convert\n Converts star list from stdin to desired format on stdout.')
    parser.add_argument('-i', '--input_format',
                        help='input format (default: daophot autodetect), one of:'
                             '\n\tDS9 ds9 region file'
                             '\n\tCOO daophot coo (7 col)'
                             '\n\tSHORT daophot ALS 5 columns')
    parser.add_argument('-o', '--output_format',
                        help='output format (default: same as input), one of:'
                             '\n\tDS9 ds9 region file'
                             '\n\tCOO daophot coo (7 col)'
                             '\n\tSHORT daophot ALS 5 columns')
    parser.add_argument('-s', '--sort', nargs='?', type=int, default=None, const=0, metavar='COL',
                        help='sort output by specified column (default 0)')
    parser.add_argument('-d', '--descending', action='store_true',
                        help='when -s, sort descending (default ascending)')
    parser.add_argument('-V', '--verbose', action='store_true',
                        help='print some info to stderr, eg. detected columns')
    return parser


# Below: standard skeleton for astwro.tools
# CUSTOMIZE:
#   1. customize postional - obligatory arguments
#   2. decide whether to print results (__do return)

def main(**kwargs):
    """Entry point for python script calls. Parameters identical to command line"""
    # Extract default arguments from command line parser and apply kwargs parameters
    args = commons.bunch_kwargs(__arg_parser(), positional=[], **kwargs)
    # call main routine - common form command line and python calls
    return __do(args)


def info():
    commons.info(__arg_parser())


if __name__ == '__main__':
    # Entry point for command line
    __args = __arg_parser().parse_args()  # parse command line arguments
    __do(__args)  # call main routine - common form command line and python calls
