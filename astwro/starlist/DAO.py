from .StarList import StarList
import pandas as pd


class DAO:
    UNKNOWN_FILE = 0
    FOUNDSTARS_FILE = COO_FILE = 1
    PHOTOMETRY_FILE = AP_FILE = 2
    PSF_STARS_FILE = LST_FILE = 3
    NEIGHBOURS_FILE = NEI_FILE = 4
    ALLSTARS_FILE = ALS_FILE = PK_FILE = NST_FILE = 5

    columns = [
        ['id'],
        ['id', 'x', 'y', 'mag_rel_treshold', 'sharp', 'round', 'round_marg'],
        [],
        ['id', 'x', 'y', 'mag1', 'err1', 'tmp'],
        [],
        ['id', 'x', 'y', 'mag_rel_psf', 'mag_rel_psf_err', 'sky', 'psf_iter', 'psf_chi', 'psf_sharp'],
    ]

    formats = {
        'id': '{:7.0f}',
    }

DAO.extensions = {
    '.txt': DAO.UNKNOWN_FILE,
    '.coo': DAO.COO_FILE,
    '.ap':  DAO.AP_FILE,
    '.lst': DAO.LST_FILE,
    '.nei': DAO.NEI_FILE,
    '.als': DAO.ALS_FILE,
}


DAO_file_firstline = ' NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD'

def read_dao_file(file, dao_type = None):
    """
    Construct StarList from daophot output file.
    The header lines in file may be missing.
    :param file: open stream or filename, if stream dao_type must be specified
    :param dao_type: file format, one of DAO.XXX_FILE constants:
                    - DAO.COO_FILE
                    - DAO.AP_FILE
                    - DAO.LST_FILE
                    - DAO.NEI_FILE
                    - DAO.ALS_FILE
                If missing extension of file will be used to determine file type
                if file is provided as filename
    :return: StarList instance
    """
    return _parse_file(file, _determine_columns(file, dao_type))


def write_dao_file(starlist, file, dao_type=None):
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
    """
    _write_file(starlist, file, _determine_columns(file, dao_type))


def _determine_columns(file, dao_type):
    if not dao_type:
        if not isinstance(file, str):
            raise TypeError('File must be filename or dao_type must be specified')
        import os
        dao_type = DAO.extensions[os.path.splitext(file)[1]]
    if not DAO.columns[dao_type]:
        raise NotImplemented('Columns for this file type not added into DAO.columns yet')
    return DAO.columns[dao_type]


def _write_file(starlist, file, columns):
    f, to_close = _get_stream(file, 'w')
    if starlist.DAO_hdr is not None:
        write_dao_header(starlist.DAO_hdr, file)
        f.write('\n')
    _write_table(starlist, file, columns)
    _close_files(to_close)

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
    stream.write(dump_dao_hdr(hdr, line_prefix=line_prefix))


def _write_table(starlist, file, columns):
    for i, row in starlist.iterrows():
        for col in columns:
            val = i if col == 'id' else row.get(col)
            if val is None: # not all columns exist in StarList, do not write rest of them
                break
            fmt = DAO.formats.get(col)
            if not fmt:
                fmt = '{:9.3f}'
            file.write(fmt.format(val))
        file.write('\n')


def _parse_file(file, columns):
    f, to_close = _get_stream(file, 'r')
    hdr, _ = read_dao_header(f)
    fl = _parse_table(f, columns)
    _close_files(to_close)
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



def _parse_table(f, cols):
    df = pd.read_table(f, names=cols, sep='\s+', na_values='-9.999', index_col='id')
    df.insert(0, 'id', df.index.to_series())
    return StarList(df)


def _get_stream(file, mode):
    to_close = []
    if isinstance(file, str):
        f = open(file, 'r')
        to_close.append(f)
    else:
        f = file
    return f, to_close


def _close_files(to_close):
    for f in to_close:
        f.close()
