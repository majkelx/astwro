import pandas as pd

# Subclassing pandas:
# http://pandas.pydata.org/pandas-docs/stable/internals.html#subclassing-pandas-data-structures

class StarList(pd.DataFrame):
    #
    # StarList properties extending  pd.DataFrame
    _metadata = ['_DAO_hdr', '_DAO_type']

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

    def renumber(self):
        """Renumbers starlist (in place), updating `id` column and index to range 1..count"""
        self.id = range(1, self.count()+1)
        self.index = self.id
