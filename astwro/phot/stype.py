# coding=utf-8
from __future__ import absolute_import, division, print_function
from collections import OrderedDict

__metaclass__ = type

import sys
if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import munch
import numpy as np
import pandas as pd


class SpectralType(object):
    """From http://www.stsci.edu/~inr/intrins.html"""
    columns = ['stype', 'U-B', 'B-V', 'V-R', 'V-I', 'V-J',	'V-H',	'V-K',	'V-L',	'V-M',	'V-N']

#    table = pd.DataFrame.f
    table =  pd.read_csv(StringIO("""stype U-B B-V V-R V-I V-J V-H V-K V-L V-M V-N
        0.0  -1.08  -0.30  -0.19  -0.31  -0.80  -0.92  -0.97  -1.13  -1.00  -9.99
        0.5  -1.00  -0.28  -0.18  -0.31  -0.77  -0.89  -0.95  -1.11  -0.99  -9.99
        1.0  -0.95  -0.26  -0.16  -0.30  -0.73  -0.85  -0.93  -1.08  -0.96  -9.99
        1.5  -0.88  -0.25  -0.15  -0.29  -0.70  -0.82  -0.91  -1.05  -0.94  -9.99
        2.0  -0.81  -0.24  -0.14  -0.29  -0.67  -0.79  -0.89  -1.02  -0.92  -9.99
        2.5  -0.72  -0.22  -0.13  -0.28  -0.64  -0.76  -0.86  -0.97  -0.88  -0.96
        3.0  -0.68  -0.20  -0.12  -0.27  -0.60  -0.72  -0.82  -0.92  -0.84  -0.91
        3.5  -0.65  -0.19  -0.12  -0.26  -0.58  -0.70  -0.80  -0.90  -0.82  -0.87
        4.0  -0.63  -0.18  -0.11  -0.25  -0.56  -0.68  -0.77  -0.86  -0.79  -0.84
        4.5  -0.61  -0.17  -0.11  -0.24  -0.54  -0.65  -0.74  -0.83  -0.76  -0.80
        5.0  -0.58  -0.16  -0.10  -0.24  -0.51  -0.62  -0.71  -0.78  -0.73  -0.75
        6.0  -0.49  -0.14  -0.10  -0.21  -0.46  -0.57  -0.64  -0.70  -0.65  -0.66
        7.0  -0.43  -0.13  -0.09  -0.19  -0.41  -0.51  -0.57  -0.61  -0.58  -0.58
        7.5  -0.40  -0.12  -0.09  -0.17  -0.39  -0.48  -0.54  -0.57  -0.54  -0.53
        8.0  -0.36  -0.11  -0.08  -0.16  -0.36  -0.45  -0.49  -0.52  -0.49  -0.48
        8.5  -0.27  -0.09  -0.08  -0.13  -0.31  -0.40  -0.43  -0.43  -0.42  -0.39
        9.0  -0.18  -0.07  -0.07  -0.10  -0.26  -0.34  -0.33  -0.34  -0.34  -0.30
        9.5  -0.10  -0.04  -0.05  -0.08  -0.22  -0.29  -0.26  -0.27  -0.26  -0.22
       10.0  -0.02  -0.01  -0.04  -0.04  -0.16  -0.19  -0.17  -0.18  -0.18  -0.14
       11.0   0.01   0.02  -0.02  -0.02  -0.11  -0.12  -0.11  -0.12  -0.13  -0.08
       12.0   0.05   0.05  -0.01   0.00  -0.07  -0.04  -0.05  -0.07  -0.08  -0.02
       13.0   0.08   0.08   0.01   0.02  -0.02   0.03   0.01  -0.01  -0.02   0.03
       14.0   0.09   0.12   0.02   0.05   0.03   0.11   0.08   0.05  -0.04   0.09
       15.0   0.09   0.15   0.04   0.09   0.09   0.19   0.15   0.12   0.10   0.16
       16.0   0.10   0.17   0.05   0.12   0.13   0.30   0.21   0.17   0.15   0.21
       17.0   0.10   0.20   0.06   0.15   0.18   0.32   0.27   0.23   0.20   0.26
       18.0   0.09   0.27   0.09   0.20   0.25   0.42   0.36   0.33   0.29   0.34
       19.0   0.08   0.30   0.10   0.24   0.31   0.49   0.44   0.41   0.36   0.41
       20.0   0.03   0.32   0.12   0.28   0.37   0.57   0.52   0.49   0.43   0.48
       21.0   0.00   0.34   0.14   0.31   0.43   0.64   0.58   0.57   0.49   0.54
       22.0   0.00   0.35   0.15   0.35   0.48   0.71   0.66   0.66   0.56   0.60
       25.0  -0.02   0.45   0.21   0.44   0.67   0.93   0.89   0.90   0.77   0.80
       28.0   0.02   0.53   0.24   0.50   0.79   1.06   1.03   1.06   0.91   0.91
       30.0   0.06   0.60   0.27   0.54   0.87   1.15   1.14   1.18   1.01   1.01
       32.0   0.09   0.63   0.30   0.58   0.97   1.25   1.26   1.31   1.12   1.11
       33.0   0.12   0.65   0.30   0.59   0.98   1.27   1.28   1.33   1.14   1.13
       35.0   0.20   0.68   0.31   0.61   1.02   1.31   1.32   1.38   1.18   1.17
       38.0   0.30   0.74   0.35   0.66   1.14   1.44   1.47   1.55   1.34   1.30
       40.0   0.44   0.81   0.42   0.75   1.34   1.67   1.74   1.85   1.61   1.54
       41.0   0.48   0.86   0.46   0.82   1.46   1.80   1.89   2.02   1.78   1.68
       42.0   0.67   0.92   0.50   0.89   1.60   1.94   2.06   2.21   1.97   1.84
       43.0   0.73   0.95   0.55   0.97   1.73   2.09   2.23   2.40   2.17   2.01
       44.0   1.00   1.00   0.60   1.04   1.84   2.22   2.38   2.57   2.36   2.15
       45.0   1.06   1.15   0.68   1.20   2.04   2.46   2.66   2.87   2.71   2.44
       47.0   1.21   1.33   0.62   1.45   2.30   2.78   3.01   3.25   3.21   2.83
       48.0   1.23   1.37   0.70   1.67   2.49   3.04   3.29   3.54   3.65   3.16
       49.0   1.18   1.47   0.76   1.84   2.61   3.22   3.47   3.72   3.95   3.39
       50.0   1.15   1.47   0.83   2.06   2.74   3.42   3.67   3.92   4.31   3.66
       51.0   1.17   1.50   0.89   2.24   2.84   3.58   3.83   4.08   4.62   3.89
       52.0   1.07   1.52   0.94   2.43   2.93   3.74   3.98   4.22   4.93   4.11
       """), sep='\s+', na_values=-9.99, index_col=0)

    stypes = OrderedDict([('B',0),('A',10),('F',20),('G',30),('K',40),('M',50)])

    @classmethod
    def stype_name(cls, sptype):
        return cls.stypes.keys()[int(np.floor(sptype/10))] + str(sptype % 10)

    @classmethod
    def stype_number(cls, sptypename):
        num = 0 if len(sptypename) == 1 else float(sptypename[1:])
        return cls.stypes[sptypename[0]] + num

    def __init__(self, reddening=None):
        self.reddening = reddening

    def __call__ (self, color, value):
        unredenrd = value - self.get_reddening(color)
        return self.table.index[(self.table[color] - unredenrd).abs().argsort()[0]]

    def get_reddening(self, color):
        return 0 if self.reddening is None else self.reddening[color]

    def get_color_values(self, color, sptypes):
        return np.array([self.get_color_value(color, t) for t in sptypes])

    def get_color_value(self, color, sptype):
        '''sptype should be either string with on letter from BFGKM set or
        one of nubmers: 0,10,20,30,40,50'''
        if isinstance(sptype, str):
            sptype = self.stype_number(sptype)
        return self.table[color].iloc[self.table.index.get_loc(sptype, method='nearest')] \
               + self.get_reddening(color)


    def generate_plot_aids(self, color):
        """
        Use on mag/color diagrams, e.g:
        >>> from astwro.phot import stype
        >>> st = stype.SpectralType(reddening={'B-V': 1.5})
        >>> aid = st.generate_plot_aids('B-V')
        >>> ax2 = ax.twiny()
        >>> ax2.set_xticks(aid.ticks)
        >>> ax2.set_xticklabels(aid.labels)
        >>> ax2.grid(False)
        >>> ax.fill(aid.fill_x, aid.fill_y, facecolor='gray', alpha=0.2)
        """
        ret = munch.Munch()
        ret.fill_x = self.get_color_values(color, 'BBAAFFGGKKMM')
        ret.fill_y = [-100, 100, 100, -100] * 3
        ret.ticks = ([self.get_color_value(color, 'B') - 0.1]
                      + list((self.get_color_values(color, 'BAFGK') + self.get_color_values(color, 'AFGKM')) / 2)
                      + [self.get_color_value(color, 'M') + 0.2])
        ret.labels = ['O'] + list(self.stypes.keys())
        return ret

    def plot_twiny_spectral_types(self, ax, color, facecolor='gray', alpha=0.2):
        """Plots shadows and spectral type labels

        Returns
        -------
        Twin axies used for labels

        Note
        ----
        Set up xlim manually on returned axies!
        """
        aids = self.generate_plot_aids(color)
        ax2 = ax.twiny()
        ax2.set_xticks(aids.ticks)
        ax2.set_xticklabels(aids.labels)
        ax2.grid(False)
        ax.fill(aids.fill_x, aids.fill_y, facecolor=facecolor, alpha=alpha)
        return ax2

