# coding=utf-8
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from .StarList import StarList

DAO_file_firstline = ' NL    NX    NY  LOWBAD HIGHBAD  THRESH     AP1  PH/ADU  RNOISE    FRAD'


def read_dao_file(f, dao_type = None):
    """
    Construct StarList from `daophot` output file

    The dao header lines in file may be omitted.
    :rtype: StarList
    :param f file or str: open stream or filename
    :param dao_type: file format, ext string one of DAO.XXX_FILE constants:
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
    ret = _parse_file(file, dao_type)
    return ret