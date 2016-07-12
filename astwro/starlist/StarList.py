import pandas as pd

class StarList(pd.DataFrame):

    @property
    def _constructor(self):
        return StarList
    #
    # StarList properties extending  pd.DataFrame
    _metadata = ['DAO_hdr']