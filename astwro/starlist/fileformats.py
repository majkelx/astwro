# coding=utf-8
from collections import namedtuple
from itertools import chain

class DAO(object):
    FType = namedtuple('DAOFileType', ['columns', 'extension', 'NL', 'read_cols'])
    class CType:
        """Column specification"""
        def __init__(self, name, format, NaN, default=None, optional=False):
            self.name = name
            self.format = format
            self.NaN = NaN
            self.default = default
            self.optional = optional

    UNKNOWN_FILE = FType(
        columns   = ['id'] + list(range(1, 100)),  # id then unknown columns
        extension = '.stars',
        NL = 1,
        read_cols=None,
    )
    COO_FILE = FType(
        columns   = ['id', 'x', 'y', 'rmag', 'fsharp', 'round', 'mround'],
        extension = '.coo',
        NL = 1,
        read_cols=None,
    )
    AP_FILE_ODD = FType(   # odd rows columns (used in read)
        columns   = ['id', 'x', 'y', 'mag'] + ['A{:X}'.format(n) for n in range(2,13)],  # id,x,y,mag,A2,A3,..,AC
        extension = '',
        NL = 2,
        read_cols=None,
    )
    AP_FILE_EVEN = FType(  # even rows columns (used in read)
        columns   = ['sky', 'sky_err', 'sky_skew', 'mag_err'] + ['A{:X}_err'.format(n) for n in range(2,13)],
        extension='',
        NL=2,
        read_cols=None,
    )
    AP_FILE = FType(  # (used in write)
        # id,x,y,mag,A2,..,AC,asky,asky_err,asky_skew,mar_err, A2_err,A3_err,...,AC_err
        columns   = AP_FILE_ODD.columns + AP_FILE_EVEN.columns,
        extension = '.ap',
        NL = 2,
        read_cols=None,
    )
    LST_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag', 'mag_err', 'd'],
        extension = '.lst',
        NL = 3,
        read_cols=None,
    )
    NEI_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag', 'sky'],
        extension = '.nei',
        NL = 3,
        read_cols=5,
    )
    ALS_FILE = FType(
        columns   = ['id', 'x', 'y', 'mag', 'mag_err', 'sky', 'iter', 'chi', 'sharp'],
        extension = '.als',
        NL = 1,
        read_cols=None,
    )
    ERR_FILE = FType(
        columns   = ['id', 'err'],
        extension = '.err',
        NL=None,
        read_cols = 2,
    )
    SHORT_FILE = FType(   # Filetype for all_stars files in Bialkow workflow
        columns=['id', 'x', 'y', 'mag', 'mag_err'],
        extension='.all_stars',
        NL=1,
        read_cols=None,
    )
    XY_FILE = FType(   # Filetype for position x,y only files
        columns=['id', 'x', 'y'],
        extension='.xy',
        NL=1,
        read_cols=3,
    )
    SKY_FILE = FType(   # Filetype for WCS coordinates file as used by ccd_phot workflow
        columns=['id', 'x', 'y', 'mag', 'mag_err', 'ra', 'dec'],
        extension='.sky',
        NL=1,
        read_cols=None,
    )
    RADEC_FILE = FType(   # Filetype for WCS coordinates
        columns=['id', 'ra', 'dec'],
        extension='.radec',
        NL=1,
        read_cols=None,
    )


    file_types = {
        COO_FILE.extension: COO_FILE,
        AP_FILE.extension: AP_FILE,
        LST_FILE.extension: LST_FILE,
        NEI_FILE.extension: NEI_FILE,
        ALS_FILE.extension: ALS_FILE,
        ERR_FILE.extension: ERR_FILE,
        SHORT_FILE.extension: SHORT_FILE,
        XY_FILE.extension: XY_FILE,
        RADEC_FILE.extension: RADEC_FILE,
    }


    # columns dictionary, the key is either:
    # - tuple (filetype:FType, column:str)
    # - column:str
    # when searching for column details, first lookup is for pair (filetype:FType.extension, column:str), if not found
    # lookup for column:str (column definition shared by file types), eventually for '_default'

    _static_columns = {
        '_default':     CType('_default', '{:9.3f}', [-9.999]),
        'id':           CType('id', '{:7.0f}', [0]),
        ('.als','mag'): CType('mag', '{:9.4f}', [99.999]),
        ('.als','mag_err'):   CType('mag_err', '{:9.4f}', [9.9999], default=0.0),
        ('.sky','mag'): CType('mag', '{:9.4f}', [99.999]),
        ('.sky','mag_err'):   CType('mag_err', '{:9.4f}', [9.9999], default=0.0),
        'iter':         CType('iter', '{:8.0f}.', [-9.999], default=0.0),
        'chi':          CType('chi', '{:9.3f}', [-9.999], default=0.0),
        'sharp':        CType('sharp', '{:9.3f}', [-9.999], default=0.0),
        'sky':          CType('sky', '{:10.3f}', [-9.999]),
        'sky_err':      CType('sky_err', '{:6.2f}', [-9.99, -9999.0], default=0),
        'sky_skew':     CType('sky_skew', '{:6.2f}', [-9.99], default=0),
        'ra':           CType('ra', ' {:s}', [], default='00:00:00.0000'),
        'dec':          CType('dec', ' {:s}', [], default='+00:00:00.000'),
        ('.ap','mag'):  CType('mag', '{:9.3f}', [99.999,-99.999,94.999, 98.999]),
        ('.ap','mag_err'):   CType('mag_err', '{:8.4f}', [9.9999], default=0.0),
        ('.ap', 'id'):  CType('id', '\n{:7.0f}', [0]),         # new linie in AP files
        ('.ap', 'sky'): CType('sky', '\n{:14.3f}', [-9.999,0]),  # new linie in AP files
    }

# add A2, A3,... and A2_err, A3_err,...
DAO._apert_columns = dict([(col, DAO.CType(col, '{:9.3f}', [99.999,-99.999,94.999], optional=True))
                       for col in ('A{:X}'.format(i) for i in range(2,13))])
DAO._ap_err_columns = dict([(col, DAO.CType(col, '{:8.4f}', [9.9999], optional=True))
                        for col in ('A{:X}_err'.format(i) for i in range(2,13))])
# dict union
DAO.columns = dict(chain.from_iterable(d.items() for d in (DAO._static_columns, DAO._apert_columns, DAO._ap_err_columns)))

