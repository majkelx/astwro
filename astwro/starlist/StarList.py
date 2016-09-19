import pandas as pd

# Subclassing pandas:
# http://pandas.pydata.org/pandas-docs/stable/internals.html#subclassing-pandas-data-structures

class StarList(pd.DataFrame):
    #
    # StarList properties extending  pd.DataFrame
    _metadata = ['_DAO_hdr']

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
        """returns DAO file header dict if any"""
        return self._DAO_hdr

    @DAO_hdr.setter
    def DAO_hdr(self, hdr):
        self._DAO_hdr = hdr

    def count(self):
        """returns number of stars in list"""
        return self.shape[0]
