from .StarList import StarList
from .file_helpers import *
import pandas as pd
from .fileformats import *


DAO_file_firstline = ' NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD'

def convert_dao_type(starlist, new_daotype, update_daotype=True):
        # type: (StarList, DAO.FType) -> bool
    """Converts from one daotype to another

    Only subset of conversions supported. You can also provide own map (directory) of column names"""
    for col in new_daotype.columns:
        if col not in starlist.columns:
            ct = _get_col_type(new_daotype.extension, col)
            if not ct.optional:
                if ct.default is None:
                    return False
                else:
                    starlist.loc[:, col] = ct.default # new col
    if update_daotype:
        starlist.DAO_type = new_daotype
    return True


def read_dao_file(file, dao_type = None):
    """
    Construct StarList from daophot output file.
    The header lines in file may be missing.
    :rtype: StarList
    :param file: open stream or filename, if stream dao_type must be specified
    :param dao_type: file format, one of DAO.XXX_FILE constants:
                    - DAO.COO_FILE
                    - DAO.AP_FILE
                    - DAO.LST_FILE
                    - DAO.NEI_FILE
                    - DAO.ALS_FILE
                If missing filename extension will be used to determine file type
                if file is provided as filename
    :return: StarList instance
    """
    ret = _parse_file(file, dao_type)
    return ret


def write_dao_file(starlist, file, dao_type=None, with_header=True):
    """
    Write StarList object into daophot  file.
    :param starlist: StarList instance to be writen
    :param file: writable stream or filename, if stream dao_type must be specified
    :param dao_type: file format, one of DAO.XXX_FILE constants:
                    - DAO.COO_FILE
                    - DAO.AP_FILE
                    - DAO.LST_FILE
                    - DAO.NEI_FILE
                    - DAO.ALS_FILE
                If missing extension of file will be used to determine file type
                if file is provided as filename
    :rtype: None
    """
    if dao_type is None:
        if starlist.DAO_type is None:
            raise Exception('Can not determine file format')
        dao_type = starlist.DAO_type
    elif dao_type != starlist.DAO_type:
        converted = convert_dao_type(starlist, dao_type, update_daotype=False)
        if not converted:
            raise Exception('Can not convert columns {} into {} '.format(starlist.columns, dao_type.columns))
    _write_file(starlist, file, dao_type, with_header=with_header)

def _get_col_type(file_ext, column):
    # type: (str, str) -> DAO.CType
    coltype = DAO.columns.get((file_ext, column))  # lookup for (filetype,col)
    if not coltype:
        coltype = DAO.columns.get(column)  # lookup for col
    if not coltype:
        coltype = DAO.columns['_default']
    return coltype


def _write_file(starlist, file, dao_type, with_header=True):
    f, to_close = get_stream(file, 'w')
    if with_header:
        if starlist.DAO_hdr is not None:
            starlist.DAO_hdr['NL'] = dao_type.NL
            write_dao_header(starlist.DAO_hdr, f)
            f.write('\n')
        else:
            raise Exception('Attempt to save dao file with header from StarList with DAO_hdr=None')
    _write_table(starlist, f, dao_type)
    close_files(to_close)


def dump_dao_hdr(hdr, line_prefix=''):
    """
    returns two line string representation of header dictionary
    :param dict hdr: dao header dictionary like StarList.DAO_hdr
    :param str line_prefix: add this prefix at beginning of every line (e.g. comment char)
    :rtype:str
    """
    first_line = ''
    second_line = ''
    second_line_frmt = ['{:3.0f}', '{:6.0f}', '{:6.0f}', '{:8.1f}', '{:8.1f}', '{:8.2f}',
                        '{:8.2f}', '{:8.2f}', '{:8.2f}', '{:8.2f}']
    second_line_frmt.reverse()
    try:
        for token in DAO_file_firstline.split(' '):
            if token != '':
                val = hdr[token]
                first_line += token
                fmt = second_line_frmt.pop()
                second_line += fmt.format(float(val))
            first_line += ' '
    except KeyError:
        # sometimes header is shorter, it's OK'
        pass
    return line_prefix + first_line + '\n' + line_prefix + second_line + '\n'


def write_dao_header(hdr, stream, line_prefix=''):
    """
    writes two lines of dao header
    :param dict hdr: dao header dictionary like StarList.DAO_hdr
    :param file stream: to write
    :param str line_prefix: add this prefix at beginning of every line (e.g. comment char)
    """
    f, to_close = get_stream(stream, 'w')
    stream.write(dump_dao_hdr(hdr, line_prefix=line_prefix))
    close_files(to_close)


def _write_table(starlist, file, dao_type):
    # preapre columns (from daotype in order but only existing in starlist)
    pd.options.mode.chained_assignment = None  # default='warn'
    columns = [c for c in dao_type.columns if c in starlist.columns]
    coltypes = [_get_col_type(dao_type.extension, c) for c in columns]
    towrite = starlist[columns]

    for i, row in towrite.iterrows():
        for col, coltype, val in zip(columns, coltypes, row):
            if pd.isnull(val):
                val = coltype.NaN[0]
            file.write(coltype.format.format(val))
        file.write('\n')

def _parse_file(file, dao_type):
    if dao_type is None and isinstance(file, str):
        _, ext = os.path.splitext(file)
        dao_type = DAO.file_types.get(ext)

    f, to_close = get_stream(file, 'r')
    try:
        hdr, _ = read_dao_header(f)
        fl = _parse_table(f, hdr, dao_type)
    finally:
        close_files(to_close)
    fl.DAO_hdr = hdr
    return  fl


def read_dao_header(stream, line_prefix=''):
    """
    tries to read dao header, if fails returns already read characters
    :param file stream: open input file
    :param line_prefix: additional prefix expected on the beginning of line
    :return: tuple (header dict, stolen chars)
             if header is detected, reads 2 lines of stream and returns (dict, None)
             else reads couple of chars and return (None, couple-of-chars)
    """
    # we are very smart, if first two characters of ile are not ' N', we suppose there is no header
    # and we get not too much to disturb further parsing of tables
    signature = ' NL'
    stolen_chars = ''
    for c in line_prefix + signature:
        r = stream.read(1)
        stolen_chars += r
        if c != r: # no header signature  found
            return None, stolen_chars

    hdr = stolen_chars + stream.readline() # first line
    val = stream.readline()
    return parse_dao_hdr(hdr, val, line_prefix), None


def parse_dao_hdr(hdr, val, line_prefix=''):
    """
    creates dao header dict form two lines of file header
    :param str hdr: first line
    :param str val: second line
    :param line_prefix: expected line prefix
    :return: dict with dao header compatible with StarList.DAO_header
    """
    # cut prefix
    hdr = hdr[len(line_prefix):] # first line
    val = val[len(line_prefix):] # second line
    # split keys, split values, zip them into list of tuples, then create dictionary out of that
    return dict(zip(hdr.split(), val.split()))


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


def _guess_filetype(header, table):
    type = DAO.UNKNOWN_FILE
    if header:
        colno = table.columns.size
        NL = int(header['NL'])
        type = DAO.UNKNOWN_FILE
        if NL == 1:
            if colno == 7:
                type = DAO.COO_FILE
            elif colno == 9:
                type = DAO.ALS_FILE
            elif colno == 5:
                type = DAO.SHORT_FILE
        elif NL == 2:
            type = DAO.AP_FILE
        elif NL == 3:
            if colno == 6:
                type = DAO.LST_FILE
            elif colno == 5:
                type = DAO.NEI_FILE
    return type
