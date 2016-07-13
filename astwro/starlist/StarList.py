import pandas as pd

# Subclassing pandas:
# http://pandas.pydata.org/pandas-docs/stable/internals.html#subclassing-pandas-data-structures

class StarList(pd.DataFrame):
    #
    # StarList properties extending  pd.DataFrame
    _metadata = ['_DAO_hdr']

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
