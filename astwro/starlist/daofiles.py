from .StarList import StarList
from .file_helpers import *
import pandas as pd
from collections import namedtuple
from itertools import chain


class DAO(object):
    FType = namedtuple('DAOFileType', ['columns', 'extension', 'NL'])
    CType = namedtuple('DAOColumnType', ['name', 'format', 'NaN'])
    UNKNOWN_FILE = FType(
        columns   = ['id'] + range(1, 100),  # id then unknown columns
        extension = '.stars',
        NL = None,
    )
    COO_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag_rel_to_threshold', 'sharp', 'round', 'round_marg'],
        extension = '.coo',
        NL = 1,
    )
    AP_FILE_ODD = FType(   # odd rows columns (used in read)
        columns   = ['id', 'x', 'y'] + ['A{:X}'.format(n) for n in range(1,13)],  # id,x,y,A1,A2,..,AC
        extension = '',
        NL = 2,
    )
    AP_FILE_EVEN = FType(  # even rows columns (used in read)
        columns   = ['sky', 'sky_err', 'sky_skew'] + ['A{:X}_err'.format(n) for n in range(1,13)],
        extension='',
        NL=2,
    )
    AP_FILE = FType(  # (used in write)
        # id,x,y,A1,A2,..,AC,asky,asky_err,asky_skew,A1_err,...,AC_err
        columns   = AP_FILE_ODD.columns + AP_FILE_EVEN.columns,
        extension = '.ap',
        NL = 2,
    )
    LST_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag1', 'err1', 5],
        extension = '.lst',
        NL = 3,
    )
    NEI_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag1', 4],
        extension = '.nei',
        NL = 3,
    )
    ALS_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag_rel_psf', 'mag_rel_psf_err', 'sky', 'psf_iter', 'psf_chi', 'psf_sharp'],
        extension = '.als',
        NL = 1,
    )
    SHORT_FILE = FType(   # Filetype for all_stars files in Bialkow workflow
        columns=['id', 'x', 'y', 'mag_rel_psf', 'mag_rel_psf_err'],
        extension='.all_stars',
        NL=1,
    )

    # columns dictionary, the key is either:
    # - tuple (filetype:FType, column:str)
    # - column:str
    # when searching for column details, first lookup is for pair (filetype:FType.extension, column:str), if not found
    # lookup for column:str (column definition shared by file types), eventually for '_default'
    _static_columns = {
        '_default':     CType('_default', '{:9.3f}', [-9.999]),
        'id':           CType('id', '{:7.0f}', [0]),
        'mag_rel_psf':  CType('mag_rel_psf', '{:9.4f}', [-9.999]),
        'mag_rel_psf_err':  CType('mag_rel_psf_err', '{:9.4f}', [-9.999]),
        'psf_iter':     CType('psf_iter', '{:9.1f}', [-9.999]),
        'sky_err':      CType('sky_err', '{:6.2f}', [-9.99]),
        'sky_skew':     CType('sky_skew', '{:6.2f}', [-9.99]),
        ('.ap', 'id'): CType('id', '\n{:7.0f}', [0]),         # new linie in AP files
        ('.ap', 'sky'): CType('sky', '\n{:14.3f}', [-9.999]),  # new linie in AP files
    }
    # add A0, A1,... and A0_err, A1_err,...
    _apert_columns = dict([(col, CType(col, '{:9.3f}', [99.999,-99.999])) for col in ('A{:X}'.format(i) for i in range(1,13))])
    _ap_err_columns = dict([(col, CType(col, '{:8.4f}', [9.9999])) for col in ('A{:X}_err'.format(i) for i in range(1,13))])
    # dict union
    columns = dict(chain.from_iterable(d.items() for d in (_static_columns, _apert_columns, _ap_err_columns)))

DAO_file_firstline = ' NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD'


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
    return _parse_file(file, dao_type)


def write_dao_file(starlist, file, dao_type=None):
    """
    Write StarList object into daophot  file.
    :rtype: None
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
    """
    if dao_type is None and isinstance(file, str): # guess file type from extension
        _, ext = os.path.splitext(file)
        types = [v for k, v in DAO.__dict__.items() if isinstance(v, DAO.FType) and v.extension == ext]
        if types:
            dao_type = types[0]
    if dao_type is None:
        dao_type = DAO.UNKNOWN_FILE

    _write_file(starlist, file, dao_type)

def _get_col_type(file_ext, column):
    # type: (str, str) -> DAO.CType
    coltype = DAO.columns.get((file_ext, column))  # lookup for (filetype,col)
    if not coltype:
        coltype = DAO.columns.get(column)  # lookup for col
    if not coltype:
        coltype = DAO.columns['_default']
    return coltype


def _write_file(starlist, file, dao_type):
    f, to_close = get_stream(file, 'w')
    if starlist.DAO_hdr is not None:
        write_dao_header(starlist.DAO_hdr, f)
        f.write('\n')
    _write_table(starlist, f, dao_type)
    close_files(to_close)


def dump_dao_hdr(hdr, line_prefix=''):
    """
    returns two line string representation of header dictionary
    :param dict hdr: dao header dictionary like StarList.DAO_hdr
    :param str line_prefix: add this prefix at beginning of every line (e.g. comment char)
    :rtype str
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
    for i, row in starlist.iterrows():
        for col in dao_type.columns:
            val = i if col == 'id' else row.get(col)
            if val is None: # not all columns exist in StarList, do not write rest of them
                continue
            coltype = _get_col_type(dao_type.extension, col)
            if pd.isnull(val):
                val = coltype.NaN[0]
            file.write(coltype.format.format(val))
        file.write('\n')


def _parse_file(file, dao_type):
    f, to_close = get_stream(file, 'r')
    hdr, _ = read_dao_header(f)
    fl = _parse_table(f, hdr, dao_type)
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
    df = pd.read_table(f, header=None, sep='\s+')  #, index_col=0)
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
    return StarList(df)


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
