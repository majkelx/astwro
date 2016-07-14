from .StarList import StarList
import pandas as pd


class DAO:
    UNKNOWN_FILE = 0
    FOUNDSTARS_FILE = COO_FILE = 1
    PHOTOMETRY_FILE = AP_FILE = 2
    PSF_STARS_FILE = LST_FILE = 3
    NEIGHBOURS_FILE = NEI_FILE = 4
    ALLSTARS_FILE = ALS_FILE = 5

    columns = [
        ['id'],
        ['id', 'x', 'y', 'rel_mag', 'sharp', 'round', 'round_marg'],
        [],
        ['id', 'x', 'y', 'mag1', 'err1', 'tmp'],
        [],
        [],
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

def starlist_from_file(file, dao_type = None):
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


def write_file(starlist, file, dao_type=None):
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
    _write_header(starlist.DAO_hdr, file)
    _write_table(starlist, file, columns)
    _close_files(to_close)

def _write_header(hdr, file):
    if hdr is None:
        return
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
    file.write(first_line + '\n' + second_line + '\n\n')


def _write_table(starlist, file, columns):
    for i, row in starlist.iterrows():
        for col in columns:
            fmt = DAO.formats.get(col)
            if not fmt:
                fmt = '{:9.3f}'
            file.write(fmt.format(row[col]))
        file.write('\n')


def _parse_file(file, columns):
    f, to_close = _get_stream(file, 'r')
    hdr = _parse_header(f)
    fl = _parse_table(f, columns)
    _close_files(to_close)
    fl.DAO_hdr = hdr
    return  fl


def _parse_header(file):
    # we are very smart, if first two characters of ile are not ' N', we suppose there is no header
    # and we get not too much to disturb further parsing of tables
    if file.read(2) != DAO_file_firstline[:2]:
        return None
    hdr = DAO_file_firstline[:2] + file.readline() # first line
    val = file.readline()
    # split keys, split values, zip them into list of tuples, then create dictionary out of that
    return dict(zip(hdr.split(), val.split()))


def _parse_table(f, hdr):
    df = pd.read_table(f, names=hdr, sep='\s+', na_values='-9.999', index_col=False)
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
