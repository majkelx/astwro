import os
import re
import pandas as pd
import astropy.table
from .StarList import StarList

def get_stream(file, mode):
    to_close = []
    if isinstance(file, str):
        file = os.path.expanduser(file)
        f = open(file, mode)
        to_close.append(f)
    else:
        f = file
    return f, to_close


def close_files(to_close):
    for f in to_close:
        f.close()


def extract_SkyCoord(starlist):
    import astropy.units as u
    from astropy.coordinates import SkyCoord

    # type: (StarList) -> SkyCoord

    ra_col = None; ra_unit=None
    dec_col = None; dec_unit = None
    #preferd col names
    for c in ['ra', 'RA', 'RAJ2000']:
        if c in starlist.columns:
            ra_col  = starlist[c]
    for c in ['dec', 'DE', 'de', 'DEC', 'DEJ2000']:
        if c in starlist.columns:
            dec_col  = starlist[c]
    # maybe our deg
    if ra_col is None and dec_col is None and 'ra_deg' in starlist.columns and 'dec_deg' in starlist.columns:
        ra_col  = starlist['ra_deg'];  ra_unit = u.deg
        dec_col = starlist['dec_deg']; dec_unit= u.deg
    else:
        # TODO: regexp
        pass;

    if ra_col is None or dec_col is None:
        return None

    if ra_unit is None:
        try:
            return SkyCoord(ra_col, dec_col)
        except u.UnitsError:
            ra_unit = u.hourangle
            dec_unit = u.deg
    return SkyCoord(ra_col, dec_col, unit=(ra_unit, dec_unit))


def as_starlist(input, read_files=True, raise_exceptions=True, updateskycoord=True):
    if isinstance(input, StarList):
        return input

    # TODO: input:Path -> string
    # TODO: input:string : read file: DAO, astropy, pandas
    if isinstance(input, astropy.table.Table):
        meta=input.meta
        input = StarList(input.to_pandas())
        input.DAO_type = meta.get('DAO_type')
        dao_hdr = {}
        for key in ['NL', 'NX', 'NY', 'LOWBAD', 'HIGHBAD', 'THRESH', 'AP1', 'PH/ADU', 'RNOISE', 'FRAD']:
            v = meta.get(key)
            if v is not None:
                dao_hdr[key] = v
        if len(dao_hdr) > 0:
            input.DAO_hdr = dao_hdr

    elif isinstance(input, pd.DataFrame):
        input = StarList(input)
    # TODO: structured numpy arrays
    elif raise_exceptions:
        raise TypeError('Cannot interpret type {} as astropy.starlist.StarList'.format(type(input)))
    else:
        return None

    # bytes->string
    for col in input:
        if isinstance(input[col][0], bytes):
            input[col] = input[col].str.decode('utf-8')

    # check id obligatory field/idx
    input.refresh_id()
    # check, update sky ra/dec coords
    if updateskycoord:
        coo = extract_SkyCoord(input)
        if coo:
            input.radec_hmsdms_from_skycoord(coo)
            input.radec_deg_from_hmsdms()
    return input

