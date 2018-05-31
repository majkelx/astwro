# coding=utf-8
from __future__ import absolute_import, division, print_function

from astropy.coordinates import Angle, SkyCoord
import astropy.units as u
import numpy as np
from os import path

import logging
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())


def central(coords, weights=None, unit=None, axies=None):
    """ Calculates cooridnates of the center of provided set of coordinates
    """
    try:
        if coords.ndim > 1:
            return _ndimcentral(coords, weights=weights, unit=unit, axies=axies)
    except AttributeError:
        pass
    return  _1dimcentral(coords, weights=weights, unit=unit)



def _1dimcentral(coords, weights, unit):

    if unit is not None:
        coords = SkyCoord(coords, unit=unit)

    ref_coords = coords[0]

    ra_offsets, dec_offsets = ref_coords.spherical_offsets_to(coords)
    if weights is not None:
        ra_offset  =  sum(ra_offsets  * weights) / sum(weights)
        dec_offset =  sum(dec_offsets * weights) / sum(weights)
    else:
        ra_offset  =  ra_offsets.mean()
        dec_offset =  dec_offsets.mean()

    return SkyCoord(ref_coords.ra + ra_offset, ref_coords.dec + dec_offset)



def _ndimcentral(coords, weights, unit, axies):
    raise NotImplementedError('vectorized central not implemented yet')
    ##_ndimcentral = np.vectorize(_1dimcentral, otypes=[SkyCoord], excluded=['unit'])





def _prepare_labels(labels_iter):
    if not labels_iter: # none or empty
        return None
    if isinstance(labels_iter[0], set): # sets are ok
        return labels_iter
    return [{e} for e in labels_iter] # convert fot list os one-element sets


def grouping(index, dist, radius, labels=None, unique_labels=True):
    """
    Finds groups of neighbour objects.

    `index` and `dist` like returned by selfmatchig
    by `astropy.coordinates.SkyCoord.match_to_catalog_sky` ::

        index, dist = coo.match_to_catalog_sky(coo, 2)

    Each element will belong to group with closest neighbor if distance to it < `radius`.
    (This does no guaranties that members of different groups are distant by more than `radius`
    in the general case.)

    Parameters
    ----------
    index : array_like
        Index of closest neighbours
    dist : array_like
        Distances to neighbours from index
    radius : float or Angle
        Radius of grouping
    labels : array_like, optional
        Array of sets. Optional labels for elements. Sets of labels will be returned.
    unique_labels : bool, optional
        If `true`, two elements can be grouped only when they labels sets are disjoint. E.g. ::

            uniquity = [{1,2}, {3,4,5}, {1,6}]

        element 0 cannot be grouped with element 2 because of label `1`.
    Returns
    -------
    groups : list of sets
        List of groups - sets of group members
    grlabels: list of sets
        List of group labels - sets of group labels
    assignation : list
        Index of group assignation `assignation[4]` is a name of group containing 4th element
        `n in groups[assignation[n]] == True`

    """
    labels = _prepare_labels(labels)
    if labels is None:
        unique_labels = False
    groups = {}  # indexed by group names (id of leaders), values - ids of members
    grlabels = {} # indexed by group names (id of leaders), values - labels of members
    assigned = {}  # indexed by ids, values of group names

    it = np.argsort(dist) if labels else range(len(index))  # w/o labels check sorting has no effect on result
    for n in it:
        i = n
        grp = set(); lbl = set()
        while i not in assigned and i not in grp:
            grp.add(i)
            try:
                lbl.update(labels[i])
            except: pass
            if dist[i] < radius: # progress
                if not unique_labels:
                    i = index[i]
                else:  # check labels before progressing
                    nxt = index[i]
                    try:
                        ilabels = grlabels[assigned[nxt]] # colect group labels
                    except KeyError:
                        ilabels = labels[nxt]   # or personal labels
                    if lbl.isdisjoint(ilabels):
                        i = nxt
        if grp:
            try:
                grp_name = assigned[i]
                groups[grp_name].update(grp)
                grlabels[grp_name].update(lbl)
            except KeyError:
                grp_name = n  # new group
                groups[grp_name] = grp
                grlabels[grp_name] = lbl
            for i in grp:
                assigned[i] = grp_name
    assert (len(assigned) == len(index))
    # dict to list, three dictionaries groups, grlabels and assigned are converted to lists
    grp_names = groups.keys()
    translate = {grname: pos for pos, grname in enumerate(grp_names)}
    return [groups[k] for k in grp_names], [grlabels[k] for k in grp_names],[translate[assigned[i]] for i in range(len(assigned))]



def match_catalogues(catalogues, radius, selfmatch_radius=0.0, max_iter=200,
                     coord_col=None, ra_col=None, dec_col=None, radec_unit=None, weight_fn=None):
    """
    Matches the objects catalogues.


    Parameters
    ----------
    catalogues : list
        List of catalogues. Catalogue can be SkyCoord object, or array_like with coord columns.
    radius : float or Quantity
        Matching radius
    max_iter : int, optional
        Maximum number of iterations
    selfmatch_radius : float or array_like, optional
        If given, self-matching with that radius performed without preserving distinct detection from one catalogue.
        Use in the case of double detections of deformed objects can occur in any of the catalogues.
    ra_col : int or str, optional
        Index of catalog column for RA (only if catalogs are not SkyCoord).
    dec_col : int or str, optional
        Index of catalog column for DEC (only if catalogs are not SkyCoord).
    coord_col : int or str, optional
        Index of catalog column of type SkyCoord (only if catalogs are `astropy.table.Table` with SkyCoord column).
    radec_unit : astropy.unit, optional
        Unit for ra,dec cols conversion: `astropy.coordinates.SkyCoord(cat[ra_col], cat[dec_col], unit=radec_unit)`
    weight_fn : callable, optional
        Function returning weight for given catalogue element. Default: `lambda x: 1.0`

    Returns
    -------
    coords : SkyCoord
        Coordinates of matched objects
    weights: list
        Summed weights for groups
    src : list of sets
        Source catalogs for matched objects - sets of catalog indexes

    """


    # labeling (assigning each catalog a number-label, storing that label for each element of joined catalog)
    labels = []
    for i,c in enumerate(catalogues):
        labels += [i]*len(c)

    logger.info('Starting matching {} catalogues'.format(len(catalogues)))
    # weighting  (calc weight for element of joined catalog)
    if weight_fn is None:
        weights = np.ones_like(labels)
    else:
        weights = []
        for i, c in enumerate(catalogues):
            weights += [weight_fn(r) for r in c]
        logger.info('Weigths applied')

    # prepare coords
    if coord_col:
        assert ra_col is None and dec_col is None, 'Either coord_col or (ra_col,dec_col) can be specified but not both'
        coord_list = [cat[coord_col] for cat in catalogues]
    elif ra_col or dec_col:
        assert ra_col and dec_col, 'Both or none of ra_col and dec_col can be specified'
        skykwargs = {'unit': radec_unit} if radec_unit is not None else {}
        coord_list = [SkyCoord(cat[ra_col], cat[dec_col], **skykwargs) for cat in catalogues]
    else:
        coord_list = catalogues
    # stack up
    coords = SkyCoord(coord_list)
    logger.info('Joined catalog of {} objects created'.format(len(coords)))
    logger.info('Matching catalogs with radius {}'.format(radius))

    c = coords
    l = labels
    w = np.array(weights)
    neighbour_order = 2
    neighbour_order_increased = False
    selfmatch_performed = False
    for iteration in range(max_iter):
        # calc distances
        idx, dis, _ = c.match_to_catalog_sky(c, neighbour_order)
        # group
        grp, lbl, assgn = grouping(idx, dis, radius=radius, labels=l, unique_labels=not selfmatch_performed)
        reduced = len(c) - len(grp)
        assert reduced >= 0
        logger.info('{:4d} iteration, order {}: {:6d} objects left'.format(iteration, neighbour_order, len(grp)))
        if reduced == 0:
            if not neighbour_order_increased:
                neighbour_order += 1
                neighbour_order_increased = True
            elif not selfmatch_performed and selfmatch_radius:
                neighbour_order = 2
                radius = selfmatch_radius
                selfmatch_performed = True
                logger.info('Self-match with radius {}'.format(selfmatch_radius))
            else:
                break
        else:
            neighbour_order_increased = False
        # calc coord and weights for groups
        c = SkyCoord([mean_coord(c[list(g)], w[list(g)]) for g in grp], unit=u.deg)
        w = np.array([sum(w[list(g)]) for g in grp])
        l = lbl

    logger.info('Matchng finished {:6d} of {:6d} objects left'.format(len(c), len(coords)))
    return c,w,l




def mean_coord(sky_coords, weigths=None):
    if isinstance(mean_coord, SkyCoord):
        coo = np.array([sky_coords.ra.ra, sky_coords.ra.deg])
    else:
        coo = np.array([[s.ra.deg, s.dec.deg] for s in sky_coords]).T
    if weigths is not None:
        ws = sum(weigths)
        coo = coo * weigths
    else:
        ws = len(sky_coords)

    ra = coo[0].sum() / ws
    dec = coo[1].sum() / ws
    return ra, dec


# def self_match(coords: SkyCoord, radius: Angle, weights=None):
#     # type: (SkyCoord, Angle, array_like) -> object
#     if weights is None:
#         weights = np.ones_like()
#     c = coords
#     n = 2
#     while n <= 2 or   min(dist) < radius:
#         idx, dist = c.match_to_catalog_sky()


def xy2sky(x, y, transformer, method='try'):
    from astwro.coord import XY2Sky
    return XY2Sky(transformer)(x,y)

def skyradec2xy(ra, dec, unit='deg', transformer=None, method='try'):
    from astwro.coord import Sky2XY
    return Sky2XY(transformer)(ra=ra, dec=dec, unit=unit)

def skycoo2xy(coo, transformer, method='try'):
    from astwro.coord import Sky2XY
    return Sky2XY(transformer)(coo=coo)


# def xy2sky(x, y, transformer, method='try'):
#     from subprocess import Popen, PIPE
#     x = np.atleast_1d(x)
#     y = np.atleast_1d(y)
#     from astwro.utils import TmpDir
#     with TmpDir() as d:
#         xyfile = path.join(d.path, 'xy')
#         np.savetxt(xyfile, (x,y))
#         # xy.tofile(xyfile, sep=' ')
#         # with open(xyfile, 'a') as f:  # new line ath the end
#         #     f.write('\n')
#         try:
#             p = Popen(['xy2sky', '-dn', '6', transformer, '@'+xyfile], stdout=PIPE, stderr=PIPE)
#             output, err = p.communicate()
#         except FileNotFoundError:
#             raise FileNotFoundError('xy2sky from WCSTools must be installed')
#         pass
#     if p.returncode != 0:
#         raise Exception('xy2sky failed:\n'+err)
#     a = np.loadtxt(output.raw)
#     pass
#
#






