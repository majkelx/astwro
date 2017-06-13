# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from .StarList import StarList
from .file_helpers import *


_DAO_file_firstline = ' NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD'


def read_dao_file(f, dao_type = None):
    """
    Construct StarList from `daophot` output file

    The dao header lines in file may be omitted.
    :rtype: StarList
    :param f file or str: open stream or filename
    :param dao_type str: file format, ext string one of DAO.XXX_FILE constants:
                    * DAO.COO_FILE or `'coo'`
                    * DAO.AP_FILE  or `'ap'`
                    * DAO.LST_FILE or `'lst'`
                    * DAO.NEI_FILE or `'nei'`
                    * DAO.ALS_FILE or `'als'`
                    * DAO.GRP_FILE or `'grp'`

                Filename extension isn't used do determine file format.
                If ``dao_type is None``, file format will be guessed from content.
    :return: StarList instance
    """
    if dao_type is None and isinstance(file, str):
        f, to_close = get_stream(file, 'r')
    try:
        hdr, _ = read_dao_header(f)
        if dao_type is None and hdr is not None and hdr.get('NL') == 2:  # must be AP
            dao_type = DAO.AP_FILE
        fl = _parse_table(f, hdr, dao_type)
    finally:
        close_files(to_close)

    fl.DAO_hdr = hdr
    return  fl


def read_dao_header(stream, line_prefix=''):
    """
    tries to read dao header (first two lines),

    If fails (no header) returns also characters readen from stream until fail

    :rtype:(dict, str)
    :param file stream file: open input file
    :param line_prefix str: additional prefix expected on the beginning of line
    :return: tuple (header dict, stolen chars)
             if header is detected, reads 2 lines of stream and returns (dict, None)
             else reads couple of chars and return (None, couple-of-chars)
    """
    # we are very smart, we read up to 3 characters of file checking if thay match' NL',
    # if no we suppose there is no header
    signature = ' NL'
    stolen_chars = ''
    for c in line_prefix + signature:
        r = stream.read(1)
        stolen_chars += r
        if c != r: # no header signature  found
            return None, stolen_chars

    hdr = stolen_chars + stream.readline() # first line
    val = stream.readline()

    # cut prefix
    hdr = hdr[len(line_prefix):] # first line
    val = val[len(line_prefix):] # second line
    # split keys, split values, zip them into list of tuples, then create dictionary out of that
    return dict(zip(hdr.split(), val.split())), None


def _parse_table(f, hdr, dao_type):
    if dao_type is not None and dao_type.read_cols is not None:  # limit number of read cols
        df = pd.read_table(f, header=None, sep='\s+', usecols=range(dao_type.read_cols))
    else:
        df = pd.read_table(f, header=None, sep='\s+')

    #df.insert(0, 'id', df.index.to_series())
    if dao_type is None:
        dao_type = _guess_filetype(hdr, df)
    if dao_type == DAO.AP_FILE:  # two row per star format correction
        odd = df.iloc[0::2]
        odd.columns = DAO.AP_FILE_ODD.columns[:odd.columns.size]
        even = df.iloc[1::2]
        even.columns = DAO.AP_FILE_EVEN.columns[:even.columns.size]
        even.index = odd.index
        df = odd.join(even, rsuffix='foo')
    else:
        df.columns = dao_type.columns[:df.columns.size]


    df.id = df.id.astype(int)
    df.index = df.id

    # find NaN
    for col in df.columns:
        coltype = _get_col_type(dao_type.extension, col)
        if coltype.NaN:
            df[col].replace(coltype.NaN, pd.np.nan, inplace=True)

    ret = StarList(df)
    ret.DAO_type = dao_type
    return ret