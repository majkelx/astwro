import pandas as pd
from astropy.table import Table

# Subclassing pandas:
# http://pandas.pydata.org/pandas-docs/stable/internals.html#subclassing-pandas-data-structures

class StarList(pd.DataFrame):
    #
    # StarList properties extending  pd.DataFrame
    _metadata = ['_DAO_hdr', '_DAO_type']
    _DAO_hdr = None
    _DAO_type = None

    @staticmethod
    def new():
        """Returns empty StarList instance with columns id,x,y"""
        idx = pd.Series(name='id', dtype='int64')
        id = pd.Series(dtype='int64')
        x = pd.Series(dtype='float64')
        y = pd.Series(dtype='float64')
        return StarList({'id': id, 'x': x, 'y': y}, index=idx)

    @property
    def _constructor(self):

        return StarList

    @property
    def DAO_hdr(self):
        """DAO file header dict if any"""
        return self._DAO_hdr

    @DAO_hdr.setter
    def DAO_hdr(self, hdr):
        self._DAO_hdr = hdr

    @property
    def DAO_type(self):
        """DAO file header dict if any"""
        return self._DAO_type

    @DAO_type.setter
    def DAO_type(self, typ):
        self._DAO_type = typ

    def import_metadata(self, src):
        """Copies metdata (dao type, dao hdr) from src

        :param StarList src: source of metadata
        """
        self.DAO_type = src.DAO_type
        self.DAO_hdr = src.DAO_hdr

    def count(self):
        """returns number of stars in list"""
        return self.shape[0]

    def renumber(self, start=1):
        """Renumbers starlist (in place), updating `id` column and index to range start.. start+count"""
        self['id'] = range(start, self.count()+start)
        self.index = self.id

    def to_table(self):
        """
        Return a :class:`astropy.table.Table` instance
        """
        t = Table.from_pandas(self)
        if self.DAO_hdr is not None:
            t.meta.update(self.DAO_hdr)
        if self.DAO_type is not None:
            t.meta['DAO_type'] = self.DAO_type
        return t

    @classmethod
    def from_table(cls, table):
        """
        Create a `StarList` from a :class:`astropy.table.Table` instance

        Parameters
        ----------
        table : :class:`astropy.table.Table`
            The astropy :class:`astropy.table.Table` instance
        Returns
        -------
        sl : `StarList`
            A `StarList`instance
        """
        sl = StarList(table.to_pandas())
        sl.DAO_type = table.meta.get('DAO_type')
        dao_hdr = {}
        for key in ['NL', 'NX', 'NY', 'LOWBAD', 'HIGHBAD', 'THRESH', 'AP1', 'PH/ADU', 'RNOISE', 'FRAD']:
            v = table.meta.get(key)
            if v is not None:
                dao_hdr[key] = v
        if len(dao_hdr) > 0:
            sl.DAO_hdr = dao_hdr
        return sl
