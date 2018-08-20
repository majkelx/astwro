# coding=utf-8
from __future__ import absolute_import, division, print_function, generators

__metaclass__ = type

import numpy as np
import re
import matplotlib.pyplot as plt
from astwro.phot import DiffPhot


class Plottable(object):
    plot_styles =    ['alpha', 'ls', 'linestyle', 'c', 'color', 'lw', 'linewidth',
                      'marker', 'mec', 'mew', 'mfc', 'ms', 'zorder', 'label']
    scatter_styles = ['alpha', 'c', 's', 'marker', 'edgecolors', 'label']
    (tool_plot, tool_errorbar, tool_scatter) = (1,2,3)
    def __init__(self, **kwargs):
        super(Plottable, self).__init__()
        _kwargs = kwargs
        # plot_styles =    {s: None for s in 'alpha', 'ls', 'c', 'lw', 'marker', 'mec', 'mew', 'mfc', 'ms', 'zorder'}
        # scatter_styles = {s: None for s in 'alpha', 'c', 's', 'marker', 'edgecolors'}

    def plot(self, ax=None, **kwargs):
        if ax is None:
            ax = self._setup_axes(**kwargs)
        self._plotonaxies(ax, **kwargs)
        return ax

    @staticmethod
    def _setup_axes(**kwargs):
        fig = plt.figure()
        return fig.add_subplot(111)

    def _plotonaxies(self, ax, **kwargs):
        pass

    @staticmethod
    def _style_kwargs(style, kwargs_list):
        res = None
        for kwargs in kwargs_list:
            try: res = kwargs[style]
            except KeyError: pass
        return res

    @staticmethod
    def _styles_kwargs(styles_list, kwargs_list):
        res = {}
        for s in styles_list:
            kw = Plottable._style_kwargs(s, kwargs_list)
            if kw is not None:
                res[s] = kw
        return res

    @staticmethod
    def _plot_styles_kwargs(kwargs_list):
        return Plottable._styles_kwargs(Plottable.plot_styles, kwargs_list)

    @staticmethod
    def _scatter_styles_kwargs(kwargs_list):
        return Plottable._styles_kwargs(Plottable.scatter_styles, kwargs_list)


class FigurePlotter(Plottable):
    def __init__(self, **kwargs):
        super(FigurePlotter, self).__init__(**kwargs)

    def _plotonaxies(self, ax, **kwargs):
        super(FigurePlotter, self)._plotonaxies(ax, **kwargs)
        r = kwargs.get('xlim')
        if r is not None:
            ax.set_xlim(r[0], r[1])
        r = kwargs.get('ylim')
        if r is not None:
            ax.set_ylim(r[0], r[1])


class Layer(Plottable):
    def __init__(self, **kwargs):
        super(Layer, self).__init__(**kwargs)
        self.default_styles = {}

    def plot_styles_kwargs(self, **kwargs):
        return self._plot_styles_kwargs([self.default_styles, kwargs])

    def scatter_styles_kwargs(self, **kwargs):
        return self._scatter_styles_kwargs([self.default_styles, kwargs])

    def _plotonaxies(self, ax, **kwargs):
        pass

class ShiftedLayer(Layer):
    def __init__(self, dx, dy, **kwargs):
        super(ShiftedLayer, self).__init__(**kwargs)
        self.dx = dx
        self.dy = dy


class IsochromeLayer(ShiftedLayer):
    def __init__(self, bands, age, Av, distance, feh=0.001, maxm=18.25, **kwargs):
        super(IsochromeLayer, self).__init__(**kwargs)
        from isochrones.mist import MIST_Isochrone
        MIST = MIST_Isochrone(bands)
        iso  = MIST.isochrone(age=np.log10(age), feh=feh, AV=Av, distance=distance, maxm=maxm)

    def _plotonaxies(self, ax, **kwargs):
        super(IsochromeLayer, self)._plotonaxies(ax, **kwargs)




class CollectionLayer(Layer):
    operators = {
        '-': lambda x, y: x - y,
        '+': lambda x, y: x + y,
    }
    oper_reg = re.compile('\s*(\w+)\s*([+-])\s*(\w+)\s*')

    def __init__(self, collections, masks=None, tool=Plottable.tool_plot, colors=None, sizes=None, subsets=None, **kwargs):
        super(CollectionLayer, self).__init__(**kwargs)
        self.collections = collections
        self.masks = masks
        self.default_styles['ls'] = 'None'
        self.default_styles['marker'] = '.'
        self.default_styles.update(self._plot_styles_kwargs([kwargs]))
        self.tool = tool
        self.colors = colors
        self.sizes = sizes
        self.subsets = subsets

    def __len__(self):
        return len(list(self.collections.values())[0])

    def get_values(self, color):
        try:
            m = self.oper_reg.match(color)
            if not m:
                return self.collections[color]
            else:
                a = m.groups()[0]
                op = m.groups()[1]
                b = m.groups()[2]
                return self.operators[op](self.collections[a], self.collections[b])
        except (TypeError, IndexError, KeyError):
            raise ValueError('"color" should be a band name or two color +/- operation, eg. "V", "B-V"')

    def get_masks(self, **kwargs):
        masks = kwargs.get('masks')
        n = len(self)
        if masks is None:
            masks = [np.ones(n, dtype=bool)]
        for i, mask in enumerate(masks):
            if (len(mask) != n):
                boolmask = np.zeros(n, dtype=bool)
                boolmask[mask] = True
                masks[i] = boolmask
        return masks

    def _plotonaxies(self, ax, **kwargs):
        super(CollectionLayer, self)._plotonaxies(ax, **kwargs)
        x = self.get_values(kwargs['xcolor'])
        y = self.get_values(kwargs['ycolor'])
        masks = self.get_masks(**kwargs)
        if self.tool == self.tool_plot:
            styles = self.plot_styles_kwargs(**kwargs)
            for mask in masks:
                ax.plot(x[mask], y[mask], **styles)
        elif self.tool == self.tool_scatter:
            styles = self.scatter_styles_kwargs(**kwargs)
            if self.colors:
                if self.colors == True: # just bool, cycle std cycler over subsets
                    assert len(self.subsets) == len(x), 'If `colors == True` for scatter, `subsets` of size of data should be specified'
                    palette = self.get_scatter_cycle_palette()
                    N = len(palette)
                    c = [palette[i%N] for i in self.subsets]
                else:
                    c = self.colors
                styles['c'] = c
            if self.sizes:
                styles['s'] = self.sizes
            for mask in masks:
                ax.scatter(x[mask], y[mask], **styles)

    def get_scatter_cycle_palette(self): return ['C'+l for l in ['0123456789']]


class CompoundPlot(FigurePlotter):
    def __init__(self, layers, **kwargs):
        super(CompoundPlot, self).__init__(**kwargs)
        self.layers = layers

    def _plotonaxies(self, ax, **kwargs):
        for l in self.layers:
            l._plotonaxies(ax, **kwargs)
        super(CompoundPlot, self)._plotonaxies(ax, **kwargs)


class FilterColorPlotter(CompoundPlot):
    def __init__(self, distance=10, age=0, Av=None, reddenings=None,
                 collections=None, limits=None, **kwargs):
        self.lstars = CollectionLayer(collections, **kwargs)
        super(FilterColorPlotter, self).__init__(layers=[self.lstars], **kwargs)
        self.age = age
        self.distance = distance
        self._Av = Av
        self.reddenings = reddenings
        self.limits = {} if limits is None else limits

    @property
    def modulus(self): return 5*np.log10(self.distance, 10) - 5

    @property
    def Av(self):
        if self._Av is not None:
            return self._Av
        return self._get_reddening('B-V') * 3.1  # 1984A&AS...58..447D

    def update_limits(self, colors, limits):
        """
        Set axis limits for plots.

        Dictionary of limits is also available via `FilterColorPlotter.limits` property.
        Note, that limits can be changed after drawing ion returned axis object also.

        Existing limits, not listed in `colors`, remains unchanged.

        Parameters
        ----------
        colors : iterable of str
            color(s) for which limit is set
        limits : list of tuples or tuple
            pairs representing limits
            if limits is a single tuple, same limits are set for all `colors`

        Example
        -------

            plotter = JohnsonCousinsPlotter(U=u, B=b, V=v)
            plotter.update_limits('UBV', (22, 10))
            plotter.update_limits(['U-B', 'B-V'], (-2, 2))
        """
        try:
            iter(colors)
        except TypeError:
            colors = [colors]
        try:
            st = {c: (l[0], l[1]) for c,l in zip (colors, limits)}
        except TypeError:
            st = {c: (limits[0], limits[1]) for c in colors}
        self.limits.update(st)



    def _get_reddening(self, color):
        try:
            return self.reddenings[color]
        except (KeyError, TypeError):
            return 0

    def _plotonaxies(self, ax, **kwargs):
        kwargs.setdefault('xlim', self.limits.get(kwargs['xcolor']))
        kwargs.setdefault('ylim', self.limits.get(kwargs['ycolor']))
        super(FilterColorPlotter, self)._plotonaxies(ax, **kwargs)



class JohnsonCousinsPlotter(FilterColorPlotter):
    default_limits = {
        'U': (20,5), 'V': (20,5), 'B': (20,5), 'R': (20,5), 'I': (20,5),
        'U-B': (0,2.5), 'B-V': (0,2.5), 'V-I': (0,3.5), 'V-R': (0,2.5), 'R-I': (0,2.5),
        'U_e': (0, 0.3), 'B_e': (0, 0.3), 'V_e': (0, 0.3), 'R_e': (0, 0.3), 'I_e': (0, 0.3),
    }
    def __init__(self, U=None, B=None, V=None, R=None, I=None,
                 U_e=None, B_e=None, V_e=None, R_e=None, I_e=None,
                 distance=None, age=None, Av=None, reddenings=None, **kwargs):
        collections = {c: v for c,v in zip('UVBRI', [U, V, B, R, I]) if v is not None}
        for c in  'UVBRI':  # DiffPhots as arguments? extract mag and error
            dp = collections.get(c)
            if isinstance(dp, DiffPhot):
                collections[c] = dp.mag
                if dp.mag_e is not None:
                    collections[c+'_e'] = dp.mag_e
        errors = {c+'_e': v for c, v in zip('UVBRI', [U_e, V_e, B_e, R_e, I_e]) if v is not None}
        collections.update(errors)
        super(JohnsonCousinsPlotter, self).__init__(
            distance, age, Av, reddenings, collections, limits=dict(self.default_limits), **kwargs)


class MultiJohnsonCousinsPlotter(JohnsonCousinsPlotter):
    def __init__(self, U=None, B=None, V=None, R=None, I=None,
                 U_e=None, B_e=None, V_e=None, R_e=None, I_e=None,
                 colors=True, sizes=False,
                 **kwargs):
        U, B, V, R, I, U_e, B_e, V_e, R_e, I_e = (np.concatenate(t) for t in [U,B,V,R,I,U_e,B_e,V_e,R_e,I_e])
        subsets = np.concatenate([ np.full_like(ss, n) for n, ss in enumerate(U)])
        super(MultiJohnsonCousinsPlotter, self).__init__(
            U, B, V, R, I, U_e, B_e, V_e, R_e, I_e, **kwargs)
        self.lstars.subsets = subsets
        self.lstars.colors = colors
        self.lstars.sizes = sizes



class _TestPlotter:
    def color_mag_plot(ax, x, y, xcolor='B-V', ycolor='V', isochrone=None, sptypes=True, legend=None,
                       masks=[None], labels=None, colors=None, edgecolors=None, alphas=None, sizes=None,
                       xlim=None, ylim=None):
        def p(par, i): return None if par is None or par[i] is None else par[i]

        for i, mask in enumerate(masks):
            s = p(sizes, i)
            if s is None:
                s = 2*(20-y[mask])
            ax.scatter(x[mask], y[mask],
               label = p(labels,i), s=s, c=p(colors,i), edgecolors=p(edgecolors,i), alpha=p(alphas,i))
        # if sptypes:
        #     ax2 = sp.plot_twiny_spectral_types(ax, xcolor)
        # if isochrone:
        #     ax.plot(iB - iV, iV, 'r', linewidth=1, label='${:g}\mathrm{{Myr}}$ isochrone'.format(isochrone/1e6))

        #ax.plot(iso_sm.B_mag - iso_sm.V_mag, iso_sm.V_mag, 'rx') # solar mass points
        # for a in np.arange(7,9, 0.3):
        #     iso3 = MIST.isochrone(age=a, feh=0.001, AV=Av, distance=distance, maxm=18.25)
        #     ax.plot(iso3.B_mag - iso3.V_mag, iso3.V_mag, label='{:.3f}My isochrone'.format(10**a/1e6), linewidth=1, alpha=0.94)
        # iso4 = MIST.isochrone(age=7, feh=0.001)#, maxm=18.25)
        # ax.plot(iso4.B_mag - iso4.V_mag + E_B_V, iso4.V_mag+ distance_modulus + Av, label='10My isochrone', linewidth=1, alpha=0.94)
        # for a in np.arange(0,4.5, 0.5):
        #     iso3 = MIST.evtrack(2.0**a, minage=7, maxage=np.log10(20e6))
        #     ax.plot(iso3.B_mag - iso3.V_mag + E_B_V, iso3.V_mag+ distance_modulus + Av, label='{:.3f}Ms track'.format(2.0**a), linewidth=1, alpha=0.94)

        # ax.plot(iso['Bmag'] - iso['Vmag'] + E_B_V, iso['Vmag'] + distance_modulus + Av, 'r', alpha=1, linewidth=1,
        #        label='10My isochrone')
        ax.set_xlabel('$B-V$')
        ax.set_ylabel('$V$')
        ax.set_xlim(0, 2.5)
#        ax2.set_xlim(0, 2.5)
        ax.set_ylim(20,5)
        if isinstance(legend, bool):
            if legend:
                ax.legend()
        else:
            ax.legend(loc=legend)


if __name__ == "__main__":
    from astroquery.vizier import Vizier
    massey = Vizier.query_region('NGC 6871', radius='0d6m0s', catalog='J/ApJ/454/151/ngc6871')[0]
    V = massey['Vmag']
    B = massey['B-V'] + V
    U = massey['U-B'] + B
    plotter = JohnsonCousinsPlotter(U, B, V, distnace=1649, age=10e6, Av=1.364)
    ax = plotter.plot(xcolor='B-V', ycolor='V')
    plt.show()

