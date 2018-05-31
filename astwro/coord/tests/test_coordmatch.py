# coding=utf-8

import pytest
import glob
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astwro.coord import CoordMatch, central, grouping, match_catalogues


def teat_test():
    pass



def coo_list(txt):
    return SkyCoord(txt, unit=(u.hourangle, u.deg))

@pytest.fixture
def c1():
    return coo_list( ["1:12:51.68 +1:11:32.3",
                      "1:12:44.0  +1:11:22.6",
                      "1:13:00.1  +1:10:24.5",
                      "1:12:51.7  +1:11:32.0",
                     ])

@pytest.fixture
def c2():
    return coo_list( ["1:14:43.2  +1:12:43",
                      "1:12:51.69 +1:11:32.1",
                      "1:13:00.0  +1:10:24.4",
                      "1:13:00.11 +1:10:24.6",
                      "1:14:44.0  +1:11:22.6",
                     ])


def test_one(c1, c2):
    match = CoordMatch(c1, c2)
    assert match is not None

def test_match(c1, c2):
    match = CoordMatch(c1, c2, 0.5)
    assert (match.iAonly == [1]   ).all()
    assert (match.iAB ==    [0,2,3]   ).all()
    assert (match.iBonly == [0,2,4] ).all()
    assert (match.iBA ==    [1,3]   ).all()


def test_mean(c1):
    c = central(c1)
    assert isinstance(c, SkyCoord)
    assert min(c1.ra) < c.ra < max(c1.ra)
    assert min(c1.dec) < c.dec < max(c1.dec)


@pytest.fixture
def index():    return [3, 2, 3, 2, 3, 1, 7, 6, 9, 8, 9, 10, 9]
@pytest.fixture
def dist():     return [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  3]
@pytest.fixture
def uniquity(): return [1, 1, 1, 2, 3, 4, 5, 6, 7, 8 ,1 ,1  ,1]

def test_grouping(index, dist):
    grp, lbl, idx = grouping(index, dist, 2.0)
    assert len(grp) == 5
    for n in range(len(index)):
        assert n in grp[idx[n]]

#@pytest.mark.xfail(reason='Not Implemented')
def test_grouping_uniq(index, dist, uniquity):
    grp, lbl, idx = grouping(index, dist, 2.0, labels=uniquity)
    assert len(grp) > 5
    for n in range(len(index)):
        assert n in grp[idx[n]]

def test_matching():
    catalogs = [
        SkyCoord([(10.0, 10.0), (20.0, 20.0), (30.0, 30.0), (30.1, 30.1), (50.0, 50.0), (50.1, 50.1), ], unit=u.deg),
        SkyCoord([(10.1, 10.1), (20.1, 20.1), (30.5, 30.5), (30.6, 30.6), (50.2, 50.2), (50.3, 50.3), ], unit=u.deg),
        SkyCoord([(10.6, 10.6), (89.1, 89.1),  ], unit=u.deg),
        SkyCoord([(10.7, 10.7), (20.3, 20.3),  ], unit=u.deg),
    ]

    c, w, s = match_catalogues(catalogs, 1*u.deg,
                               # ra_col='ra_deg', dec_col='dec_deg', radec_unit=u.deg,
                               # weight_fn=lambda x: x['mag_err']**-2,
                               )
    pass


# def test_matching():
#     path = '/Users/michal/projects/TNG/ngc7142/3.1find/'
#     files = glob.glob(f'{path}????0???.vot')
#     catalogs = [Table.read(f) for f in files[:5]]
#
#     c, w, s = match_catalogues(catalogs, 0.5*u.arcsec,
#                                ra_col='ra_deg', dec_col='dec_deg', radec_unit=u.deg,
#                                weight_fn=lambda x: x['mag_err']**-2,
#                                )
#     pass

# def test_grouping_sorting(index, dist):
#     index = [0,1,2,0]
#     dist  = [3,2,1,0]
#
#     grp, idx = grouping(index, dist, 2.0)
#     assert len(grp) == 5
#     for n in range(len(index)):
#         assert n in grp[idx[n]]
